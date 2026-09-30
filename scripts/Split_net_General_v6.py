# ═══════════════════════════════════════════════════════════════════
#
#   split_net_v5.py
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
#   4. Supports automatic area-based floorplan (N-modules).
#   5. Supports manual floorplan from config.json.
#   6. Preserves base logic for separate block regions.
#   7. Generates OpenROAD TCL per block.
#   8. Fixes OpenROAD path issues by cd'ing to project root.
#   9. Disables unsupported create_blockage -bbox command.
#   10. Sayak_V5: Integrated flow_utils for path and config management.
#   11. sayak_V6: Generalized to support N-arbitrary modules and safely 
#       handles system primitives like $add, $sub, $mul.
#
#   Author  : Sayak Deb
#   Project : Digital Lab — Third Semester, Bremen
# ═══════════════════════════════════════════════════════════════════

import os
import re
import json
import sys
from pathlib import Path

from flow_utils import get_project_root, tcl_path, load_and_validate_config

PROJECT_ROOT = get_project_root()

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
    content = re.sub(r"//[^\n]*", "", content)
    content = re.sub(r"/\*.*?\*/", " ", content, flags=re.DOTALL)
    return content

def find_matching_paren(text, open_index):
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
    module_match = re.search(r"\bmodule\s+([A-Za-z_][A-Za-z0-9_$]*)", chunk)
    if not module_match:
        return None

    module_name = module_match.group(1)
    pos = module_match.end()

    while pos < len(chunk) and chunk[pos].isspace():
        pos += 1

    if pos < len(chunk) and chunk[pos] == "#":
        hash_pos = pos
        paren_pos = chunk.find("(", hash_pos)
        if paren_pos != -1:
            close_pos = find_matching_paren(chunk, paren_pos)
            if close_pos != -1:
                pos = close_pos + 1

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
    counts = {}
    pattern = re.compile(
        r"^\s*([^\s#();,]+)\s+"
        r"(?:#\s*$[^;]*?$\s*)?"
        r"([^\s(]+)\s*$",
        re.MULTILINE
    )

    for match in pattern.finditer(body):
        cell_type = match.group(1)
        if cell_type.lower() in SKIP_KEYWORDS or cell_type.startswith("`"):
            continue
        counts[cell_type] = counts.get(cell_type, 0) + 1

    return counts

def parse_verilog(verilog_file):
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
        module_contents[module_name] = {"ports": ports, "body": body}
        counts = count_cells(body)
        cell_counts_per_module[module_name] = counts

        print(f"Found module: {module_name}")

    print("\nModules found:", module_names)
    return module_names, module_contents, cell_counts_per_module


# ==========================================================
# LIB / LEF AREA PARSING
# ==========================================================

def get_cell_area_from_lib(lib_file):
    if not os.path.exists(lib_file):
        raise FileNotFoundError(f"LIB file not found: {lib_file}")

    with open(lib_file, "r") as f:
        content = f.read()

    content = re.sub(r"/\*.*?\*/", " ", content, flags=re.DOTALL)
    cell_areas = {}
    cells = list(re.finditer(r"\bcell\s*$\s*[\"\']?([A-Za-z_][A-Za-z0-9_]*)[\"\']?\s*$", content))

    for i, cell in enumerate(cells):
        name = cell.group(1)
        start = cell.end()
        end = cells[i + 1].start() if i + 1 < len(cells) else len(content)
        body = content[start:end]
        area_match = re.search(r"\barea\s*:\s*([0-9.eE+-]+)\s*;", body)
        if area_match:
            cell_areas[name] = float(area_match.group(1))

    return cell_areas

def get_cell_area_from_lef(lef_file):
    if not os.path.exists(lef_file):
        raise FileNotFoundError(f"LEF file not found: {lef_file}")

    with open(lef_file, "r") as f:
        content = f.read()

    content = re.sub(r"#.*", "", content)
    cell_areas = {}
    pattern = re.compile(
        r"\bMACRO\s+([A-Za-z_][A-Za-z0-9_]*)"
        r".*?\bSIZE\s+([0-9.eE+-]+)\s+BY\s+([0-9.eE+-]+)\s*;",
        re.DOTALL
    )

    for match in pattern.finditer(content):
        cell_areas[match.group(1)] = float(match.group(2)) * float(match.group(3))

    return cell_areas

def merge_area_sources(lib_areas, lef_areas):
    merged = dict(lib_areas)
    for cell, lef_area in lef_areas.items():
        if cell not in merged or merged[cell] <= 0:
            merged[cell] = lef_area
    return merged


# ==========================================================
# HIERARCHICAL AREA ESTIMATION
# ==========================================================

def estimate_module_area(
    module_name, cell_counts_per_module, cell_areas, module_stack=None, default_unknown_area=0.1
):
    if module_stack is None:
        module_stack = []

    if module_name in module_stack:
        return 0.0

    module_stack.append(module_name)
    counts = cell_counts_per_module.get(module_name, {})
    total = 0.0

    for inst_type, count in counts.items():
        if inst_type in cell_areas:
            total += count * cell_areas[inst_type]
        elif inst_type in cell_counts_per_module:
            sub_area = estimate_module_area(
                inst_type, cell_counts_per_module, cell_areas, module_stack[:], default_unknown_area
            )
            total += count * sub_area
        else:
            total += count * default_unknown_area

    return total * 1.3  # 30% routing overhead


# ==========================================================
# FLOORPLAN VALIDATION & UTILS
# ==========================================================

# sayak_V6: Safely converts module names like '$add' to 'sys_add' for file paths.
def sanitize_name(name):
    return name.replace("$", "sys_")

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
    if region["urx_um"] <= region["llx_um"] or region["ury_um"] <= region["lly_um"]:
        raise ValueError(f"Region for {name} has invalid dimensions: {region}")


# ==========================================================
# VERILOG OUTPUT GENERATION
# ==========================================================

def extract_module_to_file(module_contents, module_name, output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    mod = module_contents[module_name]

    with open(output_path, "w") as f:
        f.write("// Auto-extracted by split_net_v5.py\n")
        f.write(f"// Module: {module_name}\n\n")
        f.write(f"module {module_name} (\n")
        f.write(f"    {mod['ports']}\n")
        f.write(");\n\n")
        f.write(mod["body"])
        f.write("\nendmodule\n")

# sayak_V6: Dynamic wrapper checks all provided partitions instead of hardcoded 2 modules.
def generate_top_wrapper(module_contents, config, output_dir, partitions):
    top_module = config["top_module"]
    wrapper_module = config["top_wrapper_module"]

    for module in [top_module] + partitions:
        if module not in module_contents:
            raise ValueError(f"Module '{module}' not found for wrapper generation")

    wrapper_path = os.path.join(output_dir, "top_wrapper.v")
    os.makedirs(output_dir, exist_ok=True)

    top_ports = module_contents[top_module]["ports"]
    top_body = module_contents[top_module]["body"]

    with open(wrapper_path, "w") as f:
        f.write("// ======================================================\n")
        f.write("// Auto-generated top wrapper connecting partitions\n")
        f.write("// ======================================================\n\n")
        f.write(f"module {wrapper_module} (\n")
        f.write(f"    {top_ports}\n")
        f.write(");\n\n")
        f.write(top_body)
        f.write("\nendmodule\n")

    return wrapper_path


# ==========================================================
# TCL GENERATION
# ==========================================================

# sayak_V6: Takes a dictionary of multiple blocked regions rather than just one
def generate_tcl(config, block_name, verilog_path, output_dir, own_region, blocked_regions):
    safe_block_name = sanitize_name(block_name)
    reports_dir = os.path.join(output_dir, "reports")
    results_dir = os.path.join(output_dir, "results")

    os.makedirs(reports_dir, exist_ok=True)
    os.makedirs(results_dir, exist_ok=True)

    tcl_file_path = os.path.join(output_dir, f"{safe_block_name}_flow.tcl")

    tech_lef_tcl = tcl_path(config["tech_lef_file"])
    lef_tcl = tcl_path(config["lef_file"])
    lib_tcl = tcl_path(config["lib_file"])
    verilog_tcl = tcl_path(verilog_path)
    reports_tcl = tcl_path(reports_dir)
    results_tcl = tcl_path(results_dir)

    block_cfg = config.get("block_overrides", {}).get(block_name, {})
    placement_density = block_cfg.get("placement_density", config.get("utilization", 0.70))
    pin_hor_layer = block_cfg.get("pin_hor_layer", "metal3")
    pin_ver_layer = block_cfg.get("pin_ver_layer", "metal4")

    with open(tcl_file_path, "w") as f:
        f.write("# ======================================================\n")
        f.write(f"# Block: {block_name}\n")
        f.write("# ======================================================\n\n")

        f.write("set script_dir [file dirname [file normalize [info script]]]\n")
        f.write("set project_root [file normalize \"$script_dir/../..\"]\n")
        f.write("cd $project_root\n\n")

        f.write(f"read_lef     {tech_lef_tcl}\n")
        f.write(f"read_lef     {lef_tcl}\n")
        f.write(f"read_liberty {lib_tcl}\n\n")

        f.write(f"read_verilog {verilog_tcl}\n")
        
        # sayak_V6: Encapsulate link_design target in curly braces to prevent TCL 
        # from interpreting Verilog primitives like `$add` as variables.
        f.write(f"link_design  {{{block_name}}}\n\n")

        coordinate_mode = config.get("coordinate_mode", "global_partition")

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
            die_llx, die_lly = own_region["llx_um"], own_region["lly_um"]
            die_urx, die_ury = own_region["urx_um"], own_region["ury_um"]
            core_llx = own_region["llx_um"] + config["margin"]
            core_lly = own_region["lly_um"] + config["margin"]
            core_urx = own_region["urx_um"] - config["margin"]
            core_ury = own_region["ury_um"] - config["margin"]

        f.write("initialize_floorplan \\\n")
        f.write(f"  -die_area  \"{die_llx} {die_lly} {die_urx} {die_ury}\" \\\n")
        f.write(f"  -core_area \"{core_llx} {core_lly} {core_urx} {core_ury}\" \\\n")
        f.write(f"  -site      {config['site']}\n\n")

        f.write("# === Sibling blocked region information ===\n")
        # sayak_V6: Loop through multiple blocked regions
        for sib_name, s_reg in blocked_regions.items():
            safe_sib_name = sanitize_name(sib_name)
            f.write(f"# blocked_region ({sib_name}) = {s_reg['llx_um']} {s_reg['lly_um']} {s_reg['urx_um']} {s_reg['ury_um']}\n")
            f.write(f"# create_blockage -bbox {{{s_reg['llx_um']} {s_reg['lly_um']} {s_reg['urx_um']} {s_reg['ury_um']}}} "
                    f"-type placement -name blockage_{safe_block_name}_{safe_sib_name}\n")
        f.write("\n")

        f.write("make_tracks\n\n")
        f.write(f"place_pins -hor_layers {pin_hor_layer} -ver_layers {pin_ver_layer}\n\n")
        f.write(f"global_placement -density {placement_density}\n\n")
        f.write("detailed_placement\n")
        f.write("check_placement -verbose\n\n")
        f.write("filler_placement \"FILLCELL_X8 FILLCELL_X4 FILLCELL_X2 FILLCELL_X1\"\n\n")

        f.write("if {[catch {global_route -congestion_iterations 50} gr_result]} {\n")
        f.write("  global_route\n")
        f.write("}\n")
        f.write(f"detailed_route -output_drc {reports_tcl}/{safe_block_name}.drc\n\n")

        f.write("report_design_area\nreport_wns\nreport_tns\n\n")
        
        f.write(f"write_def {results_tcl}/{safe_block_name}_placed_routed.def\n\n")
        f.write("if {[info commands write_abstract_lef] != \"\"} {\n")
        f.write(f"  write_abstract_lef {results_tcl}/{safe_block_name}.lef\n")
        f.write("}\n")

    return tcl_file_path


# ==========================================================
# MAIN SPLIT FLOW
# ==========================================================

def split_design(config):
    for key in ["verilog_file", "lib_file", "tech_lef_file", "lef_file"]:
        if not os.path.exists(config[key]):
            raise FileNotFoundError(f"{key} not found: {config[key]}")

    module_names, module_contents, cell_counts = parse_verilog(config["verilog_file"])

    # sayak_V6: Read 'partitions' list instead of hardcoded adder/multiplier
    partitions = config.get("partitions", [])
    
    # Fallback to older config keys if "partitions" is not provided
    if not partitions:
        if "adder_module" in config and "multiplier_module" in config:
            partitions = [config["adder_module"], config["multiplier_module"]]
        else:
            raise ValueError("No 'partitions' list found in config.json")

    print("\n=======================================================")
    print("MODULE VERIFICATION")
    print("=======================================================")
    for p_name in partitions:
        if p_name not in module_contents:
            raise SystemExit(f"ERROR: Partition module '{p_name}' not found. Available: {module_names}")
        else:
            print(f"Verified partition module: {p_name}")

    if config.get("generate_top_wrapper", True):
        top_module = config["top_module"]
        if top_module not in module_contents:
            raise SystemExit(f"ERROR: top module '{top_module}' not found.")

    lib_areas = get_cell_area_from_lib(config["lib_file"])
    lef_areas = get_cell_area_from_lef(config["lef_file"])
    cell_areas = merge_area_sources(lib_areas, lef_areas)

    # sayak_V6: Dynamically estimate area for all partitions
    print("\n=======================================================")
    print("AREA ESTIMATION")
    print("=======================================================")
    partition_areas = {}
    for p_name in partitions:
        area = estimate_module_area(p_name, cell_counts, cell_areas)
        partition_areas[p_name] = area
        print(f"{p_name} area: {area:.4f} um²")

    total_area = sum(partition_areas.values())

    # sayak_V6: Dynamic floorplan generation for N modules
    partition_regions = {}
    
    if config.get("manual_floorplan", {}).get("enable"):
        print("\nUsing MANUAL floorplan from config.")
        mf = config["manual_floorplan"]
        for p_name in partitions:
            if p_name not in mf:
                raise SystemExit(f"manual_floorplan missing region for {p_name}")
            partition_regions[p_name] = mf[p_name]
    else:
        print("\nUsing AUTOMATIC 1D Area-based floorplan.")
        current_x = 0.0
        for p_name in partitions:
            ratio = partition_areas[p_name] / total_area if total_area > 0 else 1.0 / len(partitions)
            width = round(config["chip_width"] * ratio, 3)
            partition_regions[p_name] = {
                "llx_um": current_x,
                "lly_um": 0.0,
                "urx_um": current_x + width,
                "ury_um": config["chip_height"]
            }
            current_x += width

    print("\n=======================================================")
    print("PARTITION REGIONS")
    print("=======================================================")
    for p_name, region in partition_regions.items():
        validate_region(p_name, region, config)
        print(f"{p_name} region: {region}")

    # Check overlaps between all regions dynamically
    partitions_list = list(partition_regions.keys())
    for i in range(len(partitions_list)):
        for j in range(i + 1, len(partitions_list)):
            if regions_overlap(partition_regions[partitions_list[i]], partition_regions[partitions_list[j]]):
                print(f"WARNING: Regions {partitions_list[i]} and {partitions_list[j]} overlap!")

    os.makedirs(config["output_dir"], exist_ok=True)

    # sayak_V6: Iterate through dynamic partitions to create dirs, extract verliog, and make TCL
    verilog_files = {}
    tcl_files = {}

    for p_name in partitions:
        safe_p_name = sanitize_name(p_name)
        p_dir = os.path.join(config["output_dir"], safe_p_name)
        os.makedirs(p_dir, exist_ok=True)

        p_v = os.path.join(p_dir, f"{safe_p_name}.v")
        extract_module_to_file(module_contents, p_name, p_v)
        verilog_files[p_name] = p_v

        # Collect all OTHER regions to set as blockages
        blocked_regions = {name: reg for name, reg in partition_regions.items() if name != p_name}

        p_tcl = generate_tcl(config, p_name, p_v, p_dir, partition_regions[p_name], blocked_regions)
        tcl_files[p_name] = p_tcl

    top_wrapper_v = None
    if config.get("generate_top_wrapper", True):
        # sayak_V6: Passes the dynamic partitions list
        top_wrapper_v = generate_top_wrapper(module_contents, config, config["output_dir"], partitions)

    # sayak_V6: Dynamic JSON payload update
    partition_info = {
        "chip_dimensions": {
            "width_um": config["chip_width"],
            "height_um": config["chip_height"],
            "dbu_per_micron": config["dbu_per_micron"]
        },
        "modules": {
            "top": config["top_module"],
            "top_wrapper": config["top_wrapper_module"],
            "partitions": partitions
        },
        "area_estimation": {
            p: {
                "module": p,
                "cell_counts": cell_counts.get(p, {}),
                "estimated_area_um2": partition_areas[p]
            } for p in partitions
        },
        "partition_regions": partition_regions,
        "openroad": {
            "site": config["site"],
            "default_utilization": config["utilization"],
            "margin_um": config["margin"],
            "block_overrides": config.get("block_overrides", {})
        },
        "files": {
            "source_verilog": tcl_path(config["verilog_file"]),
            "top_wrapper_verilog": tcl_path(top_wrapper_v) if top_wrapper_v else None,
            "partition_verilog": {p: tcl_path(v) for p, v in verilog_files.items()},
            "partition_tcl": {p: tcl_path(t) for p, t in tcl_files.items()}
        }
    }

    json_path = os.path.join(config["output_dir"], "partition_info.json")
    with open(json_path, "w") as f:
        json.dump(partition_info, f, indent=2)

    print("\n=======================================================")
    print("SPLIT COMPLETE")
    print("=======================================================")
    print("Top Wrapper        :", top_wrapper_v)
    for p in partitions:
        print(f"[{p}] Verilog: {verilog_files[p]}")
        print(f"[{p}] TCL    : {tcl_files[p]}")
    print("Partition JSON     :", json_path)
    
    print("\nRun from project root:")
    for p in partitions:
        print(f"  openroad {tcl_path(tcl_files[p])}")
    print("=======================================================")


if __name__ == "__main__":
    json_path = sys.argv[1] if len(sys.argv) > 1 else "configs/config.json"
    
    config = load_and_validate_config(json_path)
    
    for key in ["output_dir", "verilog_file", "lib_file", "tech_lef_file", "lef_file"]:
        if not Path(config[key]).is_absolute():
            config[key] = str(PROJECT_ROOT / config[key])
            
    split_design(config)