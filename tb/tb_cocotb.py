# SPDX-FileCopyrightText: © 2025 Leo Moser <leomoser99@gmail.com>
# SPDX-License-Identifier: Apache-2.0

import os
import math
import random
from pathlib import Path
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles
from cocotb.triggers import Timer, Edge, RisingEdge, FallingEdge
from cocotb.regression import TestFactory
from cocotb_tools.runner import get_runner

random.seed()

WAIT_CYCLES = random.randint(0, 5)
print(f'WAIT_CYCLES: {WAIT_CYCLES}')

FRAME_BITS_PER_ROW = 32
MAX_FRAMES_PER_COL = 20
FRAME_SELECT_WIDTH = 5 # hardcoded, should be based on FABRIC_NUM_COLUMNS

FABRIC_NUM_COLUMNS = 10
FABRIC_NUM_ROWS = 10

BITSTREAM_START = 0xFAB0FAB1
DESYNC_FLAG = 20

FABRIC_NUM_IO = 32

run_all_zeros   = False
run_all_ones    = False
run_counter     = True
run_passthrough = False

def set_fabric_io(dut, value):
    value = value & (1<<FABRIC_NUM_IO)-1

    dut.iobuf_in_i.value = value

def get_fabric_io(dut):
    value = dut.iobuf_out_o.value
    
    return value

async def reset_design(dut):
    dut.rst_ni.value = 0
    await ClockCycles(dut.clk_i, 10)
    dut.rst_ni.value = 1

async def set_defaults(dut):
    dut.bitstream_data_i.value = 0
    dut.bitstream_valid_i.value = 0
    
    dut.iobuf_in_i.value = 0
    
    print('Clearing bitstream!')
    
    # Reset all frames to zero
    await zero_bitstream(dut)
    
    print('Bitstream cleared!')

async def zero_bitstream(dut):
    """
    Upload an all-zeros bitstream in reverse to prevent
    logic loops before uploading a new user design.
    
    For faster clearing enable all FrameStrobe signals
    of a column at once.
    
    Note: Still does not reliably prevent logic loops...
    """

    # Write start of bitstream
    dut.bitstream_valid_i.value = 1
    dut.bitstream_data_i.value = BITSTREAM_START
    await ClockCycles(dut.clk_i, 1)
    
    # Write zero frames in reverse
    for column in reversed(range(FABRIC_NUM_COLUMNS)):
    
        # Write header, clear all frames of a column at once
        dut.bitstream_data_i.value = column<<(FRAME_BITS_PER_ROW-FRAME_SELECT_WIDTH) | ((1<<MAX_FRAMES_PER_COL)-1)
        await ClockCycles(dut.clk_i, 1)

        # Write row data
        dut.bitstream_data_i.value = 0x00000000
        await ClockCycles(dut.clk_i, FABRIC_NUM_ROWS)

    # Write desync bit
    dut.bitstream_data_i.value = 1<<DESYNC_FLAG
    await ClockCycles(dut.clk_i, 1)

async def upload_bitstream(dut, name):
    """
    Read data until start of bitstream is detected
    Write data until desync bit is in header
    """

    print(f'Uploading bitstream: {name}')

    proj_path = Path(__file__).resolve().parent
    with open(proj_path / f'../user_designs/designs/{name}/{name}.bit', 'br') as f:

        # Wait for start of bitstream
        while (data := f.read(4)) != None:
            number = int.from_bytes(data, "big")
            if number == BITSTREAM_START:
                print('Start of bitstream')
                
                # Write start of bitstream
                dut.bitstream_valid_i.value = 1
                dut.bitstream_data_i.value = number
                await ClockCycles(dut.clk_i, 1)

                if WAIT_CYCLES:
                    dut.bitstream_valid_i.value = 0
                    await ClockCycles(dut.clk_i, WAIT_CYCLES)

                break
    
        # Read bitstream content
        while 1:
        
            # Read header
            data = f.read(4)
            if data == None:
                break
            header = int.from_bytes(data, "big")
            
            print(f'--- header: 0x{header:08x}')

            # Write header
            dut.bitstream_valid_i.value = 1
            dut.bitstream_data_i.value = header
            await ClockCycles(dut.clk_i, 1)
            
            if WAIT_CYCLES:
                dut.bitstream_valid_i.value = 0
                await ClockCycles(dut.clk_i, WAIT_CYCLES)

            # Desync
            if header & (1<<DESYNC_FLAG):
                print("Detected desync flag!")
                break
            
            # Read row data
            for i in range(FABRIC_NUM_ROWS):
                row_data = int.from_bytes(f.read(4), "big")
                
                print(f'0x{row_data:08x}')
                
                # Write row data
                dut.bitstream_valid_i.value = 1
                dut.bitstream_data_i.value = row_data
                await ClockCycles(dut.clk_i, 1)
                
                if WAIT_CYCLES:
                    dut.bitstream_valid_i.value = 0
                    await ClockCycles(dut.clk_i, WAIT_CYCLES)
        
        print(f'Bitstream upload completed')
        
        # Stop the bitstream
        dut.bitstream_valid_i.value = 0
        dut.bitstream_data_i.value = 0
        await ClockCycles(dut.clk_i, 1)

@cocotb.test(skip=True)
async def test_default(dut):
    """No bitstream loaded"""

    # Start the clock
    c = Clock(dut.clk_i, 10, 'ns')
    await cocotb.start(c.start())

    # Assign default values
    await set_defaults(dut)
    await reset_design(dut)
    dut._log.info("Reset done")
    
    await ClockCycles(dut.clk_i, 10)

@cocotb.test(skip=run_all_zeros==False)
async def test_all_zeros(dut):
    """Load bitstream to set output to zero"""

    # Start the clock
    c = Clock(dut.clk_i, 10, 'ns')
    await cocotb.start(c.start())

    # Assign default values
    await set_defaults(dut)
    await reset_design(dut)
    dut._log.info("Reset done")
    
    # Defaults
    dut.clk.value = 0
    dut.clk2.value = 0
    dut.rst.value = 0
    dut.en.value = 0
    dut.iobuf_in_upper_i.value = 0
    
    await upload_bitstream(dut, 'all_zeros')
    
    values = [random.randint(0,(1<<32)-1) for _ in range(10)]
    
    await ClockCycles(dut.clk_i, 10)
    
    for value in values:
        set_fabric_io(dut, value)
        await ClockCycles(dut.clk_i, 1)
        assert(get_fabric_io(dut) == 0)
    
    await ClockCycles(dut.clk_i, 10)

@cocotb.test(skip=run_all_ones==False)
async def test_all_ones(dut):
    """Load bitstream to set output to ones"""

    # Start the clock
    c = Clock(dut.clk_i, 10, 'ns')
    await cocotb.start(c.start())

    # Assign default values
    await set_defaults(dut)
    await reset_design(dut)
    dut._log.info("Reset done")
    
    await upload_bitstream(dut, 'all_ones')

    values = [random.randint(0,(1<<FABRIC_NUM_IO)-1) for _ in range(10)]
    
    for value in values:
        set_fabric_io(dut, value)
        await ClockCycles(dut.clk_i, 1)
        assert(get_fabric_io(dut) == (1<<FABRIC_NUM_IO)-1)
    
    await ClockCycles(dut.clk_i, 10)

@cocotb.test(skip=run_counter==False)
async def test_counter(dut):
    """Load bitstream for counter"""

    # Start the clock
    c = Clock(dut.clk_i, 10, 'ns')
    await cocotb.start(c.start())

    # Assign default values
    await set_defaults(dut)
    await reset_design(dut)
    dut._log.info("Reset done")
    
    await upload_bitstream(dut, 'counter')
    
    # Defaults
    dut.clk.value = 0
    dut.clk2.value = 0
    dut.rst.value = 0
    dut.en.value = 0
    dut.iobuf_in_upper_i.value = 0
    
    # Reset
    dut.rst.value = 1
    await ClockCycles(dut.clk_i, 5)
    
    c = Clock(dut.clk, 10, 'ns')
    await cocotb.start(c.start())
    
    await ClockCycles(dut.clk_i, 5)
    dut.rst.value = 0
    
    MAX_CNT = 30
    
    await ClockCycles(dut.clk_i, MAX_CNT)
    assert(get_fabric_io(dut) == MAX_CNT-1)

@cocotb.test(skip=run_passthrough==False)
async def test_passthrough(dut):
    """Load bitstream for test_passthrough"""

    # Start the clock
    c = Clock(dut.clk_i, 10, 'ns')
    await cocotb.start(c.start())

    # Assign default values
    await set_defaults(dut)
    await reset_design(dut)
    dut._log.info("Reset done")

    await upload_bitstream(dut, 'passthrough')
    
    values = [random.randint(0,(1<<FABRIC_NUM_IO)-1) for _ in range(10)]
    
    for value in values:
        set_fabric_io(dut, value)
        await ClockCycles(dut.clk_i, 1)
        assert(get_fabric_io(dut) == value)
    
    await ClockCycles(dut.clk_i, 10)

if __name__ == "__main__":

    sim = os.getenv("SIM", "icarus")
    pdk_root = os.getenv("PDK_ROOT", Path("~/.ciel").expanduser())
    pdk = os.getenv("PDK", "ihp-sg13g2")
    scl = os.getenv("SCL", "gf180mcu_fd_sc_mcu7t5v0")
    gl = os.getenv("GL", None)
    
    fabric = os.getenv("FABRIC", "fabric_10x10")
    
    proj_path = Path(__file__).resolve().parent
    
    tile_library = os.getenv("TILE_LIBRARY", proj_path / ".." / "ip" / "fabulous-tiles")

    primitives_path = Path(tile_library) / "primitives"
    tiles_path = Path(tile_library) / "tiles"

    primitives_files = list(primitives_path.glob('**/fabulous/*.v'))
    tile_files = list(tiles_path.glob(f'**/macro/{pdk}/fabulous/*.v'))

    print(f"Primitive sources: {primitives_files}")
    print(f"Tile sources: {tile_files}")
    
    sources = []
    
    sources.extend(primitives_files)
    sources.extend(tile_files)
    
    # Add models pack
    sources.append(Path(tile_library) / "models_pack.v")

    # Add fabric wrapper
    sources.append(proj_path / f'../fabrics/{fabric}/fabric_wrapper.sv')

    # Add fabric netlist
    sources.append(proj_path / f'../fabrics/{fabric}/macro/{pdk}/fabulous/eFPGA.v')

    # Add testbench wrapper
    sources.append(proj_path / 'tb_icarus.sv')
    
    # Add fabric config
    sources.append(proj_path / '../ip/fabric_config/fabric_config.sv')

    # Add fabric config
    sources.append(proj_path / '../ip/fabric_spi/fabric_spi_receiver.sv')

    hdl_toplevel = "tb"

    runner = get_runner(sim)
    runner.build(
        sources=sources,
        hdl_toplevel=hdl_toplevel,
        defines={'COCOTB': True, 'FUNCTIONAL': True, 'UNIT_DELAY': '#0'},
        always=True,
    )

    runner.test(
        hdl_toplevel=hdl_toplevel,
        test_module="tb_cocotb,",
        plusargs=['-fst'],
        waves=True
    )
