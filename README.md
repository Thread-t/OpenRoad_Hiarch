# Netlist Partitioning & OpenROAD Floorplan Generator

A Python-based flow for partitioning gate-level Verilog designs and generating configurable **OpenROAD floorplanning and implementation scripts**.

**Author:** Sayak Deb

## Features

* Gate-level Verilog parsing and module partitioning
* Liberty/LEF-based area estimation
* Automatic and manual floorplanning
* Floorplan boundary and overlap validation
* OpenROAD TCL generation
* Top-level wrapper generation
* Block-specific placement and routing settings
* Metal3/Metal4 pin placement
* Partition metadata and summaries

## Project Structure

```text
project/
├── scripts/
│   └── split_net_v4.py
├── configs/
│   └── config.json
├── inputs/
│   ├── *.v
│   ├── *.lib
│   └── *.lef
└── generated/
    ├── partitions/
    ├── tcl/
    ├── top_wrapper.v
    └── partition_info.json
```

## Configuration

Edit:

```text
configs/config.json
```

Key settings:

```text
top_module
top_wrapper_module
adder_module
multiplier_module
manual_floorplan
block_overrides
```

## Run

From the project root:

```bash
python3 scripts/split_net_v4.py
```

Use a custom configuration:

```bash
python3 scripts/split_net_v4.py <config_file>
```

Show available options:

```bash
python3 scripts/split_net_v4.py --help
```

## Output

The flow generates:

* Partitioned Verilog files
* OpenROAD TCL scripts
* `top_wrapper.v`
* `partition_info.json`

Generated files are placed in the configured output directory.

## Troubleshooting

* Check module names against the Verilog netlist.
* Verify Liberty and LEF paths.
* Make sure the technology files are compatible.
* Run the script from the project root.
* Check manual floorplan coordinates and region overlap.
* Reduce placement density if routing fails.

---

**Project:** Netlist Partitioning & OpenROAD Floorplan Generator
**Main Script:** `scripts/split_net_v4.py`
