# ==========================================================
# ARYA UPDATE TOP V1
# Automatically generated top-level hierarchical flow
# Do not edit this TCL manually.
# Modify config.json and regenerate instead.
# ==========================================================

# === Create output directories ===
file mkdir /work/Hierarchical_OpenROAD_Framework_general/generated/top/results
file mkdir /work/Hierarchical_OpenROAD_Framework_general/generated/top/reports

# === Read technology and standard-cell libraries ===
read_lef /work/Hierarchical_OpenROAD_Framework_general/inputs/NangateOpenCellLibrary.tech.lef
read_lef /work/Hierarchical_OpenROAD_Framework_general/inputs/NangateOpenCellLibrary.macro.mod.lef
read_liberty /work/Hierarchical_OpenROAD_Framework_general/inputs/NangateOpenCellLibrary_typical.lib

# === Read hardened macro LEFs ===
read_lef /work/Hierarchical_OpenROAD_Framework_general/generated/adder_8/results/adder_8.lef
read_lef /work/Hierarchical_OpenROAD_Framework_general/generated/subtractor_8/results/subtractor_8.lef
read_lef /work/Hierarchical_OpenROAD_Framework_general/generated/mux_8/results/mux_8.lef

# === Read and link top-level wrapper ===
read_verilog /work/Hierarchical_OpenROAD_Framework_general/generated/top_wrapper.v
link_design top_wrapper

# === Create top-level floorplan ===
initialize_floorplan \
  -die_area "0 0 340 210" \
  -core_area "3 3 337 207" \
  -site FreePDK45_38x28_10R_NP_162NW_34O

# initialize_floorplan removes existing tracks.
# Therefore routing tracks are created afterward.
make_tracks

# === Config-driven macro placement ===
# Module: adder_8, Instance: U_ADDER
place_macro -macro_name U_ADDER -location {4 5} -orientation R0 -exact

# Module: subtractor_8, Instance: U_SUBTRACTOR
place_macro -macro_name U_SUBTRACTOR -location {118 5} -orientation R0 -exact

# Module: mux_8, Instance: U_MUX
place_macro -macro_name U_MUX -location {232 5} -orientation R0 -exact

# === Place top-level IO pins ===
place_pins -hor_layers metal3 -ver_layers metal4

# === Check placement ===
check_placement -verbose
report_design_area

# === Write top-level results ===
write_def /work/Hierarchical_OpenROAD_Framework_general/generated/top/results/top_wrapper_macros_placed.def
write_db /work/Hierarchical_OpenROAD_Framework_general/generated/top/results/top_wrapper_macros_placed.odb

puts "=============================================="
puts "TOP-LEVEL MACRO INTEGRATION COMPLETED"
puts "DEF: /work/Hierarchical_OpenROAD_Framework_general/generated/top/results/top_wrapper_macros_placed.def"
puts "ODB: /work/Hierarchical_OpenROAD_Framework_general/generated/top/results/top_wrapper_macros_placed.odb"
puts "=============================================="
