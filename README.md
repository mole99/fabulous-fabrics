# FABulous Fabrics

This repository contains a collection of fabrics using the [fabulous-tiles](https://github.com/mole99/fabulous-tiles) tile libraries.

The fabrics can be found under `fabrics/`.

- classic_fabric_10x10
- classic_fabric_32x32
- tiny_fabric_5x5

The prefix describes the tile library that is used, either `classic` or `tiny`.

The fabrics can be implemented with LibreLane using the FABulous plugin for LibreLane: [librelane_plugin_fabulous](https://github.com/mole99/librelane_plugin_fabulous).
See below for more information about stitching the fabric. 

TODO documentation

A Continuous Integration (CI) setup implements all of the fabrics for the gf180mcu, sky130, and ihp-sg13g2 PDKs.

## Requirements

For information on installing Nix with the FOSSi Foundation cache, please refer to the LibreLane documentation: https://librelane.readthedocs.io/en/stable/installation/nix_installation/index.html

## Stitch the Fabrics

As a prerequisite make sure that the tiles for the tile library that you are using have been implemented in `ip/fabulous-tiles`.

If so, you can proceed by enabling a Nix shell with LibreLane in this repository:

```
nix-shell
```

To implement all fabrics, run:

```
make all
```

To implement a single fabric, run:

```
make classic_fabric_10x10
```

After a fabrics has been implemented you can view it either in OpenROAD or KLayout by appending `-openroad` or `-klayout` to the fabric name.
For example, to view `classic_fabric_10x10` in OpenROAD, run: `make classic_fabric_10x10-openroad`.

By default the fabrics are implemented using the ihp-sg13g2 PDK.
The currently supported PDKs are: `gf180mcu`, `sky130`, `ihp-sg13g2`.

To change the PDK, set the `PDK` environment variable:

```
export PDK=gf180mcu
```

## Implement the User Designs

Currently, forks of Yosys and nextpnr are required in order to implement the user designs. The changes to these forks are being upstreamed.

You can enable a Nix shell with these forks by running:

```
cd user_designs; nix-shell
```

The user designs for both fabric families can be found under `user_designs/designs/`.
Before you build the user designs, you need to select for which tile library and fabric you want to implement the design.

The default is:

```
export FABRIC=classic_fabric_10x10
export TILE_LIBRARY=classic
```

You can change it for example to:

```
export FABRIC=tiny_fabric_5x5
export TILE_LIBRARY=tiny
```

Finally, you can build the user designs for the fabric:

```
make all
```

Or you can build individual user designs

```
make counter
```

The following Make targets are available:

```
make counter-clean
make counter-synth
make counter-pnr
make counter-bit
make counter-hex
```

## Simulate the Fabric

After you have generated the bitstreams for the user designs you can simulate the fabric.
You will again need the Nix shell from the root of this repository.

Again, use `FABRIC` and `TILE_LIBRARY` to select both accordingly.

There are two ways to simulate the fabric:

#### RTL "Emulation"

In this case, "emulation" means that we simulate the fabric, however, without uploading the bitstream.
The configuration bits of the fabric are already initialized with the user design bitstream.
This has the benefit that simulation is much faster: no need to upload the bitstream and the Verilog simulator can prune dead branches. However, the disadvantage is that only a single user design can be run per simulation.

To emulate a user design, simply set EMULATE to its name:

```
export EMULATE=counter
```

Then, run the simulation using cocotb:

```
cd tb; python3 bare_tb.py
```

#### RTL Simulation

To start the RTL simulation, simply run cocotb:

```
cd tb; python3 bare_tb.py
```

And it will run all available test cases for the selected fabric and tile library.
