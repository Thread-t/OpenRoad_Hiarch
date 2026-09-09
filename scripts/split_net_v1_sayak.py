
# ═══════════════════════════════════════════════════════════════════
#
#   split_net.py
#   ────────────────────────────────────────────────────────────────
#   Netlist Partitioning & OpenROAD Floorplan Generator
#
#   Parses a synthesized gate-level Verilog netlist, splits it into
#   an adder block and a multiplier block, estimates each block's
#   physical area from the Nangate .lib/.lef cell library, and
#   auto-generates per-block OpenROAD TCL flow scripts with correct
#   floorplan regions and placement blockages — supporting both
#   automatic area-based splitting and manual user-defined floorplans
#   (via config.json).
#
#   Author  : Sayak Deb
#   Project : Digital Lab — Third Semester, Bremen
#   Tools   : Python 3, OpenROAD, Yosys, Nangate45 Open Cell Library
#
# ─────────────────────────────────────────────────────────────
import re
import json
import os

# ─────────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────────
#CONFIG = {
#   "chip_width"        : 200.0,
#    "chip_height"       : 200.0,
#    "dbu_per_micron"    : 1000,
#    "aspect_ratio"      : 1.0,
#    "utilization"       : 0.70,
#    "margin"            : 3.0,
#    "site"              : "FreePDK45_38x28_10R_NP_162NW_34O",
#    "output_dir"        : "results",
#    "verilog_file"      : "top_design_gate.v",
#    "lib_file"          : "NangateOpenCellLibrary_typical.lib",
#    "tech_lef_file"     : "NangateOpenCellLibrary.tech.lef",
#    "lef_file"          : "NangateOpenCellLibrary.macro.mod.lef",
#    "adder_module"      : "adder_32",
#    "multiplier_module" : "multiplier_32"
#} 
# ─────────────────────────────────────────────────────────────

DEFAULT_CONFIG = {
    "chip_width"        : 200.0,
    "chip_height"       : 200.0,
    "dbu_per_micron"    : 1000,
    "aspect_ratio"      : 1.0,
    "utilization"       : 0.70,
    "margin"            : 3.0,
    "site"              : "FreePDK45_38x28_10R_NP_162NW_34O",
    "output_dir"        : "results",
    "verilog_file"      : "top_design_gate.v",
    "lib_file"          : "NangateOpenCellLibrary_typical.lib",
    "tech_lef_file"     : "NangateOpenCellLibrary.tech.lef",
    "lef_file"          : "NangateOpenCellLibrary.macro.mod.lef",
    "adder_module"      : "adder_32",
    "multiplier_module" : "multiplier_32",

    "manual_floorplan": {
        "enable": False,
        "adder_32": {
            "llx_um": 0.0,   "lly_um": 0.0,
            "urx_um": 140.0, "ury_um": 200.0
        },
        "multiplier_32": {
            "llx_um": 140.0, "lly_um": 0.0,
            "urx_um": 200.0, "ury_um": 200.0
        }
    }
}

def load_config(json_path="config.json"):
    """Load user config from JSON and merge it onto the defaults."""
    config = json.loads(json.dumps(DEFAULT_CONFIG))  # deep copy
    if os.path.exists(json_path):
        print(f"  📄 Loading user config from: {json_path}")
        with open(json_path) as f:
            user_config = json.load(f)
        for key, value in user_config.items():
            if isinstance(value, dict) and key in config and isinstance(config[key], dict):
                config[key].update(value)   # shallow-merge nested dicts (e.g. manual_floorplan)
            else:
                config[key] = value
    else:
        print(f"  No {json_path} found — using built-in defaults")
    return config

# Keywords that are NOT cell instances
SKIP_KEYWORDS = {
    'module', 'endmodule', 'input', 'output', 'inout',
    'wire', 'reg', 'logic', 'assign', 'always', 'begin',
    'end', 'if', 'else', 'case', 'endcase', 'generate',
    'endgenerate', 'for', 'genvar', 'parameter', 'localparam',
    'function', 'task', 'initial', 'posedge', 'negedge',
    'integer', 'signed', 'unsigned', 'default', 'forever',
    'begin', 'end', 'wire', 'reg', 'logic', 'assign',
    'genvar', 'generate', 'endgenerate'
}

# ─────────────────────────────────────────────────────────────
# STEP 1: CLEAN VERILOG (remove comments)
# ─────────────────────────────────────────────────────────────
def clean_verilog(content):
    """Remove ALL comments from Verilog"""
    # Remove single line comments: // ...
    content = re.sub(r'//[^\n]*\n', '\n', content)
    # Remove multi-line comments: /* ... */
    content = re.sub(r'/\*.*?\*/', ' ', content, flags=re.DOTALL)
    return content

# ─────────────────────────────────────────────────────────────
# STEP 2: PARSE VERILOG
# ─────────────────────────────────────────────────────────────
def parse_verilog(verilog_file):
    """Parse Verilog by splitting on endmodule"""
    print(f"\n{'='*55}")
    print(f"  PARSING VERILOG: {verilog_file}")
    print(f"{'='*55}")

    with open(verilog_file, 'r') as f:
        raw = f.read()

    clean = clean_verilog(raw)

    print(f"  Raw size   : {len(raw)} chars")
    print(f"  Clean size : {len(clean)} chars")

    # ── Split into chunks by endmodule ──
    chunks = re.split(r'\bendmodule\b', clean)

    print(f"  Chunks found (= number of modules): {len(chunks)-1}")

    module_names    = []
    module_contents = {}
    cell_counts_per_module = {}

    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue

        # Find 'module NAME (' inside this chunk
        mod_header = re.search(
            r'\bmodule\s+([A-Za-z_][A-Za-z0-9_$]*)\s*'
            r'(?:#\s*$[^)]*$)?\s*$([^;]*)$\s*;',  # Match module name and ports
            chunk,
            re.DOTALL
        )

        if not mod_header:
            # Try simpler pattern
            mod_header = re.search(
                r'\bmodule\s+([A-Za-z_][A-Za-z0-9_$]*)', # Match module name only
                chunk
            )
            if not mod_header:
                continue
            mod_name = mod_header.group(1)
            mod_ports = ""
            body_start = mod_header.end()
        else:
            mod_name  = mod_header.group(1)
            mod_ports = mod_header.group(2).strip()
            body_start = mod_header.end()

        # Everything after port list = body
        mod_body = chunk[body_start:].strip()

        print(f"\n  📦 Found module: '{mod_name}'")
        print(f"     Ports (first 80): {mod_ports[:80]}")
        print(f"     Body  (first 80): {mod_body[:80]}")

        module_names.append(mod_name)
        module_contents[mod_name] = {
            "ports": mod_ports,
            "body" : mod_body,
            "raw_chunk": chunk
        }

        # ── Count cell instances in body ──
        cell_counts = count_cells(mod_body)
        cell_counts_per_module[mod_name] = cell_counts

        if cell_counts:
            print(f"     Cells:")
            for cname, cnt in cell_counts.items():
                print(f"       {cname:25s} × {cnt}")
        else:
            print(f"     No standard cell instances found")

    print(f"\n  ── Summary ──")
    print(f"  Modules found: {module_names}")

    return module_names, module_contents, cell_counts_per_module

# ─────────────────────────────────────────────────────────────
# HELPER: Count Cells in Module Body
# ─────────────────────────────────────────────────────────────
def count_cells(body):
    """
    Count standard cell instances in module body.
    Pattern: CELLNAME INSTANCENAME (
    e.g.  full_adder fa0 (.a(a[0]), ...)
    """
    cell_counts = {}

    # Pattern: word (
    # This matches: full_adder fa0 (
    pattern = re.compile(
        r'^\s*([A-Za-z_][A-Za-z0-9_$]*)\s+'
        r'([A-Za-z_][A-Za-z0-9_$\[\]]*)\s*\(',
        re.MULTILINE
    )

    for m in pattern.finditer(body):
        cell_type = m.group(1)
        inst_name = m.group(2)
        
        # Skip keywords
        if cell_type.lower() not in SKIP_KEYWORDS:
            cell_counts[cell_type] = cell_counts.get(cell_type, 0) + 1

    return cell_counts

# ─────────────────────────────────────────────────────────────
# STEP 3: READ LIB FILE
# ─────────────────────────────────────────────────────────────
def get_cell_area_from_lib(lib_file):
    """Read LIB file for cell areas"""
    print(f"\n{'='*55}")
    print(f"  READING LIB: {lib_file}")
    print(f"{'='*55}")

    cell_areas = {}

    with open(lib_file, 'r') as f:
        content = f.read()

    # Remove comments first (/* ... */)
    content = re.sub(r'/\*.*?\*/', ' ', content, flags=re.DOTALL)

    # Find cell blocks - pattern: cell ( "CELLNAME" ) { ... }
    # so it will fetch patterns like this in gate level netlist INV_X1 _133_ (NAND2_X1 _144_ (
    cell_starts = []
    for m in re.finditer(
        r'\bcell\s*\(\s*["\']?([A-Za-z_][A-Za-z0-9_]*)["\']?\s*\)',  # (cell_name, position_in_file)
        content
    ):
        cell_starts.append((m.group(1), m.end()))

    print(f"  Found {len(cell_starts)} cell definitions")

    for i, (cname, start) in enumerate(cell_starts):

        end = cell_starts[i+1][1] if i+1 < len(cell_starts) else len(content)
        body = content[start:end]

        # Find area - pattern: area : VALUE ;
        area_m = re.search(r'\barea\s*:\s*([\d.]+)\s*;', body)
        if area_m:
            area = float(area_m.group(1))
            cell_areas[cname] = area
            print(f"  {cname:25s} → {area:.6f} um²")
        else:
            # Try alternative: area : VALUE ;
            area_m = re.search(r'area\s*:\s*([\d.]+)', body)
            if area_m:
                area = float(area_m.group(1))
                cell_areas[cname] = area
                print(f"  {cname:25s} → {area:.6f} um² (alt)")

    if not cell_areas:
        print(f"  No areas found in LIB!")
        print(f"  → Using LEF file for area (SIZE W BY H)")

    return cell_areas

# ─────────────────────────────────────────────────────────────
# STEP 4: READ LEF FILE (Backup for Area)
# ─────────────────────────────────────────────────────────────
def get_cell_area_from_lef(lef_file):
    """Read LEF file for cell areas (SIZE W BY H)"""
    print(f"\n{'='*55}")
    print(f"  READING LEF: {lef_file}")
    print(f"{'='*55}")

    cell_areas = {}

    with open(lef_file, 'r') as f:
        content = f.read()

    # Remove comments first (# ...)
    content = re.sub(r'#.*?\n', '\n', content)

    # Pattern: MACRO CELLNAME ... SIZE W BY H
    macro_pattern = re.compile(
        r'MACRO\s+([A-Za-z_][A-Za-z0-9_]*)'
        r'.*?SIZE\s+([\d.]+)\s+BY\s+([\d.]+)',
        re.DOTALL
    )

    matches = list(macro_pattern.finditer(content))
    print(f"  Found {len(matches)} MACRO definitions")

    for m in matches:
        cell_name = m.group(1)
        width     = float(m.group(2))
        height    = float(m.group(3))
        area      = width * height
        cell_areas[cell_name] = area
        print(f"  {cell_name:25s} → {width:.3f} × {height:.3f}"
              f" = {area:.6f} um²")

    if not cell_areas:
        print(f"   No MACRO SIZE found in LEF!")
        print(f"  → Will use default area = 0.1 um²")

    return cell_areas

# ─────────────────────────────────────────────────────────────
# STEP 5: CALCULATE MODULE AREA
# For each cell type in the module, it looks up that cell's area from the .lib-derived dictionary (falling back to a default of 0.1 µm² 
# for any unrecognized cell type — shouldn't happen once the LIB parse works: refer the function get_cell_area_from_lef()), multiplies by how many instances the module has, and sums it all. 
# Then it inflates the raw cell area by 30% as a rough allowance for routing/interconnect overhead — real chip area is always bigger than the sum of 
# gate footprints because of wiring and spacing.
#
# For your adder: Σ(count × area) = 193.914 µm² → × 1.3 = 252.09 µm². 
# Same for multiplier: 63 × 1.064 = 67.03 µm² → × 1.3 = 87.14 µm².
# ─────────────────────────────────────────────────────────────
def calculate_area(cell_counts, cell_areas, default=0.1):
    """Total area = Σ (count × area) + 30% routing overhead"""
    total = 0.0
    for cell, count in cell_counts.items():
        total += count * cell_areas.get(cell, default)
    return total * 1.3  # +30% routing overhead

# ─────────────────────────────────────────────────────────────
# STEP 6: EXTRACT MODULE TO FILE
# ─────────────────────────────────────────────────────────────
def extract_module_to_file(module_contents, module_name,
                            output_path):
    """Write a single module to a .v file"""

    print(f"  Extracting '{module_name}'...")

    if module_name not in module_contents:
        print(f"\n  '{module_name}' not found!")
        print(f"  Available: {list(module_contents.keys())}")
        raise ValueError(f"Module '{module_name}' not found")

    mod   = module_contents[module_name]
    ports = mod["ports"]
    body  = mod["body"]

    with open(output_path, 'w') as f:
        f.write(f"// Auto-extracted by split_net.py\n")
        f.write(f"// Module: {module_name}\n\n")
        f.write(f"module {module_name} (\n")
        f.write(f"    {ports}\n")
        f.write(f");\n\n")
        f.write(body)
        f.write(f"\nendmodule\n")

    print(f"  Written → {output_path}")

# ─────────────────────────────────────────────────────────────
# STEP 7: GENERATE TCL SCRIPT
# ─────────────────────────────────────────────────────────────
def generate_tcl(config, block_name, verilog_path, output_dir, own_region, blocked_region):
    """Generate OpenROAD TCL script"""

    os.makedirs(os.path.join(output_dir, "reports"), exist_ok=True)
    os.makedirs(os.path.join(output_dir, "results"),  exist_ok=True)

    tcl_path = os.path.join(output_dir, f"{block_name}_flow.tcl")

    # Get absolute path for verilog
    verilog_abs = os.path.abspath(verilog_path)

    with open(tcl_path, 'w') as f:
        f.write(f"# ─────────────────────────────────────────────\n")
        f.write(f"# OpenROAD TCL Script Made by Sayak\n")
        f.write(f"# Block    : {block_name}\n")
        f.write(f"# Generated: by split_net.py\n")
        f.write(f"# ─────────────────────────────────────────────\n\n")

        f.write(f"# === Read technology files ===\n")
        f.write(f"read_lef     {os.path.abspath(config['tech_lef_file'])}\n")
        f.write(f"read_lef     {os.path.abspath(config['lef_file'])}\n")
        f.write(f"read_liberty {os.path.abspath(config['lib_file'])}\n\n")

        f.write(f"# === Read gate-level netlist ===\n")
        f.write(f"read_verilog {verilog_abs}\n")
        f.write(f"link_design  {block_name}\n\n")

        f.write(f"# === Floorplan (block's actual chip-coordinate region) ===\n")
        f.write(f"initialize_floorplan \\\n")
        f.write(f"  -die_area  \"{own_region['llx_um']} {own_region['lly_um']} "
                f"{own_region['urx_um']} {own_region['ury_um']}\" \\\n")
        f.write(f"  -core_area \"{own_region['llx_um']+config['margin']} "
                f"{own_region['lly_um']+config['margin']} "
                f"{own_region['urx_um']-config['margin']} "
                f"{own_region['ury_um']-config['margin']}\" \\\n")
        f.write(f"  -site      {config['site']}\n\n")

        f.write(f"# === Block sibling region (cannot be placed into) ===\n")
        f.write(f"create_blockage -bbox {{{blocked_region['llx_um']} {blocked_region['lly_um']} "
                f"{blocked_region['urx_um']} {blocked_region['ury_um']}}} "
                f"-type placement -name blockage_{block_name}\n\n")

        f.write(f"# === Initialize routing tracks ===\n")
        f.write(f"make_tracks\n\n")

        f.write(f"# === Pin placement ===\n")
        f.write(f"place_pins -hor_layers metal1 -ver_layers metal2\n\n")

        f.write(f"# === Global placement ===\n")
        f.write(f"global_placement -density {config['utilization']}\n\n")

        f.write(f"# === Detailed placement ===\n")
        f.write(f"detailed_placement\n")
        f.write(f"check_placement -verbose\n\n")

        f.write(f"# === Filler cells ===\n")
        f.write(f"filler_placement "
                f"\"FILLCELL_X8 FILLCELL_X4 "
                f"FILLCELL_X2 FILLCELL_X1\"\n\n")

        f.write(f"# === Route ===\n")
        f.write(f"global_route\n")
        f.write(f"detailed_route "
                f"-output_drc reports/{block_name}.drc\n\n")

        f.write(f"# === Reports ===\n")
        f.write(f"report_design_area\n")
        f.write(f"report_wns\n")
        f.write(f"report_tns\n\n")

        f.write(f"# === Export layout ===\n")
        f.write(f"write_def results/{block_name}_placed_routed.def\n")

    print(f"  TCL → {tcl_path}")
    return tcl_path

# ─────────────────────────────────────────────────────────────
# MAIN FUNCTION
# ─────────────────────────────────────────────────────────────
def split_design(config):

    # ── 1. Parse ──
    module_names, module_contents, cell_counts_per_module = \
        parse_verilog(config["verilog_file"])

    # ── 2. Validate ──
    adder_name = config["adder_module"]
    mult_name  = config["multiplier_module"]

    print(f"\n{'='*55}")
    print(f"  CHECKING MODULES")
    print(f"{'='*55}")
    print(f"  Looking for  : '{adder_name}' and '{mult_name}'")
    print(f"  Found        : {module_names}")

    if adder_name not in module_contents:
        print(f"\n   '{adder_name}' NOT FOUND!")
        print(f"  → Change 'adder_module' in CONFIG to one of:")
        for m in module_names: print(f"     '{m}'")
        raise SystemExit(1)

    if mult_name not in module_contents:
        print(f"\n   '{mult_name}' NOT FOUND!")
        print(f"  → Change 'multiplier_module' in CONFIG to one of:")
        for m in module_names: print(f"     '{m}'")
        raise SystemExit(1)

    print(f" Both modules found!")

    # ── 3. Read Areas ──
    cell_areas = get_cell_area_from_lib(config["lib_file"])

    # Fallback to LEF if LIB didn't yield areas
    if not cell_areas:
        cell_areas = get_cell_area_from_lef(config["lef_file"])

    # ── 4. Calculate Areas ──
    print(f"\n{'='*55}")
    print(f"  AREA CALCULATION")
    print(f"{'='*55}")

    adder_counts = cell_counts_per_module.get(adder_name, {})
    mult_counts  = cell_counts_per_module.get(mult_name,  {})

    adder_area = calculate_area(adder_counts, cell_areas)
    mult_area  = calculate_area(mult_counts,  cell_areas)
    total_area = adder_area + mult_area

    print(f"  Adder cells  : {dict(adder_counts)}")
    print(f"  Mult  cells  : {dict(mult_counts)}")
    print(f"  Adder area   : {adder_area:.4f} um²")
    print(f"  Mult  area   : {mult_area:.4f} um²")

    # Fallback: use cell count ratio if areas = 0
    if total_area == 0:
        print(f"    Areas = 0, using cell count ratio")
        ac = max(sum(adder_counts.values()), 1)
        mc = max(sum(mult_counts.values()),  1)
        split_ratio = ac / (ac + mc)
        adder_area  = ac * 0.1
        mult_area   = mc * 0.1
        total_area  = adder_area + mult_area
    else:
        split_ratio = adder_area / total_area

    print(f"  Split ratio  : {split_ratio:.4f}")
    print(f"  Adder gets   : {split_ratio*100:.1f}% of chip")
    print(f"  Mult  gets   : {(1-split_ratio)*100:.1f}% of chip")

    # ── 5. Calculate Regions ── <Not useful now>
    #split_x = round(config["chip_width"] * split_ratio, 3)

    #adder_region = {
    #   "llx_um": 0.0,          "lly_um": 0.0,
    #    "urx_um": split_x,      "ury_um": config["chip_height"]
    #}
    #mult_region = {
    #    "llx_um": split_x,      "lly_um": 0.0,
    #    "urx_um": config["chip_width"], "ury_um": config["chip_height"]
    #}

    #print(f"\n  Adder region : (0, 0) → ({split_x}, {config['chip_height']})")
    #print(f"  Mult  region : ({split_x}, 0) → ({config['chip_width']}, {config['chip_height']})")

    #----------------------- Sayak ------------------------
    # ── 5. Calculate Regions ──
    if config["manual_floorplan"]["enable"]:
        print(f"\n   Using MANUAL floorplan from config.json (area-based split ignored)")

        mf = config["manual_floorplan"]
        missing = [name for name in (adder_name, mult_name) if name not in mf]
        if missing:
            print(f"\n  manual_floorplan is enabled but missing region(s) for: {missing}")
            print(f"     'adder_module' = '{adder_name}'")
            print(f"     'multiplier_module' = '{mult_name}'")
            print(f"  → manual_floorplan keys in config.json must match these exactly.")
            print(f"     Current manual_floorplan keys: {[k for k in mf.keys() if k != 'enable']}")
            raise SystemExit(1)

        required_fields = {"llx_um", "lly_um", "urx_um", "ury_um"}
        for name in (adder_name, mult_name):
            missing_fields = required_fields - set(mf[name].keys())
            if missing_fields:
                print(f"\n  manual_floorplan['{name}'] is missing field(s): {missing_fields}")
                raise SystemExit(1)

        adder_region = mf[adder_name]
        mult_region  = mf[mult_name]

        if not (adder_region["urx_um"] <= mult_region["llx_um"] or
                mult_region["urx_um"] <= adder_region["llx_um"] or
                adder_region["ury_um"] <= mult_region["lly_um"] or
                mult_region["ury_um"] <= adder_region["lly_um"]):
            print(f"\n   WARNING: adder_region and multiplier_region appear to OVERLAP!")
            print(f"     Adder : {adder_region}")
            print(f"     Mult  : {mult_region}")

        for name, region in [(adder_name, adder_region), (mult_name, mult_region)]:
            if (region["urx_um"] > config["chip_width"] or
                region["ury_um"] > config["chip_height"] or
                region["llx_um"] < 0 or region["lly_um"] < 0):
                print(f"\n   WARNING: region for '{name}' extends outside "
                      f"the {config['chip_width']}×{config['chip_height']} chip!")
                print(f"     Region: {region}")

        split_x = adder_region["urx_um"]
    else:
        split_x = round(config["chip_width"] * split_ratio, 3)
        adder_region = {
            "llx_um": 0.0,          "lly_um": 0.0,
            "urx_um": split_x,      "ury_um": config["chip_height"]
        }
        mult_region = {
            "llx_um": split_x,      "lly_um": 0.0,
            "urx_um": config["chip_width"], "ury_um": config["chip_height"]
        }


    print(f"\n  Adder region : ({adder_region['llx_um']}, {adder_region['lly_um']}) → ({adder_region['urx_um']}, {adder_region['ury_um']})")
    print(f"  Mult  region : ({mult_region['llx_um']}, {mult_region['lly_um']}) → ({mult_region['urx_um']}, {mult_region['ury_um']})")

    # ── Cross-check: manual floorplan vs. area-based estimate ──
    if config["manual_floorplan"]["enable"]:
        adder_manual_area = (adder_region["urx_um"] - adder_region["llx_um"]) * \
                             (adder_region["ury_um"] - adder_region["lly_um"])
        mult_manual_area  = (mult_region["urx_um"]  - mult_region["llx_um"])  * \
                             (mult_region["ury_um"]  - mult_region["lly_um"])
        manual_split_ratio = adder_manual_area / (adder_manual_area + mult_manual_area)

        print(f"\n Manual vs. area-estimate check:")
        print(f"     Manual split   : adder = {manual_split_ratio*100:.1f}%  "
              f"mult = {(1-manual_split_ratio)*100:.1f}%")
        print(f"     Area estimate  : adder = {split_ratio*100:.1f}%  "
              f"mult = {(1-split_ratio)*100:.1f}%")

        deviation = abs(manual_split_ratio - split_ratio) * 100
        if deviation > 10:
            print(f" Manual split gives adder {manual_split_ratio*100:.1f}%, "
                  f"but area estimate suggests {split_ratio*100:.1f}% "
                  f"— consider adjusting (deviation: {deviation:.1f} pts)")
        else:
            print(f" Within {deviation:.1f} pts of area estimate — looks reasonable")


    # ── 6. Create Dirs ──
    adder_dir = os.path.join(config["output_dir"], "adder")
    mult_dir  = os.path.join(config["output_dir"], "multiplier")
    os.makedirs(adder_dir, exist_ok=True)
    os.makedirs(mult_dir,  exist_ok=True)

    # ── 7. Extract Verilog ──
    print(f"\n{'='*55}")
    print(f"  EXTRACTING MODULES")
    print(f"{'='*55}")

    adder_v = os.path.join(adder_dir, "adder.v")
    mult_v  = os.path.join(mult_dir,  "multiplier.v")

    extract_module_to_file(module_contents, adder_name, adder_v)
    extract_module_to_file(module_contents, mult_name,  mult_v)

    # ── 8. Generate TCL ──
    print(f"\n{'='*55}")
    print(f"  GENERATING TCL SCRIPTS")
    print(f"{'='*55}")

    generate_tcl(config, adder_name, adder_v, adder_dir, adder_region, mult_region)
    generate_tcl(config, mult_name,  mult_v,  mult_dir,  mult_region,  adder_region)

    # ── 9. Save JSON ──
    partition_info = {
        "chip_dimensions"  : {
            "width_um"      : config["chip_width"],
            "height_um"     : config["chip_height"],
            "dbu_per_micron": config["dbu_per_micron"]
        },
        "modules"          : {
            "adder"     : adder_name,
            "multiplier": mult_name
        },
        "area_estimation"  : {
            "adder"      : {
                "cell_counts"       : adder_counts,
                "estimated_area_um2": adder_area
            },
            "multiplier" : {
                "cell_counts"       : mult_counts,
                "estimated_area_um2": mult_area
            }
        },
        "partition"        : {
            "split_ratio"       : split_ratio,
            "split_direction"   : "vertical",
            "adder_region"      : adder_region,
            "multiplier_region" : mult_region
        },
        "files"            : {
            "adder_verilog": adder_v,
            "mult_verilog" : mult_v,
            "adder_tcl"    : f"{adder_dir}/{adder_name}_flow.tcl",
            "mult_tcl"     : f"{mult_dir}/{mult_name}_flow.tcl"
        }
    }

    json_path = os.path.join(config["output_dir"], "partition_info.json")
    with open(json_path, 'w') as f:
        json.dump(partition_info, f, indent=2)

    # ── 10. Summary ──
    print(f"\n{'='*55}")
    print(f"   SPLIT COMPLETE!")
    print(f"{'='*55}")
    print(f"  Adder  Verilog → {adder_v}")
    print(f"  Mult   Verilog → {mult_v}")
    print(f"  Adder  TCL    → {adder_dir}/{adder_name}_flow.tcl")
    print(f"  Mult   TCL    → {mult_dir}/{mult_name}_flow.tcl")
    print(f"  JSON          → {json_path}")
    print(f"{'='*55}\n")


#if __name__ == "__main__":
#   split_design(CONFIG)

if __name__ == "__main__":
    import sys
    json_path = sys.argv[1] if len(sys.argv) > 1 else "config.json"
    config = load_config(json_path)
    split_design(config)