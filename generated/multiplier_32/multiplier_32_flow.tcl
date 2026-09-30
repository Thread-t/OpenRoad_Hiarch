# ======================================================
# Block: multiplier_32
# ======================================================

set script_dir [file dirname [file normalize [info script]]]
set project_root [file normalize "$script_dir/../.."]
cd $project_root

read_lef     /Users/sayakdeb/Documents/Bremen_Study_files/Third_Sem/Digitall_Lab/Latest_project/Work_31_07_2026 /inputs/NangateOpenCellLibrary.tech.lef
read_lef     /Users/sayakdeb/Documents/Bremen_Study_files/Third_Sem/Digitall_Lab/Latest_project/Work_31_07_2026 /inputs/NangateOpenCellLibrary.macro.mod.lef
read_liberty /Users/sayakdeb/Documents/Bremen_Study_files/Third_Sem/Digitall_Lab/Latest_project/Work_31_07_2026 /inputs/NangateOpenCellLibrary_typical.lib

read_verilog /Users/sayakdeb/Documents/Bremen_Study_files/Third_Sem/Digitall_Lab/Latest_project/Work_31_07_2026 /generated/multiplier_32/multiplier_32.v
link_design  {multiplier_32}

initialize_floorplan \
  -die_area  "0.0 0.0 80.0 200.0" \
  -core_area "3.0 3.0 77.0 197.0" \
  -site      FreePDK45_38x28_10R_NP_162NW_34O

# === Sibling blocked region information ===
# blocked_region (adder_32) = 0.0 0.0 120.0 200.0
# create_blockage -bbox {0.0 0.0 120.0 200.0} -type placement -name blockage_multiplier_32_adder_32

make_tracks

place_pins -hor_layers metal3 -ver_layers metal4

global_placement -density 0.55

detailed_placement
check_placement -verbose

filler_placement "FILLCELL_X8 FILLCELL_X4 FILLCELL_X2 FILLCELL_X1"

if {[catch {global_route -congestion_iterations 50} gr_result]} {
  global_route
}
detailed_route -output_drc /Users/sayakdeb/Documents/Bremen_Study_files/Third_Sem/Digitall_Lab/Latest_project/Work_31_07_2026 /generated/multiplier_32/reports/multiplier_32.drc

report_design_area
report_wns
report_tns

write_def /Users/sayakdeb/Documents/Bremen_Study_files/Third_Sem/Digitall_Lab/Latest_project/Work_31_07_2026 /generated/multiplier_32/results/multiplier_32_placed_routed.def

if {[info commands write_abstract_lef] != ""} {
  write_abstract_lef /Users/sayakdeb/Documents/Bremen_Study_files/Third_Sem/Digitall_Lab/Latest_project/Work_31_07_2026 /generated/multiplier_32/results/multiplier_32.lef
}
