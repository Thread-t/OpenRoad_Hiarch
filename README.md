╔════════════════════════════════════════════════════════════╗
║     NETLIST PARTITIONING & OPENROAD FLOORPLAN GENERATOR    ║
╚════════════════════════════════════════════════════════════╝

A Python flow for partitioning gate-level Verilog designs and generating
configurable OpenROAD floorplanning and implementation scripts.

Author: Sayak Deb

✨ FEATURES
───────────
• Gate-level Verilog parsing and module partitioning
• Liberty/LEF-based area estimation
• Automatic or manual floorplanning
• Floorplan boundary and overlap validation
• OpenROAD TCL generation
• Top-level wrapper generation
• Block-specific placement/routing settings
• Metal3/Metal4 pin placement
• Partition metadata and summaries

📁 PROJECT STRUCTURE
────────────────────
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

⚙️ CONFIGURATION
────────────────
Edit:

    configs/config.json

Key settings include:
    top_module
    top_wrapper_module
    adder_module
    multiplier_module
    manual_floorplan
    block_overrides

▶️ RUN
──────
From the project root:

    python3 scripts/split_net_v4.py

Custom configuration:

    python3 scripts/split_net_v4.py <config_file>

Help:

    python3 scripts/split_net_v4.py --help

📤 OUTPUT
─────────
Generated partition Verilog files, OpenROAD TCL scripts,
top_wrapper.v, and partition_info.json are written to the
configured output directory.

🛠️ TROUBLESHOOTING
───────────────────
• Check module names against the Verilog netlist.
• Verify Liberty/LEF paths and technology compatibility.
• Run from the project root.
• Check manual floorplan coordinates and region overlap.
• Reduce placement density if routing fails.

────────────────────────────────────────────────────────────
Project: Netlist Partitioning & OpenROAD Floorplan Generator
Main script: scripts/split_net_v4.py
