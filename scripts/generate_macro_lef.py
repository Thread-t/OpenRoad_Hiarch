import os


# ==========================================================
# Project paths
# ==========================================================

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

MACROS_DIR = os.path.join(
    PROJECT_ROOT,
    "generated",
    "macros"
)

ADDER_TCL = os.path.join(
    MACROS_DIR,
    "generate_adder_macro_lef.tcl"
)

MULTIPLIER_TCL = os.path.join(
    MACROS_DIR,
    "generate_multiplier_macro_lef.tcl"
)


# ==========================================================
# Helper functions
# ==========================================================

def rel(path):
    """
    Convert an absolute path into a project-relative,
    Linux-friendly path for use inside OpenROAD TCL scripts.
    """
    return os.path.relpath(path, PROJECT_ROOT).replace("\\", "/")


def require_file(path, description):
    """
    Check whether a required input file exists.
    """
    if not os.path.isfile(path):
        raise FileNotFoundError(
            f"{description} not found: {path}"
        )


# ==========================================================
# Generate adder Macro LEF TCL
# ==========================================================

def generate_adder_tcl():
    tech_lef_abs = os.path.join(
        PROJECT_ROOT,
        "inputs",
        "NangateOpenCellLibrary.tech.lef"
    )

    std_lef_abs = os.path.join(
        PROJECT_ROOT,
        "inputs",
        "NangateOpenCellLibrary.macro.mod.lef"
    )

    adder_def_abs = os.path.join(
        PROJECT_ROOT,
        "generated",
        "adder",
        "results",
        "adder_32_placed_routed.def"
    )

    adder_lef_abs = os.path.join(
        PROJECT_ROOT,
        "generated",
        "macros",
        "adder_32.lef"
    )

    tech_lef = rel(tech_lef_abs)
    std_lef = rel(std_lef_abs)
    adder_def = rel(adder_def_abs)
    adder_lef = rel(adder_lef_abs)

    with open(ADDER_TCL, "w", encoding="utf-8") as f:
        f.write("# ==========================================================\n")
        f.write("# ARYA UPDATE MACRO LEF V3\n")
        f.write("# Generate abstract LEF for the adder partition.\n")
        f.write("# A separate OpenROAD run is used because this OpenROAD\n")
        f.write("# version does not support a standalone clear command.\n")
        f.write("# ==========================================================\n\n")

        f.write("# Read technology and standard-cell LEF files\n")
        f.write(f"read_lef {tech_lef}\n")
        f.write(f"read_lef {std_lef}\n\n")

        f.write("# Read routed adder DEF\n")
        f.write(f"read_def {adder_def}\n\n")

        f.write("# Write abstract Macro LEF\n")
        f.write(f"write_abstract_lef {adder_lef}\n")


# ==========================================================
# Generate multiplier Macro LEF TCL
# ==========================================================

def generate_multiplier_tcl():
    tech_lef_abs = os.path.join(
        PROJECT_ROOT,
        "inputs",
        "NangateOpenCellLibrary.tech.lef"
    )

    std_lef_abs = os.path.join(
        PROJECT_ROOT,
        "inputs",
        "NangateOpenCellLibrary.macro.mod.lef"
    )

    multiplier_def_abs = os.path.join(
        PROJECT_ROOT,
        "generated",
        "multiplier",
        "results",
        "multiplier_32_placed_routed.def"
    )

    multiplier_lef_abs = os.path.join(
        PROJECT_ROOT,
        "generated",
        "macros",
        "multiplier_32.lef"
    )

    tech_lef = rel(tech_lef_abs)
    std_lef = rel(std_lef_abs)
    multiplier_def = rel(multiplier_def_abs)
    multiplier_lef = rel(multiplier_lef_abs)

    with open(MULTIPLIER_TCL, "w", encoding="utf-8") as f:
        f.write("# ==========================================================\n")
        f.write("# ARYA UPDATE MACRO LEF V3\n")
        f.write("# Generate abstract LEF for the multiplier partition.\n")
        f.write("# A separate OpenROAD run is used because this OpenROAD\n")
        f.write("# version does not support a standalone clear command.\n")
        f.write("# ==========================================================\n\n")

        f.write("# Read technology and standard-cell LEF files\n")
        f.write(f"read_lef {tech_lef}\n")
        f.write(f"read_lef {std_lef}\n\n")

        f.write("# Read routed multiplier DEF\n")
        f.write(f"read_def {multiplier_def}\n\n")

        f.write("# Write abstract Macro LEF\n")
        f.write(f"write_abstract_lef {multiplier_lef}\n")


# ==========================================================
# Main
# ==========================================================

def main():
    os.makedirs(MACROS_DIR, exist_ok=True)

    required_files = {
        "Technology LEF": os.path.join(
            PROJECT_ROOT,
            "inputs",
            "NangateOpenCellLibrary.tech.lef"
        ),
        "Standard-cell LEF": os.path.join(
            PROJECT_ROOT,
            "inputs",
            "NangateOpenCellLibrary.macro.mod.lef"
        ),
        "Adder routed DEF": os.path.join(
            PROJECT_ROOT,
            "generated",
            "adder",
            "results",
            "adder_32_placed_routed.def"
        ),
        "Multiplier routed DEF": os.path.join(
            PROJECT_ROOT,
            "generated",
            "multiplier",
            "results",
            "multiplier_32_placed_routed.def"
        )
    }

    print("Checking required input files...")

    for description, path in required_files.items():
        require_file(path, description)
        print(f"Found: {description}")

    generate_adder_tcl()
    generate_multiplier_tcl()

    print("\nMacro LEF TCL generation complete.")
    print("Generated:", ADDER_TCL)
    print("Generated:", MULTIPLIER_TCL)

    print("\nRun these commands inside Docker from the project root:")
    print(
        "openroad "
        "generated/macros/generate_adder_macro_lef.tcl"
    )
    print(
        "openroad "
        "generated/macros/generate_multiplier_macro_lef.tcl"
    )


if __name__ == "__main__":
    main()
