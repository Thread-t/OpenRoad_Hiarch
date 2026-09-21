# ==========================================================
# ARYA UPDATE TOP V1
# Automatically generated top-level hierarchical flow
# Do not edit this TCL manually.
# Modify config.json and regenerate instead.
# ==========================================================

# === Create output directories ===
file mkdir generated/top/results
file mkdir generated/top/reports

# === Read technology and standard-cell libraries ===
read_lef inputs/NangateOpenCellLibrary.tech.lef
read_lef inputs/NangateOpenCellLibrary.macro.mod.lef
read_liberty inputs/NangateOpenCellLibrary_typical.lib

# === Read hardened macro LEFs ===
read_lef generated/macros/adder_32.lef
read_lef generated/macros/multiplier_32.lef

# === Read and link top-level wrapper ===
read_verilog generated/top_wrapper.v
link_design top_wrapper

# === Create top-level floorplan ===
initialize_floorplan \
  -die_area "0 0 240 240" \
  -core_area "5 5 235 235" \
  -site FreePDK45_38x28_10R_NP_162NW_34O

# initialize_floorplan removes existing tracks.
# Therefore routing tracks are created afterward.
make_tracks

# === Config-driven macro placement ===
# Module: adder_32, Instance: U_ADDER
place_macro -macro_name U_ADDER -location {10 20} -orientation R0 -exact

# Module: multiplier_32, Instance: U_MULTIPLIER
place_macro -macro_name U_MULTIPLIER -location {140 20} -orientation R0 -exact

# === Place top-level IO pins ===
place_pins -hor_layers metal3 -ver_layers metal4

# === Check placement ===
check_placement -verbose
report_design_area

# === Write top-level results ===
write_def generated/top/results/top_wrapper_macros_placed.def
write_db generated/top/results/top_wrapper_macros_placed.odb

puts "=============================================="
puts "TOP-LEVEL MACRO INTEGRATION COMPLETED"
puts "DEF: generated/top/results/top_wrapper_macros_placed.def"
puts "ODB: generated/top/results/top_wrapper_macros_placed.odb"
puts "=============================================="
