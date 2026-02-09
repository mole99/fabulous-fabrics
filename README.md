# FABulous Fabrics

This repository contains a collection of fabrics using the [default tile library](https://github.com/mole99/fabulous-tiles) of FABulous.

The fabrics can be found under `fabrics/`.

The fabrics can be implemented with LibreLane using the FABulous plugin for LibreLane: [librelane_plugin_fabulous](https://github.com/mole99/librelane_plugin_fabulous).

TODO documentation

A Continuous Integration (CI) setup implements all of the fabrics for the gf180mcu, sky130, and ihp-sg13g2 PDKs.

## Requirements

For information on installing Nix with the FOSSi Foundation cache, please refer to the LibreLane documentation: https://librelane.readthedocs.io/en/stable/installation/nix_installation/index.html

## Stitch the Tiles into Fabrics

First, enable a Nix shell with LibreLane:

```
nix-shell
```

To implement all fabrics, run:

```
make all
```

To implement a single fabric, run:

```
make fabric_8x8
```

After a fabrics has been implemented you can view it either in OpenROAD or KLayout:

By default the fabrics are implemented using the ihp-sg13g2 PDK.
The supported PDKs are: `gf180mcu`, `sky130`, `ihp-sg13g2`.

To change the PDK, set the `PDK` environment variable:

```
PDK=gf180mcu make all
```
