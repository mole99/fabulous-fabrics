# SPDX-FileCopyrightText: © 2026 FABulous Contributors
# SPDX-License-Identifier: Apache-2.0

import os
import random
from pathlib import Path
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, Timer
from cocotb.types import LogicArray, Logic

from .common import zero_bitstream, upload_bitstream, PCF

testname = Path(__file__).stem
proj_path = Path(__file__).resolve().parent
fabric = os.getenv("FABRIC", "fabric_10x10")

@cocotb.test()
async def test_multiplication(dut):
    """Load bitstream for multiplication"""

    pcf = PCF(dut, proj_path / f"../../fabrics/{fabric}/constraints.pcf")
    pcf.write_gtkw(f"{testname}.gtkw", ["a", "b", "c"])

    # Zero all config bits
    await zero_bitstream(dut)
    await Timer(10, unit="ns")

    # Upload the bitstream
    await upload_bitstream(dut, proj_path / f'../../user_designs/designs/{testname}/{testname}.bit')
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
