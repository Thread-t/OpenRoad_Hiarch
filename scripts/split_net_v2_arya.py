# ═══════════════════════════════════════════════════════════════════
#
#   split_net_v2_arya.py
#   ────────────────────────────────────────────────────────────────
#   Netlist Partitioning & OpenROAD Floorplan Generator
#
#   Based on:
#   split_net_v2_sayak.py
#
#   Purpose:
#   Parses a synthesized Nangate gate-level Verilog netlist, splits it
#   into adder and multiplier blocks, estimates area using Nangate
#   .lib/.lef files, supports manual floorplan regions from config.json,
#   and generates OpenROAD TCL scripts.
#
#   ARYA UPDATE SUMMARY:
#   1. Added project-root based path handling.
#   2. Default config file is now configs/config.json.
#   3. Input files are read from inputs/.
#   4. Generated files are written to generated/.
#   5. TCL files now use Linux/WSL-friendly relative paths instead of
#      Windows absolute paths.
#   6. Every changed section is marked with ARYA UPDATE comments.\n#   7. ARYA UPDATE V9: Disabled create_blockage because this OpenROAD version does not support create_blockage -bbox.
#
#   Project folder expected:
#
#   Hierarchical_OpenROAD_Framework/
#   ├── inputs/
#   │   ├── top_design_gate.v
#   │   ├── NangateOpenCellLibrary_typical.lib
#   │   ├── NangateOpenCellLibrary.tech.lef
#   │   └── NangateOpenCellLibrary.macro.mod.lef
#   ├── configs/
#   │   └── config.json
#   ├── scripts/
#   │   └── split_net_v2_arya.py
#   └── generated/
#
# ═══════════════════════════════════════════════════════════════════

import os
import re
import json
import sys


# ==========================================================
# ARYA UPDATE V1:
# Added project-root path handling.
# This avoids hardcoded Windows/Linux paths and makes the
# script portable for all team members.
# ==========================================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
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


DEFAULT_CONFIG = {
    "chip_width": 200.0,
    "chip_height": 200.0,
    "dbu_per_micron": 1000,
    "aspect_ratio": 1.0,
    "utilization": 0.70,
    "margin": 3.0,
    "site": "FreePDK45_38x28_10R_NP_162NW_34O",

    # ======================================================
    # ARYA UPDATE V2:
    # Updated default paths to match our common team folder:
    # inputs/ and generated/.
    # ======================================================
    "output_dir": "generated",
    "verilog_file": "inputs/top_design_gate.v",
    "lib_file": "inputs/NangateOpenCellLibrary_typical.lib",
    "tech_lef_file": "inputs/NangateOpenCellLibrary.tech.lef",
    "lef_file": "inputs/NangateOpenCellLibrary.macro.mod.lef",

    "adder_module": "adder_32",
    "multiplier_module": "multiplier_32",

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
    }
}


# ==========================================================
# ARYA UPDATE V3:
# Default config is now loaded from configs/config.json.
# User can still pass another config path in command line.
# ==========================================================
def load_config(json_path=None):
    config = json.loads(json.dumps(DEFAULT_CONFIG))

    if json_path is None:
        json_path = project_path("configs/config.json")
    else:
        json_path = project_path(json_path)

    if os.path.exists(json_path):
        print("Loading config:", json_path)
        with open(json_path, "r") as f:
            user_config = json.load(f)

        for key, value in user_config.items():
            if isinstance(value, dict) and key in config and isinstance(config[key], dict):
                config[key].update(value)
            else:
                config[key] = value
    else:
        print("No config file found. Using default config.")

    # ======================================================
    # ARYA UPDATE V4:
    # Convert all important paths to absolute paths internally.
    # This helps Python find files correctly on Windows/WSL.
    # TCL output will still be converted back to relative paths.
    # ======================================================
    for key in ["verilog_file", "lib_file", "tech_lef_file", "lef_file", "output_dir"]:
        config[key] = project_path(config[key])

    return config


SKIP_KEYWORDS = {
    "module", "endmodule", "input", "output", "inout",
    "wire", "reg", "logic", "assign", "always", "begin",
    "end", "if", "else", "case", "endcase", "generate",
    "endgenerate", "for", "genvar", "parameter", "localparam",
    "function", "task", "initial", "posedge", "negedge",
    "integer", "signed", "unsigned", "default"
}


def clean_verilog(content):
    """Remove single-line and multi-line Verilog comments."""
    content = re.sub(r"//[^\n]*\n", "\n", content)
    content = re.sub(r"/\*.*?\*/", " ", content, flags=re.DOTALL)
    return content


def count_cells(body):
    """Count standard-cell instances inside a module body."""
    counts = {}
    pattern = re.compile(
        r"^\s*([A-Za-z_][A-Za-z0-9_$]*)\s+"
        r"([A-Za-z_][A-Za-z0-9_$\[\]]*)\s*\(",
        re.MULTILINE
    )

    for match in pattern.finditer(body):
        cell_type = match.group(1)
        if cell_type.lower() not in SKIP_KEYWORDS:
            counts[cell_type] = counts.get(cell_type, 0) + 1

    return counts


def parse_verilog(verilog_file):
    """Parse gate-level Verilog and extract module contents."""
    print("\n=======================================================")
    print("PARSING VERILOG:", verilog_file)
    print("=======================================================")

    if not os.path.exists(verilog_file):
        raise FileNotFoundError("Verilog file not found: " + verilog_file)

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

        header = re.search(
            r"\bmodule\s+([A-Za-z_][A-Za-z0-9_$]*)\s*"
            r"(?:#\s*\([^)]*\))?\s*\((.*?)\)\s*;",
            chunk,
            re.DOTALL
        )

        if not header:
            header = re.search(r"\bmodule\s+([A-Za-z_][A-Za-z0-9_$]*)", chunk)
            if not header:
                continue
            module_name = header.group(1)
            ports = ""
            body_start = header.end()
        else:
            module_name = header.group(1)
            ports = header.group(2).strip()
            body_start = header.end()

        body = chunk[body_start:].strip()

        module_names.append(module_name)
        module_contents[module_name] = {
            "ports": ports,
            "body": body
        }

        cell_counts_per_module[module_name] = count_cells(body)

        print("Found module:", module_name)
        if cell_counts_per_module[module_name]:
            print("  Cell counts:", cell_counts_per_module[module_name])
        else:
            print("  No standard cells found")

    return module_names, module_contents, cell_counts_per_module


def get_cell_area_from_lib(lib_file):
    """Extract cell area from Liberty file."""
    print("\nReading LIB:", lib_file)

    if not os.path.exists(lib_file):
        raise FileNotFoundError("LIB file not found: " + lib_file)

    with open(lib_file, "r") as f:
        content = f.read()

    content = re.sub(r"/\*.*?\*/", " ", content, flags=re.DOTALL)

    cell_areas = {}
    cells = list(re.finditer(
        r"\bcell\s*\(\s*[\"\']?([A-Za-z_][A-Za-z0-9_]*)[\"\']?\s*\)",
        content
    ))

    for i, cell in enumerate(cells):
        name = cell.group(1)
        start = cell.end()
        end = cells[i + 1].start() if i + 1 < len(cells) else len(content)
        body = content[start:end]

        area_match = re.search(r"\barea\s*:\s*([\d.]+)\s*;", body)
        if area_match:
            cell_areas[name] = float(area_match.group(1))

    print("Cell areas from LIB:", len(cell_areas))
    return cell_areas


def get_cell_area_from_lef(lef_file):
    """Fallback: extract cell area from LEF SIZE statements."""
    print("\nReading LEF:", lef_file)

    if not os.path.exists(lef_file):
        raise FileNotFoundError("LEF file not found: " + lef_file)

    with open(lef_file, "r") as f:
        content = f.read()

    cell_areas = {}
    pattern = re.compile(
        r"MACRO\s+([A-Za-z_][A-Za-z0-9_]*)"
        r".*?SIZE\s+([\d.]+)\s+BY\s+([\d.]+)",
        re.DOTALL
    )

    for match in pattern.finditer(content):
        name = match.group(1)
        width = float(match.group(2))
        height = float(match.group(3))
        cell_areas[name] = width * height

    print("Cell areas from LEF:", len(cell_areas))
    return cell_areas


def calculate_area(cell_counts, cell_areas, default=0.1):
    """
    Area estimate = sum(cell_count * cell_area) + 30% routing overhead.
    This is used only for automatic partition region estimation.
    """
    area = 0.0
    for cell, count in cell_counts.items():
        area += count * cell_areas.get(cell, default)
    return area * 1.3


def extract_module_to_file(module_contents, module_name, output_path):
    """Write one module into a separate Verilog file."""
    if module_name not in module_contents:
        raise ValueError(f"Module {module_name} not found")

    mod = module_contents[module_name]

    with open(output_path, "w") as f:
        f.write("// Auto-extracted by split_net_v2_arya.py\n")
        f.write(f"// Module: {module_name}\n\n")
        f.write(f"module {module_name} (\n")
        f.write("    " + mod["ports"] + "\n")
        f.write(");\n\n")
        f.write(mod["body"])
        f.write("\nendmodule\n")

    print("Generated Verilog:", output_path)


def generate_tcl(config, block_name, verilog_path, output_dir, own_region, blocked_region):
    """Generate OpenROAD TCL script for one partition."""
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

    with open(tcl_file_path, "w") as f:
        f.write("# OpenROAD TCL generated by split_net_v2_arya.py\n")
        f.write(f"# Block: {block_name}\n")
        f.write("# ARYA UPDATE V7: Uses project-relative Linux-friendly paths.\n\n")

        f.write("# Read Nangate technology files\n")
        f.write(f"read_lef     {tech_lef_tcl}\n")
        f.write(f"read_lef     {lef_tcl}\n")
        f.write(f"read_liberty {lib_tcl}\n\n")

        f.write("# Read gate-level netlist\n")
        f.write(f"read_verilog {verilog_tcl}\n")
        f.write(f"link_design  {block_name}\n\n")

        f.write("# Floorplan region for this block\n")
        f.write("initialize_floorplan \\\n")
        f.write(
            f"  -die_area  \"{own_region['llx_um']} {own_region['lly_um']} "
            f"{own_region['urx_um']} {own_region['ury_um']}\" \\\n"
        )
        f.write(
            f"  -core_area \"{own_region['llx_um'] + config['margin']} "
            f"{own_region['lly_um'] + config['margin']} "
            f"{own_region['urx_um'] - config['margin']} "
            f"{own_region['ury_um'] - config['margin']}\" \\\n"
        )
        f.write(f"  -site      {config['site']}\n\n")

        # ======================================================
        # ARYA UPDATE V9:
        # Disabled create_blockage because this OpenROAD version
        # does not support the command:
        # create_blockage -bbox ...
        #
        # The floorplan region is still controlled by:
        # initialize_floorplan -die_area and -core_area.
        # ======================================================
        f.write("# Blockage command disabled: unsupported in this OpenROAD version\n")
        f.write(
            f"# create_blockage -bbox {{{blocked_region['llx_um']} {blocked_region['lly_um']} "
            f"{blocked_region['urx_um']} {blocked_region['ury_um']}}} "
            f"-type placement -name blockage_{block_name}\n\n"
        )

        f.write("make_tracks\n")
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
        f.write("place_pins -hor_layers metal3 -ver_layers metal4\n")
        f.write(f"global_placement -density {config['utilization']}\n")
        f.write("detailed_placement\n")
        f.write("check_placement -verbose\n\n")

        f.write("filler_placement \"FILLCELL_X8 FILLCELL_X4 FILLCELL_X2 FILLCELL_X1\"\n")
        f.write("global_route\n")
        f.write(f"detailed_route -output_drc {reports_tcl}/{block_name}.drc\n\n")

        f.write("report_design_area\n")
        f.write("report_wns\n")
        f.write("report_tns\n\n")

        f.write(f"write_def {results_tcl}/{block_name}_placed_routed.def\n")

    print("Generated TCL:", tcl_file_path)
    return tcl_file_path


def split_design(config):
    module_names, module_contents, cell_counts = parse_verilog(config["verilog_file"])

    adder_name = config["adder_module"]
    mult_name = config["multiplier_module"]

    if adder_name not in module_contents:
        raise SystemExit(f"Adder module {adder_name} not found")
    if mult_name not in module_contents:
        raise SystemExit(f"Multiplier module {mult_name} not found")

    cell_areas = get_cell_area_from_lib(config["lib_file"])
    if not cell_areas:
        cell_areas = get_cell_area_from_lef(config["lef_file"])

    adder_area = calculate_area(cell_counts.get(adder_name, {}), cell_areas)
    mult_area = calculate_area(cell_counts.get(mult_name, {}), cell_areas)
    total_area = adder_area + mult_area

    split_ratio = 0.5 if total_area == 0 else adder_area / total_area

    print("\nArea estimate:")
    print("  Adder:", adder_area, "um²")
    print("  Multiplier:", mult_area, "um²")
    print("  Split ratio:", split_ratio)

    if config["manual_floorplan"]["enable"]:
        print("\nUsing manual floorplan from config.json")
        adder_region = config["manual_floorplan"][adder_name]
        mult_region = config["manual_floorplan"][mult_name]
    else:
        print("\nUsing automatic area-based floorplan")
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

    print("Adder region:", adder_region)
    print("Multiplier region:", mult_region)

    os.makedirs(config["output_dir"], exist_ok=True)

    adder_dir = os.path.join(config["output_dir"], "adder")
    mult_dir = os.path.join(config["output_dir"], "multiplier")
    os.makedirs(adder_dir, exist_ok=True)
    os.makedirs(mult_dir, exist_ok=True)

    adder_v = os.path.join(adder_dir, "adder.v")
    mult_v = os.path.join(mult_dir, "multiplier.v")

    extract_module_to_file(module_contents, adder_name, adder_v)
    extract_module_to_file(module_contents, mult_name, mult_v)

    adder_tcl = generate_tcl(config, adder_name, adder_v, adder_dir, adder_region, mult_region)
    mult_tcl = generate_tcl(config, mult_name, mult_v, mult_dir, mult_region, adder_region)

    partition_info = {
        "chip_dimensions": {
            "width_um": config["chip_width"],
            "height_um": config["chip_height"],
            "dbu_per_micron": config["dbu_per_micron"]
        },
        "modules": {
            "adder": adder_name,
            "multiplier": mult_name
        },
        "area_estimation": {
            "adder": {
                "cell_counts": cell_counts.get(adder_name, {}),
                "estimated_area_um2": adder_area
            },
            "multiplier": {
                "cell_counts": cell_counts.get(mult_name, {}),
                "estimated_area_um2": mult_area
            }
        },
        "partition": {
            "split_ratio": split_ratio,
            "split_direction": "vertical",
            "adder_region": adder_region,
            "multiplier_region": mult_region
        },
        "files": {
            "adder_verilog": tcl_path(adder_v),
            "mult_verilog": tcl_path(mult_v),
            "adder_tcl": tcl_path(adder_tcl),
            "mult_tcl": tcl_path(mult_tcl)
        }
    }

    json_path = os.path.join(config["output_dir"], "partition_info.json")
    with open(json_path, "w") as f:
        json.dump(partition_info, f, indent=2)

    print("\nSPLIT COMPLETE")
    print("Adder Verilog:", adder_v)
    print("Multiplier Verilog:", mult_v)
    print("Adder TCL:", adder_tcl)
    print("Multiplier TCL:", mult_tcl)
    print("Partition JSON:", json_path)


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
