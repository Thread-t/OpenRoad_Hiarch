# ═══════════════════════════════════════════════════════════════════
#
#   split_net_v4.py
#   ────────────────────────────────────────────────────────────────
#   Netlist Partitioning & OpenROAD TCL Generator
#
#   Final combined version based on:
#   - split_net_v2_sayak.py
#   - split_net_v3_arya.py
#
#   Main features:
#   1. Parses multi-module gate-level Verilog.
#   2. Splits selected partition modules into separate .v files.
#   3. Reads area information from Liberty and LEF files.
#   4. Supports automatic area-based floorplan.
#   5. Supports manual floorplan from config.json.
#   6. Preserves base logic:
#      - each block has its own region
#      - sibling/blocked region information is kept
#   7. Generates OpenROAD TCL per block.
#   8. Fixes OpenROAD path issues by cd'ing to project root.
#   9. Disables unsupported create_blockage -bbox command.
#   10. Adds routing fixes for multiplier:
#       - lower density
#       - metal3/metal4 pin placement
#       - optional routing layer guidance
#   11. Generates top_wrapper.v for later top-level connection.
#
#   Author  : Sayak Deb
#   Project : Digital Lab — Third Semester, Bremen
#   Tools   : Python 3, OpenROAD, Yosys, Nangate45 Open Cell Library
#
# ═══════════════════════════════════════════════════════════════════

import os
import re
import json
import sys
import copy


# ==========================================================
# ARYA UPDATE V1:
# Added project-root path handling.
# This avoids hardcoded Windows/Linux paths and makes the
# script portable for all team members.
# ==========================================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# ==========================================================
# ARYA UPDATE V14:
# The script is stored inside the scripts/ directory.
# Therefore, the project root is one directory above it.
# This keeps inputs/, configs/, and generated/ paths correct.
# ==========================================================
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)


def project_path(path):
    """Return absolute path relative to project root."""
    if os.path.isabs(path):
        return path
    return os.path.join(PROJECT_ROOT, path)


def tcl_path(path):
    """
    ARYA UPDATE V6:
    Convert an absolute/relative path into a TCL-friendly path
    relative to the project root, using forward slashes.

    Example:
    C:\\...\\Hierarchical_OpenROAD_Framework\\inputs\\file.lef
    becomes:
    inputs/file.lef

    This avoids Windows paths inside OpenROAD TCL.
    """
    rel = os.path.relpath(path, PROJECT_ROOT)
    return rel.replace("\\", "/")

# ==========================================================
# DEFAULT CONFIG
# ==========================================================

DEFAULT_CONFIG = {
    # Full chip dimensions used for partition planning
    "chip_width": 200.0,
    "chip_height": 200.0,
    "dbu_per_micron": 1000,

    # OpenROAD floorplan defaults
    "utilization": 0.70,
    "margin": 3.0,
    "site": "FreePDK45_38x28_10R_NP_162NW_34O",

    # Default folder structure
    "output_dir": "generated",

    # Input files
    "verilog_file": "inputs/top_design_gate.v",
    "lib_file": "inputs/NangateOpenCellLibrary_typical.lib",
    "tech_lef_file": "inputs/NangateOpenCellLibrary.tech.lef",
    "lef_file": "inputs/NangateOpenCellLibrary.macro.mod.lef",

    # Current base-flow blocks
    # Later we can generalize this to any number of blocks.
    "top_module": "top_design",
    "top_wrapper_module": "top_wrapper",
    "adder_module": "adder_32",
    "multiplier_module": "multiplier_32",

    # Generate top_wrapper.v for later macro/top-level connection
    "generate_top_wrapper": True,

    # Manual floorplan support
    # If enable = True, automatic area-based split is ignored.
    "manual_floorplan": {
        "enable": False,

        "adder_32": {
            "llx_um": 0.0,
            "lly_um": 0.0,
            "urx_um": 120.0,
            "ury_um": 200.0
        },

        "multiplier_32": {
            "llx_um": 120.0,
            "lly_um": 0.0,
            "urx_um": 200.0,
            "ury_um": 200.0
        }
    },

    # Block-specific OpenROAD settings
    # Main purpose: fix multiplier routing congestion.
    "block_overrides": {
        "adder_32": {
            "placement_density": 0.70,
            "pin_hor_layer": "metal3",
            "pin_ver_layer": "metal4"
        },

        "multiplier_32": {
            "placement_density": 0.55,
            "pin_hor_layer": "metal3",
            "pin_ver_layer": "metal4"
        }
    }
}


# ==========================================================
# CONFIG LOADING
# ==========================================================

def deep_update(base, update):
    """Recursively update nested dictionaries."""
    for key, value in update.items():
        if (
            isinstance(value, dict)
            and key in base
            and isinstance(base[key], dict)
        ):
            deep_update(base[key], value)
        else:
            base[key] = value
    return base


def load_config(json_path=None):
    """
    Load config from JSON.
    Default config path:
      configs/config.json

    Usage:
      python scripts/split_net_v4.py
      python scripts/split_net_v4.py configs/config.json
    """

    config = copy.deepcopy(DEFAULT_CONFIG)

    if json_path is None:
        json_path = project_path("configs/config.json")
    else:
        json_path = project_path(json_path)

    if os.path.exists(json_path):
        print(f"Loading config: {json_path}")
        with open(json_path, "r") as f:
            user_config = json.load(f)
        config = deep_update(config, user_config)
    else:
        print("No config file found. Using built-in defaults.")

    # Convert important paths to absolute internally
    for key in [
        "output_dir",
        "verilog_file",
        "lib_file",
        "tech_lef_file",
        "lef_file"
    ]:
        config[key] = project_path(config[key])

    return config


# ==========================================================
# VERILOG PARSING
# ==========================================================

SKIP_KEYWORDS = {
    "module", "endmodule", "input", "output", "inout",
    "wire", "reg", "logic", "assign", "always", "begin",
    "end", "if", "else", "case", "endcase", "generate",
    "endgenerate", "for", "genvar", "parameter", "localparam",
    "function", "task", "initial", "posedge", "negedge",
    "integer", "signed", "unsigned", "default"
}


def clean_verilog(content):
    """Remove Verilog comments."""
    content = re.sub(r"//[^\n]*", "", content)
    content = re.sub(r"/\*.*?\*/", " ", content, flags=re.DOTALL)
    return content


def find_matching_paren(text, open_index):
    """Find matching closing parenthesis for text[open_index] == '('."""
    depth = 0
    for i in range(open_index, len(text)):
        if text[i] == "(":
            depth += 1
        elif text[i] == ")":
            depth -= 1
            if depth == 0:
                return i
    return -1


def parse_module_chunk(chunk):
    """
    Parse one module chunk without relying only on fragile regex.

    Returns:
      module_name, ports, body
    """

    module_match = re.search(
        r"\bmodule\s+([A-Za-z_][A-Za-z0-9_$]*)",
        chunk
    )

    if not module_match:
        return None

    module_name = module_match.group(1)
    pos = module_match.end()

    # Skip whitespace
    while pos < len(chunk) and chunk[pos].isspace():
        pos += 1

    # Optional parameter block: #( ... )
    if pos < len(chunk) and chunk[pos] == "#":
        hash_pos = pos
        paren_pos = chunk.find("(", hash_pos)
        if paren_pos != -1:
            close_pos = find_matching_paren(chunk, paren_pos)
            if close_pos != -1:
                pos = close_pos + 1

    # Find port list
    open_paren = chunk.find("(", pos)
    if open_paren == -1:
        ports = ""
        body_start = pos
    else:
        close_paren = find_matching_paren(chunk, open_paren)
        if close_paren == -1:
            ports = ""
            body_start = pos
        else:
            ports = chunk[open_paren + 1:close_paren].strip()

            semi = chunk.find(";", close_paren)
            if semi == -1:
                body_start = close_paren + 1
            else:
                body_start = semi + 1

    body = chunk[body_start:].strip()

    return module_name, ports, body


def count_cells(body):
    """
    Count cell/module instances inside a module body.

    This version avoids complex backslash character classes,
    so it works safely with:
      NAND2_X1 _123_ (
      INV_X1 _045_ (
      full_adder fa0 (
      adder_32 U_ADDER (

    It captures:
      token1 = cell/module type
      token2 = instance name
    """

    counts = {}

    # Safe pattern:
    # line starts with: <cell_type> <instance_name> (
    #
    # Examples matched:
    #   NAND2_X1 _123_ (
    #   INV_X1 _045_ (
    #   full_adder fa0 (
    #   multiplier_32 U_MULTIPLIER (
    #
    # It avoids complicated [] character classes.
    pattern = re.compile(
        r"^\s*([^\s#();,]+)\s+"
        r"(?:#\s*$[^;]*?$\s*)?"
        r"([^\s(]+)\s*$",
        re.MULTILINE
    )

    for match in pattern.finditer(body):
        cell_type = match.group(1)
        inst_name = match.group(2)

        # Skip Verilog keywords
        if cell_type.lower() in SKIP_KEYWORDS:
            continue

        # Skip compiler directives if any
        if cell_type.startswith("`"):
            continue

        counts[cell_type] = counts.get(cell_type, 0) + 1

    return counts


def parse_verilog(verilog_file):
    """
    Parse multi-module Verilog file.

    Returns:
      module_names
      module_contents[module] = {ports, body}
      cell_counts_per_module[module] = {cell_type: count}
    """

    print("\n=======================================================")
    print("PARSING VERILOG:", verilog_file)
    print("=======================================================")

    if not os.path.exists(verilog_file):
        raise FileNotFoundError(f"Verilog file not found: {verilog_file}")

    with open(verilog_file, "r") as f:
        raw = f.read()

    clean = clean_verilog(raw)

    chunks = re.split(r"\bendmodule\b", clean)

    module_names = []
    module_contents = {}
    cell_counts_per_module = {}

    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue

        parsed = parse_module_chunk(chunk)
        if parsed is None:
            continue

        module_name, ports, body = parsed

        module_names.append(module_name)
        module_contents[module_name] = {
            "ports": ports,
            "body": body
        }

        counts = count_cells(body)
        cell_counts_per_module[module_name] = counts

        print(f"Found module: {module_name}")
        if counts:
            print(f"  Cell/module instances: {counts}")
        else:
            print("  No cell/module instances found")

    print("\nModules found:", module_names)

    return module_names, module_contents, cell_counts_per_module


# ==========================================================
# LIB / LEF AREA PARSING
# ==========================================================

def get_cell_area_from_lib(lib_file):
    """Extract cell area values from Liberty file."""

    print("\n=======================================================")
    print("READING LIB:", lib_file)
    print("=======================================================")

    if not os.path.exists(lib_file):
        raise FileNotFoundError(f"LIB file not found: {lib_file}")

    with open(lib_file, "r") as f:
        content = f.read()

    content = re.sub(r"/\*.*?\*/", " ", content, flags=re.DOTALL)

    cell_areas = {}

    cells = list(re.finditer(
        r"\bcell\s*$\s*[\"\']?([A-Za-z_][A-Za-z0-9_]*)[\"\']?\s*$",
        content
    ))

    print(f"Cell definitions found in LIB: {len(cells)}")

    for i, cell in enumerate(cells):
        name = cell.group(1)
        start = cell.end()
        end = cells[i + 1].start() if i + 1 < len(cells) else len(content)
        body = content[start:end]

        area_match = re.search(r"\barea\s*:\s*([0-9.eE+-]+)\s*;", body)

        if area_match:
            area = float(area_match.group(1))
            cell_areas[name] = area

    print(f"Cell areas extracted from LIB: {len(cell_areas)}")

    return cell_areas


def get_cell_area_from_lef(lef_file):
    """Extract cell area from LEF MACRO SIZE statements."""

    print("\n=======================================================")
    print("READING LEF:", lef_file)
    print("=======================================================")

    if not os.path.exists(lef_file):
        raise FileNotFoundError(f"LEF file not found: {lef_file}")

    with open(lef_file, "r") as f:
        content = f.read()

    # Remove LEF comments
    content = re.sub(r"#.*", "", content)

    cell_areas = {}

    pattern = re.compile(
        r"\bMACRO\s+([A-Za-z_][A-Za-z0-9_]*)"
        r".*?\bSIZE\s+([0-9.eE+-]+)\s+BY\s+([0-9.eE+-]+)\s*;",
        re.DOTALL
    )

    matches = list(pattern.finditer(content))

    print(f"MACRO definitions with SIZE found in LEF: {len(matches)}")

    for match in matches:
        name = match.group(1)
        width = float(match.group(2))
        height = float(match.group(3))
        cell_areas[name] = width * height

    print(f"Cell areas extracted from LEF: {len(cell_areas)}")

    return cell_areas


def merge_area_sources(lib_areas, lef_areas):
    """
    Use LIB areas where available and positive.
    Use LEF area for missing or zero LIB entries.
    """

    merged = dict(lib_areas)

    for cell, lef_area in lef_areas.items():
        if cell not in merged or merged[cell] <= 0:
            merged[cell] = lef_area

    return merged


# ==========================================================
# HIERARCHICAL AREA ESTIMATION
# ==========================================================

def estimate_module_area(
    module_name,
    cell_counts_per_module,
    cell_areas,
    module_stack=None,
    default_unknown_area=0.1
):
    """
    Estimate area for module.

    If instance type is a standard cell:
      use cell_areas[cell]

    If instance type is another module:
      recursively estimate that module area.

    If unknown:
      use default area.
    """

    if module_stack is None:
        module_stack = []

    if module_name in module_stack:
        print(f"WARNING: recursive module reference detected: {module_name}")
        return 0.0

    module_stack.append(module_name)

    counts = cell_counts_per_module.get(module_name, {})
    total = 0.0

    for inst_type, count in counts.items():
        if inst_type in cell_areas:
            total += count * cell_areas[inst_type]

        elif inst_type in cell_counts_per_module:
            sub_area = estimate_module_area(
                inst_type,
                cell_counts_per_module,
                cell_areas,
                module_stack[:],
                default_unknown_area
            )
            total += count * sub_area

        else:
            print(
                f"WARNING: Unknown cell/module '{inst_type}', "
                f"using default area {default_unknown_area} um²"
            )
            total += count * default_unknown_area

    # 30% routing overhead
    return total * 1.3


# ==========================================================
# FLOORPLAN VALIDATION
# ==========================================================

def region_area(region):
    return (
        (region["urx_um"] - region["llx_um"])
        * (region["ury_um"] - region["lly_um"])
    )


def regions_overlap(r1, r2):
    return not (
        r1["urx_um"] <= r2["llx_um"]
        or r2["urx_um"] <= r1["llx_um"]
        or r1["ury_um"] <= r2["lly_um"]
        or r2["ury_um"] <= r1["lly_um"]
    )


def validate_region(name, region, config):
    required = {"llx_um", "lly_um", "urx_um", "ury_um"}

    missing = required - set(region.keys())
    if missing:
        raise ValueError(f"Region for {name} missing keys: {missing}")

    if region["llx_um"] < 0 or region["lly_um"] < 0:
        raise ValueError(f"Region for {name} has negative coordinate: {region}")

    if region["urx_um"] <= region["llx_um"]:
        raise ValueError(f"Region for {name} has invalid X range: {region}")

    if region["ury_um"] <= region["lly_um"]:
        raise ValueError(f"Region for {name} has invalid Y range: {region}")

    if region["urx_um"] > config["chip_width"]:
        raise ValueError(f"Region for {name} exceeds chip width: {region}")

    if region["ury_um"] > config["chip_height"]:
        raise ValueError(f"Region for {name} exceeds chip height: {region}")


# ==========================================================
# VERILOG OUTPUT GENERATION
# ==========================================================

def extract_module_to_file(module_contents, module_name, output_path):
    """Write one module into a separate Verilog file."""

    if module_name not in module_contents:
        raise ValueError(f"Module {module_name} not found")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    mod = module_contents[module_name]

    with open(output_path, "w") as f:
        f.write("// Auto-extracted by split_net_v4.py\n")
        f.write(f"// Module: {module_name}\n\n")
        f.write(f"module {module_name} (\n")
        f.write(f"    {mod['ports']}\n")
        f.write(");\n\n")
        f.write(mod["body"])
        f.write("\nendmodule\n")

    print("Generated Verilog:", output_path)


def generate_top_wrapper(module_contents, config, output_dir):
    """
    Generate top_wrapper.v.

    This reconnects the partitioned blocks later.
    It contains:
      - black-box declaration for adder module
      - black-box declaration for multiplier module
      - wrapper module containing original top body
    """

    top_module = config["top_module"]
    wrapper_module = config["top_wrapper_module"]

    adder_module = config["adder_module"]
    mult_module = config["multiplier_module"]

    for module in [top_module, adder_module, mult_module]:
        if module not in module_contents:
            raise ValueError(f"Module '{module}' not found for wrapper generation")

    wrapper_path = os.path.join(output_dir, "top_wrapper.v")
    os.makedirs(output_dir, exist_ok=True)

    top_ports = module_contents[top_module]["ports"]
    top_body = module_contents[top_module]["body"]

    adder_ports = module_contents[adder_module]["ports"]
    mult_ports = module_contents[mult_module]["ports"]

    with open(wrapper_path, "w") as f:
        f.write("// ======================================================\n")
        f.write("// Auto-generated top wrapper\n")
        f.write("// Used to reconnect separated partition blocks\n")
        f.write("// ======================================================\n\n")

        f.write("// Black-box declaration for first partition\n")
        f.write(f"module {adder_module} (\n")
        f.write(f"    {adder_ports}\n")
        f.write(");\n")
        f.write("endmodule\n\n")

        f.write("// Black-box declaration for second partition\n")
        f.write(f"module {mult_module} (\n")
        f.write(f"    {mult_ports}\n")
        f.write(");\n")
        f.write("endmodule\n\n")

        f.write("// Top wrapper connecting both partitions\n")
        f.write(f"module {wrapper_module} (\n")
        f.write(f"    {top_ports}\n")
        f.write(");\n\n")
        f.write(top_body)
        f.write("\nendmodule\n")

    print("Generated top wrapper:", wrapper_path)
    return wrapper_path


# ==========================================================
# TCL GENERATION
# ==========================================================

def generate_tcl(
    config,
    block_name,
    verilog_path,
    output_dir,
    own_region,
    blocked_region
):
    """
    Generate OpenROAD TCL script for one partition.

    Preserves base logic:
      - own_region is used for this block floorplan
      - blocked_region is recorded as sibling region
      - create_blockage is kept as comment because unsupported

    Adds routing fixes:
      - block-specific placement density
      - metal3/metal4 pins by default
      - optional set_routing_layers
      - global_route fallback
    """

    reports_dir = os.path.join(output_dir, "reports")
    results_dir = os.path.join(output_dir, "results")

    os.makedirs(reports_dir, exist_ok=True)
    os.makedirs(results_dir, exist_ok=True)

    tcl_file_path = os.path.join(output_dir, f"{block_name}_flow.tcl")

    # ======================================================
    # ARYA UPDATE V7:
    # Use relative TCL paths so generated TCL does not contain
    # Windows-style C:\\ paths. This is important because
    # OpenROAD usually runs in Linux/WSL/Docker.
    # ======================================================

    tech_lef_tcl = tcl_path(config["tech_lef_file"])
    lef_tcl = tcl_path(config["lef_file"])
    lib_tcl = tcl_path(config["lib_file"])
    verilog_tcl = tcl_path(verilog_path)
    reports_tcl = tcl_path(reports_dir)
    results_tcl = tcl_path(results_dir)

    block_cfg = config.get("block_overrides", {}).get(block_name, {})

    placement_density = block_cfg.get(
        "placement_density",
        config.get("utilization", 0.70)
    )
    
    # ======================================================
    # ARYA UPDATE V10:
    # Use Metal3/Metal4 for IO pin placement.
    #
    # Reason:
    # Metal1/Metal2 pin placement caused detailed routing
    # failure (DRT-0255: Maze Route cannot find path).
    #
    # Using higher routing layers provides more routing
    # resources and avoids congestion near the cell rows.
    # ======================================================
    # Sayak : Directly passing metal 3 and metal 4 for pin placement in the TCL file
    pin_hor_layer = block_cfg.get("pin_hor_layer", "metal3")
    pin_ver_layer = block_cfg.get("pin_ver_layer", "metal4")

    with open(tcl_file_path, "w") as f:
        f.write("# ======================================================\n")
        f.write("# OpenROAD TCL generated by split_net_v4.py\n")
        f.write(f"# Block: {block_name}\n")
        f.write("# ======================================================\n\n")

        f.write("# Move to project root so relative paths work\n")
        f.write("set script_dir [file dirname [file normalize [info script]]]\n")
        f.write("set project_root [file normalize \"$script_dir/../..\"]\n")
        f.write("cd $project_root\n\n")

        f.write("# === Read technology files ===\n")
        f.write(f"read_lef     {tech_lef_tcl}\n")
        f.write(f"read_lef     {lef_tcl}\n")
        f.write(f"read_liberty {lib_tcl}\n\n")

        f.write("# === Read gate-level netlist ===\n")
        f.write(f"read_verilog {verilog_tcl}\n")
        f.write(f"link_design  {block_name}\n\n")

        f.write("# === Floorplan for this block region ===\n")
        f.write("# Base logic preserved: this block uses assigned chip region.\n")

        coordinate_mode = config.get("coordinate_mode", "global_partition")

        # Calculate die and core area based on coordinate mode
        # take local_macro coordinates and calculate accordingly #Sayak
        if coordinate_mode == "local_macro":
            die_llx = 0.0
            die_lly = 0.0
            die_urx = own_region["urx_um"] - own_region["llx_um"]
            die_ury = own_region["ury_um"] - own_region["lly_um"]

            core_llx = config["margin"]
            core_lly = config["margin"]
            core_urx = die_urx - config["margin"]
            core_ury = die_ury - config["margin"]

        else:
            die_llx = own_region["llx_um"]
            die_lly = own_region["lly_um"]
            die_urx = own_region["urx_um"]
            die_ury = own_region["ury_um"]

            core_llx = own_region["llx_um"] + config["margin"]
            core_lly = own_region["lly_um"] + config["margin"]
            core_urx = own_region["urx_um"] - config["margin"]
            core_ury = own_region["ury_um"] - config["margin"]
        # `````````````````````````````Sayak````````````````````````````````` #`

        # ======================================================
#         # ======================================================
        # ARYA UPDATE V15:
        # Coordinate-mode comments must be written before the
        # initialize_floorplan command.
        # ======================================================

        f.write(f"# Coordinate mode: {coordinate_mode}\n")

        if coordinate_mode == "local_macro":
            f.write(
                "# Local macro mode: block hardened from (0,0); "
                "global placement saved in JSON.\n"
            )
        else:
            f.write(
                "# Global partition mode: block hardened using "
                "full-chip coordinates.\n"
            )

        f.write("initialize_floorplan \\\n")
        f.write(
            f"  -die_area  \"{die_llx} {die_lly} {die_urx} {die_ury}\" \\\n"
        )
        f.write(
            f"  -core_area \"{core_llx} {core_lly} {core_urx} {core_ury}\" \\\n"
        )
        f.write(f"  -site      {config['site']}\n\n")

        f.write("# === Sibling blocked region information ===\n")
        f.write("# This region belongs to the other partition.\n")
        f.write("# Kept for base logic and later integration reference.\n")
        f.write(
            f"# blocked_region = "
            f"{blocked_region['llx_um']} {blocked_region['lly_um']} "
            f"{blocked_region['urx_um']} {blocked_region['ury_um']}\n"
        )
        # ======================================================
        # ARYA UPDATE V9:
        # Disabled create_blockage because this OpenROAD version
        # does not support the command:
        # create_blockage -bbox ...
        #
        # The floorplan region is still controlled by:
        # initialize_floorplan -die_area and -core_area.
        # ======================================================
        f.write("# create_blockage disabled: unsupported in this OpenROAD version\n")
        f.write(
            f"# create_blockage -bbox {{{blocked_region['llx_um']} {blocked_region['lly_um']} "
            f"{blocked_region['urx_um']} {blocked_region['ury_um']}}} "
            f"-type placement -name blockage_{block_name}\n\n"
        )

        f.write("# === Initialize routing tracks ===\n")
        f.write("make_tracks\n\n")

        # ======================================================
        # ======================================================
        # ARYA UPDATE V16:
        # Disabled signal-routing layer restriction.
        #
        # Restricting signals to metal4-metal10 caused DRT-0255
        # because the detailed router could not access some IO
        # and standard-cell pins through the lower layers.
        #
        # OpenROAD is now allowed to select the required routing
        # layers automatically.
        # ======================================================
        f.write("# === Routing layer guidance disabled ===\n")
        f.write("# set_routing_layers -signal metal4-metal10\n\n")

        f.write("# === Pin placement ===\n")
        f.write(
            f"place_pins -hor_layers {pin_hor_layer} "
            f"-ver_layers {pin_ver_layer}\n\n"
        )

        f.write("# === Global placement ===\n")
        f.write(f"global_placement -density {placement_density}\n\n")

        f.write("# === Detailed placement ===\n")
        f.write("detailed_placement\n")
        f.write("check_placement -verbose\n\n")

        f.write("# === Filler cells ===\n")
        f.write(
            "filler_placement "
            "\"FILLCELL_X8 FILLCELL_X4 FILLCELL_X2 FILLCELL_X1\"\n\n"
        )

        f.write("# === Routing ===\n")
        f.write("if {[catch {global_route -congestion_iterations 50} gr_result]} {\n")
        f.write("  puts \"global_route with congestion_iterations failed; running default global_route\"\n")
        f.write("  global_route\n")
        f.write("}\n")
        f.write(
            f"detailed_route -output_drc "
            f"{reports_tcl}/{block_name}.drc\n\n"
        )

        f.write("# === Reports ===\n")
        f.write("report_design_area\n")
        f.write("report_wns\n")
        f.write("report_tns\n\n")

        f.write("# === Export routed block DEF ===\n")
        f.write(
            f"write_def "
            f"{results_tcl}/{block_name}_placed_routed.def\n\n"
        )

        f.write("# === Optional abstract LEF for later macro-based flow ===\n")
        f.write("if {[info commands write_abstract_lef] != \"\"} {\n")
        f.write(
            f"  write_abstract_lef "
            f"{results_tcl}/{block_name}.lef\n"
        )
        f.write("} else {\n")
        f.write("  puts \"write_abstract_lef not available in this OpenROAD version\"\n")
        f.write("}\n")

    print("Generated TCL:", tcl_file_path)
    return tcl_file_path


# ==========================================================
# MAIN SPLIT FLOW
# ==========================================================

def split_design(config):

    # ------------------------------------------------------
    # Validate input files
    # ------------------------------------------------------
    for key in ["verilog_file", "lib_file", "tech_lef_file", "lef_file"]:
        if not os.path.exists(config[key]):
            raise FileNotFoundError(f"{key} not found: {config[key]}")

    # ------------------------------------------------------
    # Parse Verilog
    # ------------------------------------------------------
    module_names, module_contents, cell_counts = parse_verilog(
        config["verilog_file"]
    )

    adder_name = config["adder_module"]
    mult_name = config["multiplier_module"]

    if adder_name not in module_contents:
        raise SystemExit(
            f"ERROR: adder module '{adder_name}' not found. "
            f"Available modules: {module_names}"
        )

    if mult_name not in module_contents:
        raise SystemExit(
            f"ERROR: multiplier module '{mult_name}' not found. "
            f"Available modules: {module_names}"
        )

    if config.get("generate_top_wrapper", True):
        top_module = config["top_module"]
        if top_module not in module_contents:
            raise SystemExit(
                f"ERROR: top module '{top_module}' not found. "
                f"Available modules: {module_names}"
            )

    # ------------------------------------------------------
    # Read area information
    # ------------------------------------------------------
    lib_areas = get_cell_area_from_lib(config["lib_file"])
    lef_areas = get_cell_area_from_lef(config["lef_file"])

    cell_areas = merge_area_sources(lib_areas, lef_areas)

    print("\n=======================================================")
    print("AREA SOURCE SUMMARY")
    print("=======================================================")
    print(f"LIB areas: {len(lib_areas)}")
    print(f"LEF areas: {len(lef_areas)}")
    print(f"Merged areas: {len(cell_areas)}")

    # ------------------------------------------------------
    # Estimate area
    # ------------------------------------------------------
    adder_area = estimate_module_area(adder_name, cell_counts, cell_areas)
    mult_area = estimate_module_area(mult_name, cell_counts, cell_areas)

    total_area = adder_area + mult_area

    if total_area == 0:
        print("WARNING: total estimated area is 0. Using 50/50 split.")
        split_ratio = 0.5
    else:
        split_ratio = adder_area / total_area

    print("\n=======================================================")
    print("AREA ESTIMATION")
    print("=======================================================")
    print(f"{adder_name} area: {adder_area:.4f} um²")
    print(f"{mult_name} area: {mult_area:.4f} um²")
    print(f"Split ratio: {split_ratio:.4f}")
    print(f"{adder_name} gets {split_ratio * 100:.1f}%")
    print(f"{mult_name} gets {(1 - split_ratio) * 100:.1f}%")

    # ------------------------------------------------------
    # Floorplan regions
    # ------------------------------------------------------
    if config["manual_floorplan"]["enable"]:
        print("\nUsing MANUAL floorplan from config.")

        mf = config["manual_floorplan"]

        if adder_name not in mf:
            raise SystemExit(f"manual_floorplan missing region for {adder_name}")

        if mult_name not in mf:
            raise SystemExit(f"manual_floorplan missing region for {mult_name}")

        adder_region = mf[adder_name]
        mult_region = mf[mult_name]

    else:
        print("\nUsing AUTOMATIC area-based floorplan.")

        split_x = round(config["chip_width"] * split_ratio, 3)

        adder_region = {
            "llx_um": 0.0,
            "lly_um": 0.0,
            "urx_um": split_x,
            "ury_um": config["chip_height"]
        }

        mult_region = {
            "llx_um": split_x,
            "lly_um": 0.0,
            "urx_um": config["chip_width"],
            "ury_um": config["chip_height"]
        }

    validate_region(adder_name, adder_region, config)
    validate_region(mult_name, mult_region, config)

    if regions_overlap(adder_region, mult_region):
        print("WARNING: adder and multiplier regions overlap!")

    print("\n=======================================================")
    print("PARTITION REGIONS")
    print("=======================================================")
    print(f"{adder_name} region: {adder_region}")
    print(f"{mult_name} region: {mult_region}")

    # ------------------------------------------------------
    # Create output dirs
    # ------------------------------------------------------
    os.makedirs(config["output_dir"], exist_ok=True)

    adder_dir = os.path.join(config["output_dir"], "adder")
    mult_dir = os.path.join(config["output_dir"], "multiplier")

    os.makedirs(adder_dir, exist_ok=True)
    os.makedirs(mult_dir, exist_ok=True)

    # ------------------------------------------------------
    # Extract block Verilog files
    # ------------------------------------------------------
    adder_v = os.path.join(adder_dir, f"{adder_name}.v")
    mult_v = os.path.join(mult_dir, f"{mult_name}.v")

    extract_module_to_file(module_contents, adder_name, adder_v)
    extract_module_to_file(module_contents, mult_name, mult_v)

    # ------------------------------------------------------
    # Generate top wrapper
    # ------------------------------------------------------
    top_wrapper_v = None

    if config.get("generate_top_wrapper", True):
        top_wrapper_v = generate_top_wrapper(
            module_contents,
            config,
            config["output_dir"]
        )

    # ------------------------------------------------------
    # Generate OpenROAD TCL files
    # ------------------------------------------------------
    adder_tcl = generate_tcl(
        config,
        adder_name,
        adder_v,
        adder_dir,
        adder_region,
        mult_region
    )

    mult_tcl = generate_tcl(
        config,
        mult_name,
        mult_v,
        mult_dir,
        mult_region,
        adder_region
    )

    # ------------------------------------------------------
    # Save partition_info.json
    # ------------------------------------------------------
    partition_info = {
        "chip_dimensions": {
            "width_um": config["chip_width"],
            "height_um": config["chip_height"],
            "dbu_per_micron": config["dbu_per_micron"]
        },

        "modules": {
            "top": config["top_module"],
            "top_wrapper": config["top_wrapper_module"],
            "adder": adder_name,
            "multiplier": mult_name
        },

        "area_estimation": {
            "adder": {
                "module": adder_name,
                "cell_counts": cell_counts.get(adder_name, {}),
                "estimated_area_um2": adder_area
            },
            "multiplier": {
                "module": mult_name,
                "cell_counts": cell_counts.get(mult_name, {}),
                "estimated_area_um2": mult_area
            }
        },

        "partition": {
            "split_ratio": split_ratio,
            "split_direction": "vertical",
            "adder_region": adder_region,
            "multiplier_region": mult_region,
            "adder_blocked_region": mult_region,
            "multiplier_blocked_region": adder_region
        },

        "openroad": {
            "site": config["site"],
            "default_utilization": config["utilization"],
            "margin_um": config["margin"],
            "block_overrides": config.get("block_overrides", {})
        },

        "files": {
            "source_verilog": tcl_path(config["verilog_file"]),
            "adder_verilog": tcl_path(adder_v),
            "multiplier_verilog": tcl_path(mult_v),
            "top_wrapper_verilog": tcl_path(top_wrapper_v) if top_wrapper_v else None,
            "adder_tcl": tcl_path(adder_tcl),
            "multiplier_tcl": tcl_path(mult_tcl)
        }
    }

    json_path = os.path.join(config["output_dir"], "partition_info.json")

    with open(json_path, "w") as f:
        json.dump(partition_info, f, indent=2)

    # ------------------------------------------------------
    # Summary
    # ------------------------------------------------------
    print("\n=======================================================")
    print("SPLIT COMPLETE")
    print("=======================================================")
    print("Adder Verilog      :", adder_v)
    print("Multiplier Verilog :", mult_v)
    print("Top Wrapper        :", top_wrapper_v)
    print("Adder TCL          :", adder_tcl)
    print("Multiplier TCL     :", mult_tcl)
    print("Partition JSON     :", json_path)
    print("\nRun from project root:")
    print(f"  openroad {tcl_path(adder_tcl)}")
    print(f"  openroad {tcl_path(mult_tcl)}")
    print("=======================================================")


if __name__ == "__main__":
    # ======================================================
    # ARYA UPDATE V8:
    # Run with:
    # python scripts/split_net_v2_arya.py
    #
    # Or with custom config:
    # python scripts/split_net_v2_arya.py configs/config.json
    # ======================================================
    json_path = sys.argv[1] if len(sys.argv) > 1 else None
    config = load_config(json_path)
    split_design(config)