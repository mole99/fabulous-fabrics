# SPDX-FileCopyrightText: © 2025 Leo Moser <leomoser99@gmail.com>
# SPDX-License-Identifier: Apache-2.0

import os
import re
import math
import random
from pathlib import Path
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, Timer, Edge, RisingEdge, FallingEdge
from cocotb.regression import TestFactory
from cocotb_tools.runner import get_runner
from cocotb.types import LogicArray, Logic

proj_path = Path(__file__).resolve().parent
fabric = os.getenv("FABRIC", "fabric_10x10")

FRAME_BITS_PER_ROW = 32
MAX_FRAMES_PER_COL = 20
FRAME_SELECT_WIDTH = 5 # hardcoded, should be based on FABRIC_NUM_COLUMNS

BITSTREAM_START = 0xFAB0FAB1
DESYNC_FLAG = 20

async def zero_bitstream(dut, delay=10):
    """
    Upload an all-zeros bitstream in reverse to prevent
    logic loops before uploading a new user design.
    """

    dut.FrameData.value = 0
    dut.FrameStrobe.value = (1<<len(dut.FrameStrobe))-1
    await Timer(delay, unit="ns")
    
    dut.FrameStrobe.value = 0
    await Timer(delay, unit="ns")

async def upload_bitstream(dut, name, delay=10):
    """
    Read data until start of bitstream is detected
    Write data until desync bit is in header
    """

    print(f'Uploading bitstream: {name}')
    
    framedata_bits = len(dut.FrameData)
    framestrobe_bits = len(dut.FrameStrobe)
    
    num_rows = framedata_bits//FRAME_BITS_PER_ROW
    num_columns = framestrobe_bits//MAX_FRAMES_PER_COL

    with open(proj_path / f'../user_designs/designs/{name}/{name}.bit', 'br') as f:

        # Wait for start of bitstream
        while (data := f.read(4)) != None:
            word = int.from_bytes(data, "big")
            if word == BITSTREAM_START:
                print('Start of bitstream')
                break
    
        # Read bitstream content
        while 1:
        
            # Read header
            data = f.read(4)
            if data == None:
                break
            header = int.from_bytes(data, "big")
            
            #print(f'--- header: 0x{header:08x}')
            
            column_select = (header >> 27) & 0x1F # bits 31:27
            sync_bit = (header >> DESYNC_FLAG) & 0x1 # bit 20
            frame_strobe = header & 0xFFFFF # bits 19:0
            
            #print(f"column_select: {column_select}")
            #print(f"sync_bit: {sync_bit}")
            #print(f"frame_strobe: {frame_strobe}")

            # Desync
            if sync_bit:
                print("Detected desync flag!")
                break
            
            # Read row data
            all_row_data = 0
            for i in range(num_rows):
                row_data = int.from_bytes(f.read(4), "big")
                all_row_data = all_row_data << FRAME_BITS_PER_ROW | row_data

            #print(f'0x{all_row_data:08x}')

            # Set frame data
            dut.FrameData.value = all_row_data
            
            # Assert frame strobe
            dut.FrameStrobe.value = frame_strobe<<(MAX_FRAMES_PER_COL*column_select)
            await Timer(delay, unit="ns")
            
            # Deassert frame strobe
            dut.FrameStrobe.value = 0
            await Timer(delay, unit="ns")
        
        print(f'Bitstream upload completed')
        
        # Stop the bitstream
        dut.FrameData.value = 0
        dut.FrameStrobe.value = 0
        await Timer(delay, unit="ns")

class PCF:
    "A class to load a PCF file and find the signals in the testbench."
    def __init__(self, dut, file):
        self.signals = {}
        print(f"Reading PCF file: {file}")
        with open(file, "r") as pcf_file:
            while line := pcf_file.readline():
                if match := re.match(r"\s*set_io\s+(?P<signal>\w+)(\[(?P<index>\d+)?\])?\s+X(?P<tilex>\d+)Y(?P<tiley>\d+)\/(?P<bel>\w+)", line):
                    signal = match.group("signal")
                    index = match.group("index")
                    tile_x = match.group("tilex")
                    tile_y = match.group("tiley")
                    bel = match.group("bel")

                    if index is None:
                        index = 0
                    else:
                        index = int(index)

                    # Find the signal in dut
                    dut_signal_in = self.find_signal(dut, tile_x, tile_y, bel, use="IN")
                    dut_signal_out = self.find_signal(dut, tile_x, tile_y, bel, use="OUT")
                    dut_signal_en = self.find_signal(dut, tile_x, tile_y, bel, use="EN")
                    
                    assert dut_signal_in is not None, f"Couldn't find IN port for: {line}"
                    assert dut_signal_out is not None, f"Couldn't find OUT port for: {line}"
                    assert dut_signal_en is not None, f"Couldn't find EN port for: {line}"
                    
                    # Add an index to a signal
                    if signal in self.signals:
                        self.signals[signal][index] = {
                            "IN":   dut_signal_in,
                            "OUT":  dut_signal_out,
                            "EN":   dut_signal_en,
                        }

                        # Sort by index
                        self.signals[signal] = dict(sorted(self.signals[signal].items()))
                    # Add a new signal
                    else:
                        self.signals[signal] = {
                             index: {
                                "IN":   dut_signal_in,
                                "OUT":  dut_signal_out,
                                "EN":   dut_signal_en,
                            }
                        }

    def find_signal(self, dut, tile_x, tile_y, bel, use):
        for element in dut:
            if match := re.match(r"Tile_X(?P<tilex>\d+)Y(?P<tiley>\d+)_(?P<bel>\w)_(?P<use>\w+)_top", element._name):
                match_x = match.group("tilex")
                match_y = match.group("tiley")
                match_bel = match.group("bel")
                match_use = match.group("use") # "OUT", "IN", "EN"
                
                if tile_x == match_x and tile_y == match_y and use == match_use and bel == match_bel:
                    #print(f"Found! {match.group(0)}")
                    return element
        return None

    def get(self, signal, index=None):
        #print(f"get {signal} {index}")
    
        # Get the full signal
        if index is None:
            return LogicArray("".join(str(bit["IN"].value) for bit in reversed(self.signals[signal].values())))
        # Get a single bit
        else:
            return Logic(self.signals[signal][index]["IN"].value)
    
    def set(self, signal, value, index=None):
        #print(f"set {signal} {value} {index}")
        
        # Get the full signal
        if index is None:
            for index, bit in enumerate(reversed(value)):
                self.signals[signal][index]["OUT"].value = bit
        else:
            self.signals[signal][index]["OUT"].value = value

    def get_raw(self, signal, use, index=0):
        return self.signals[signal][index][use]

@cocotb.test()
async def test_counter(dut):
    """Load bitstream for counter"""

    pcf = PCF(dut, proj_path / f"../fabrics/{fabric}/constraints.pcf")
    
    # Reset
    pcf.set("clk1", Logic(0), index=0)
    pcf.set("clk2", Logic(0), index=0)
    pcf.set("rst", Logic(1), index=0)
    pcf.set("ena", Logic(1), index=0)
    await Timer(10, unit="ns")

    # Zero all config bits
    await zero_bitstream(dut)
    await Timer(10, unit="ns")

    # Upload the bitstream
    await upload_bitstream(dut, 'counter')
    await Timer(10, unit="ns")

    # Start a clock on clk1
    clock = pcf.get_raw("clk1", "OUT")
    cocotb.start_soon(Clock(clock, 10, 'ns').start())

    await ClockCycles(clock, 10)
    
    pcf.set("rst", Logic(0), index=0)
    pcf.set("ena", Logic(0), index=0)

    await ClockCycles(clock, 10)

    pcf.set("ena", Logic(1), index=0)

    NUM_CYCLES = 123
    await ClockCycles(clock, NUM_CYCLES)

    assert pcf.get("c").to_unsigned() == NUM_CYCLES-1


@cocotb.test()
async def test_all_ones(dut):
    """Load bitstream for all_ones"""

    pcf = PCF(dut, proj_path / f"../fabrics/{fabric}/constraints.pcf")

    # Zero all config bits
    await zero_bitstream(dut)
    await Timer(10, unit="ns")

    # Upload the bitstream
    await upload_bitstream(dut, 'all_ones')
    await Timer(10, unit="ns")
    
    assert pcf.get("a").to_unsigned() == LogicArray.from_signed(-1, len(pcf.get("a")))
    assert pcf.get("b").to_unsigned() == LogicArray.from_signed(-1, len(pcf.get("b")))
    assert pcf.get("c").to_unsigned() == LogicArray.from_signed(-1, len(pcf.get("c")))


@cocotb.test()
async def test_all_zeros(dut):
    """Load bitstream for all_zeros"""

    pcf = PCF(dut, proj_path / f"../fabrics/{fabric}/constraints.pcf")

    # Zero all config bits
    await zero_bitstream(dut)
    await Timer(10, unit="ns")

    # Upload the bitstream
    await upload_bitstream(dut, 'all_zeros')
    await Timer(10, unit="ns")
    
    assert pcf.get("a").to_unsigned() == LogicArray.from_unsigned(0, len(pcf.get("a")))
    assert pcf.get("b").to_unsigned() == LogicArray.from_unsigned(0, len(pcf.get("b")))
    assert pcf.get("c").to_unsigned() == LogicArray.from_unsigned(0, len(pcf.get("c")))

@cocotb.test()
async def test_passthrough(dut):
    """Load bitstream for passthrough"""

    pcf = PCF(dut, proj_path / f"../fabrics/{fabric}/constraints.pcf")

    # Zero all config bits
    await zero_bitstream(dut)
    await Timer(10, unit="ns")

    # Upload the bitstream
    await upload_bitstream(dut, 'passthrough')
    await Timer(10, unit="ns")
    
    for i in range(32):
        # Get a random value
        value = random.randint(0, 2**len(pcf.get("a"))-1)

        pcf.set("a", LogicArray.from_unsigned(value, len(pcf.get("a"))))
        await Timer(10, unit="ns")
        assert(pcf.get("b").to_unsigned() == value)

@cocotb.test()
async def test_addition(dut):
    """Load bitstream for addition"""

    pcf = PCF(dut, proj_path / f"../fabrics/{fabric}/constraints.pcf")

    # Zero all config bits
    await zero_bitstream(dut)
    await Timer(10, unit="ns")

    # Upload the bitstream
    await upload_bitstream(dut, 'addition')
    await Timer(10, unit="ns")
    
    for i in range(32):
        # Get a random value
        value_a = random.randint(0, 2**len(pcf.get("a"))-1)
        value_b = random.randint(0, 2**len(pcf.get("b"))-1)
        
        result = value_a + value_b

        pcf.set("a", LogicArray.from_unsigned(value_a, len(pcf.get("a"))))
        pcf.set("b", LogicArray.from_unsigned(value_b, len(pcf.get("b"))))
        
        await Timer(10, unit="ns")
        assert(pcf.get("c").to_unsigned() == result)

@cocotb.test()
async def test_multiplication(dut):
    """Load bitstream for multiplication"""

    pcf = PCF(dut, proj_path / f"../fabrics/{fabric}/constraints.pcf")

    # Zero all config bits
    await zero_bitstream(dut)
    await Timer(10, unit="ns")

    # Upload the bitstream
    await upload_bitstream(dut, 'multiplication')
    await Timer(10, unit="ns")
    
    for i in range(32):
        # Get a random value
        value_a = random.randint(0, 2**4-1)
        value_b = random.randint(0, 2**4-1)
        
        result = value_a * value_b

        pcf.set("a", LogicArray.from_unsigned(value_a, 4))
        pcf.set("b", LogicArray.from_unsigned(value_b, 4))
        
        await Timer(10, unit="ns")
        assert(pcf.get("c").to_unsigned() == result)

@cocotb.test()
async def test_register_file(dut):
    """Load bitstream for register_file"""

    pcf = PCF(dut, proj_path / f"../fabrics/{fabric}/constraints.pcf")

    # Reset
    pcf.set("clk1", Logic(0), index=0)
    pcf.set("clk2", Logic(0), index=0)
    pcf.set("rst", Logic(1), index=0)
    pcf.set("ena", Logic(1), index=0)
    await Timer(10, unit="ns")

    # Zero all config bits
    await zero_bitstream(dut)
    await Timer(10, unit="ns")

    # Upload the bitstream
    await upload_bitstream(dut, 'register_file')
    await Timer(10, unit="ns")
    
    # Start a clock on clk1
    clock1 = pcf.get_raw("clk1", "OUT")
    cocotb.start_soon(Clock(clock1, 10, 'ns').start())
    
    # Start a clock on clk1
    clock2 = pcf.get_raw("clk2", "OUT")
    cocotb.start_soon(Clock(clock2, 20, 'ns').start())
    
    await ClockCycles(clock1, 10)
    
    # Fill the memory with data
    for i in range(32):
        print(i)
        print(LogicArray.from_unsigned(i & 0xF, len(pcf.get("word_a"))))
        print(LogicArray.from_unsigned(i, len(pcf.get("addr_a"))))
    
        pcf.set("word_a", LogicArray.from_unsigned(i & 0xF, len(pcf.get("word_a"))))
        pcf.set("addr_a", LogicArray.from_unsigned(i, len(pcf.get("addr_a"))))
        await ClockCycles(clock1, 1)

    
    # Read from both read ports
    for i in range(32):
        pcf.set("addr_b", LogicArray.from_unsigned(31 - i, len(pcf.get("addr_b"))))
        pcf.set("addr_c", LogicArray.from_unsigned(i & 0x3, len(pcf.get("addr_c"))))
        await ClockCycles(clock2, 1)
    
        print(f"B[{31 - i}]: {pcf.get('word_b')}")
        print(f"C[{i & 0x3}]: {pcf.get('word_c')}")

if __name__ == "__main__":

    sim = os.getenv("SIM", "icarus")
    pdk_root = os.getenv("PDK_ROOT", Path("~/.ciel").expanduser())
    pdk = os.getenv("PDK", "ihp-sg13g2")
    scl = os.getenv("SCL", "gf180mcu_fd_sc_mcu7t5v0")
    gl = os.getenv("GL", None)
    
    tile_library = os.getenv("TILE_LIBRARY", proj_path / ".." / "ip" / "fabulous-tiles")

    primitives_path = Path(tile_library) / "primitives"
    tiles_path = Path(tile_library) / "tiles"

    primitives_files = list(primitives_path.glob('**/fabulous/*.v'))
    tile_files = list(tiles_path.glob(f'**/macro/{pdk}/fabulous/*.v'))

    #print(f"Primitive sources: {primitives_files}")
    #print(f"Tile sources: {tile_files}")
    
    sources = []
    
    sources.extend(primitives_files)
    sources.extend(tile_files)
    
    # Add models pack
    sources.append(Path(tile_library) / "models_pack.v")

    # Add custom cells
    sources.append(Path(tile_library) / "custom.v")

    # Add fabric netlist
    sources.append(proj_path / f'../fabrics/{fabric}/macro/{pdk}/fabulous/eFPGA.v')
    
    # Add fabric config
    sources.append(proj_path / '../ip/fabric_config/fabric_config.sv')

    # Add fabric config
    sources.append(proj_path / '../ip/fabric_spi/fabric_spi_receiver.sv')

    hdl_toplevel = "eFPGA" # fabric # TODO use proper fabric name

    runner = get_runner(sim)
    runner.build(
        sources=sources,
        hdl_toplevel=hdl_toplevel,
        defines={},
        always=True,
        clean=True,
        timescale=("1ns", "1ps"),
        waves=True,
    )

    runner.test(
        hdl_toplevel=hdl_toplevel,
        test_module="bare_tb,",
        plusargs=['-fst'],
        waves=True
    )
