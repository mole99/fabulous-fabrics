# User Designs

The following user designs are available:

| Name      | Description |
|-----------|-------------|
| `all_zeros` | all outputs set to zero |
| `all_ones`  | all outputs set to one |
| `counter`   | 32-bit counter |
| `passthrough` | inputs connected to outputs |

The intention was for these example designs to be as generic as possible, so they can be reused for various fabrics.


## Requirements

Enable a Nix shell with Yosys and nextpnr:

```
nix shell nixpkgs#{yosys,nextpnr}
```

**Note:** To generate the bitstreams you need to `pip3 install fasm`.

## Implement the Designs

To build individual user designs, go into one of the directories and run the commands:

```
make all
```

```
make all_zeros
```

```
make all_zeros-synth
make all_zeros-pnr
make all_zeros-bit
make all_zeros-hex
```

You can also enter the individual design directories and run make from there:

```
Commands:
 synth           ... Synthesize the user design
 pnr             ... Run Place and Route
 bitstream       ... Generate the bitstream
 clean           ... Delete all generated files
 help            ... Show this help message
```

---


export PATH=~/Repositories/yosys:$PATH
export PATH=~/Repositories/nextpnr/build/:$PATH
