# ─────────────────────────────────────────────
# OpenROAD TCL Script Made by Sayak
# Block    : multiplier_32
# Generated: by split_net.py
# ─────────────────────────────────────────────

# === Read technology files ===
read_lef     /Users/sayakdeb/Documents/Bremen_Study_files/Third_Sem/Digitall_Lab/Latest_project/Work_1_07_2026/NangateOpenCellLibrary.tech.lef
read_lef     /Users/sayakdeb/Documents/Bremen_Study_files/Third_Sem/Digitall_Lab/Latest_project/Work_1_07_2026/NangateOpenCellLibrary.macro.mod.lef
read_liberty /Users/sayakdeb/Documents/Bremen_Study_files/Third_Sem/Digitall_Lab/Latest_project/Work_1_07_2026/NangateOpenCellLibrary_typical.lib

# === Read gate-level netlist ===
read_verilog /Users/sayakdeb/Documents/Bremen_Study_files/Third_Sem/Digitall_Lab/Latest_project/Work_1_07_2026/results/multiplier/multiplier.v
link_design  multiplier_32

# === Floorplan (block's actual chip-coordinate region) ===
initialize_floorplan \
  -die_area  "120.0 0.0 200.0 200.0" \
  -core_area "123.0 3.0 197.0 197.0" \
  -site      FreePDK45_38x28_10R_NP_162NW_34O

# === Block sibling region (cannot be placed into) ===
create_blockage -bbox {0.0 0.0 120.0 200.0} -type placement -name blockage_multiplier_32

# === Initialize routing tracks ===
make_tracks

# === Pin placement ===
place_pins -hor_layers metal1 -ver_layers metal2

# === Global placement ===
global_placement -density 0.7

# === Detailed placement ===
detailed_placement
check_placement -verbose

# === Filler cells ===
filler_placement "FILLCELL_X8 FILLCELL_X4 FILLCELL_X2 FILLCELL_X1"

# === Route ===
global_route
detailed_route -output_drc reports/multiplier_32.drc

# === Reports ===
report_design_area
report_wns
report_tns

# === Export layout ===
write_def results/multiplier_32_placed_routed.def
