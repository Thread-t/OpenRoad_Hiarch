# ==========================================================
# ARYA UPDATE MACRO LEF V3
# Generate abstract LEF for the adder partition.
# A separate OpenROAD run is used because this OpenROAD
# version does not support a standalone clear command.
# ==========================================================

# Read technology and standard-cell LEF files
read_lef inputs/NangateOpenCellLibrary.tech.lef
read_lef inputs/NangateOpenCellLibrary.macro.mod.lef

# Read routed adder DEF
read_def generated/adder/results/adder_32_placed_routed.def

# Write abstract Macro LEF
write_abstract_lef generated/macros/adder_32.lef
