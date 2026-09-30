# ======================================================
# Block: mux_8
# ======================================================

set script_dir [file dirname [file normalize [info script]]]
set project_root [file normalize "$script_dir/../.."]
cd $project_root

read_lef     /work/Hierarchical_OpenROAD_Framework_general/inputs/NangateOpenCellLibrary.tech.lef
read_lef     /work/Hierarchical_OpenROAD_Framework_general/inputs/NangateOpenCellLibrary.macro.mod.lef
read_liberty /work/Hierarchical_OpenROAD_Framework_general/inputs/NangateOpenCellLibrary_typical.lib

read_verilog /work/Hierarchical_OpenROAD_Framework_general/generated/mux_8/mux_8.v
link_design  {mux_8}

initialize_floorplan \
  -die_area  "0.0 0.0 80.0 200.0" \
  -core_area "3.0 3.0 77.0 197.0" \
  -site      FreePDK45_38x28_10R_NP_162NW_34O

# === Sibling blocked region information ===
# blocked_region (adder_8) = 0.0 0.0 110.0 200.0
# create_blockage -bbox {0.0 0.0 110.0 200.0} -type placement -name blockage_mux_8_adder_8
# blocked_region (subtractor_8) = 110.0 0.0 220.0 200.0
# create_blockage -bbox {110.0 0.0 220.0 200.0} -type placement -name blockage_mux_8_subtractor_8

make_tracks

place_pins -hor_layers metal3 -ver_layers metal4

global_placement -density 0.5

detailed_placement
check_placement -verbose

filler_placement "FILLCELL_X8 FILLCELL_X4 FILLCELL_X2 FILLCELL_X1"

if {[catch {global_route -congestion_iterations 50} gr_result]} {
  global_route
}
detailed_route -output_drc /work/Hierarchical_OpenROAD_Framework_general/generated/mux_8/reports/mux_8.drc

report_design_area
report_wns
report_tns

write_def /work/Hierarchical_OpenROAD_Framework_general/generated/mux_8/results/mux_8_placed_routed.def

if {[info commands write_abstract_lef] != ""} {
  write_abstract_lef /work/Hierarchical_OpenROAD_Framework_general/generated/mux_8/results/mux_8.lef
}
