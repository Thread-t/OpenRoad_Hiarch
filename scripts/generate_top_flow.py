#!/usr/bin/env python3

"""
ARYA UPDATE TOP V1

Generates the OpenROAD TCL script for top-level hierarchical
macro integration using values from configs/config.json.

Generated file:
    generated/top/top_wrapper_flow.tcl
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


# ==========================================================
# Project paths
# ==========================================================

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

DEFAULT_CONFIG_PATH = PROJECT_ROOT / "configs" / "config.json"

INPUT_DIR = PROJECT_ROOT / "inputs"
GENERATED_DIR = PROJECT_ROOT / "generated"
TOP_DIR = GENERATED_DIR / "top"
TOP_RESULTS_DIR = TOP_DIR / "results"
TOP_REPORTS_DIR = TOP_DIR / "reports"

TOP_WRAPPER_FILE = GENERATED_DIR / "top_wrapper.v"
OUTPUT_TCL_FILE = TOP_DIR / "top_wrapper_flow.tcl"


# ==========================================================
# Helper functions
# ==========================================================

def load_json(path: Path) -> dict[str, Any]:
    """Load the JSON configuration file."""

    if not path.is_file():
        raise FileNotFoundError(
            f"Configuration file not found: {path}"
        )

    try:
        with path.open("r", encoding="utf-8") as file:
            config = json.load(file)

    except json.JSONDecodeError as error:
        raise ValueError(
            f"Invalid JSON in {path}\n"
            f"Line {error.lineno}, "
            f"column {error.colno}: {error.msg}"
        ) from error

    if not isinstance(config, dict):
        raise ValueError(
            "The root of config.json must be a JSON object."
        )

    return config


def require_file(path: Path, description: str) -> None:
    """Check that a required file exists."""

    if not path.is_file():
        raise FileNotFoundError(
            f"{description} not found: {path}"
        )


def project_relative(path: Path) -> str:
    """
    Convert a path to a project-relative Linux-style path
    for use inside OpenROAD TCL.
    """

    return path.resolve().relative_to(
        PROJECT_ROOT.resolve()
    ).as_posix()


def require_string(
    mapping: dict[str, Any],
    key: str,
    context: str
) -> str:
    """Read a required non-empty string."""

    value = mapping.get(key)

    if not isinstance(value, str) or not value.strip():
        raise ValueError(
            f"{context}.{key} must be a non-empty string."
        )

    return value.strip()


def require_number(
    mapping: dict[str, Any],
    key: str,
    context: str
) -> float:
    """Read a required numeric value."""

    if key not in mapping:
        raise KeyError(
            f"Missing {context}.{key}"
        )

    try:
        return float(mapping[key])

    except (TypeError, ValueError) as error:
        raise ValueError(
            f"{context}.{key} must be numeric. "
            f"Received: {mapping[key]!r}"
        ) from error


def read_rectangle(
    mapping: dict[str, Any],
    context: str
) -> dict[str, float]:
    """Read and validate a rectangular area."""

    rectangle = {
        "llx_um": require_number(
            mapping,
            "llx_um",
            context
        ),
        "lly_um": require_number(
            mapping,
            "lly_um",
            context
        ),
        "urx_um": require_number(
            mapping,
            "urx_um",
            context
        ),
        "ury_um": require_number(
            mapping,
            "ury_um",
            context
        ),
    }

    if rectangle["urx_um"] <= rectangle["llx_um"]:
        raise ValueError(
            f"{context}: urx_um must be greater than llx_um."
        )

    if rectangle["ury_um"] <= rectangle["lly_um"]:
        raise ValueError(
            f"{context}: ury_um must be greater than lly_um."
        )

    return rectangle


def rectangle_to_tcl(
    rectangle: dict[str, float]
) -> str:
    """Convert a rectangle to OpenROAD TCL coordinates."""

    return (
        f'{rectangle["llx_um"]:g} '
        f'{rectangle["lly_um"]:g} '
        f'{rectangle["urx_um"]:g} '
        f'{rectangle["ury_um"]:g}'
    )


# ==========================================================
# Read top-level configuration
# ==========================================================

def read_top_configuration(
    config: dict[str, Any]
) -> dict[str, Any]:
    """Read and validate the top_integration section."""

    top_config = config.get("top_integration")

    if not isinstance(top_config, dict):
        raise KeyError(
            "Missing top_integration section in config.json."
        )

    top_module = require_string(
        top_config,
        "top_module",
        "top_integration"
    )

    die_area_raw = top_config.get("die_area")
    core_area_raw = top_config.get("core_area")
    pin_layers_raw = top_config.get("pin_layers")
    macros_raw = top_config.get("macros")

    if not isinstance(die_area_raw, dict):
        raise KeyError(
            "Missing top_integration.die_area."
        )

    if not isinstance(core_area_raw, dict):
        raise KeyError(
            "Missing top_integration.core_area."
        )

    if not isinstance(pin_layers_raw, dict):
        raise KeyError(
            "Missing top_integration.pin_layers."
        )

    if not isinstance(macros_raw, list) or not macros_raw:
        raise ValueError(
            "top_integration.macros must contain "
            "at least one macro."
        )

    die_area = read_rectangle(
        die_area_raw,
        "top_integration.die_area"
    )

    core_area = read_rectangle(
        core_area_raw,
        "top_integration.core_area"
    )

    horizontal_layer = require_string(
        pin_layers_raw,
        "horizontal",
        "top_integration.pin_layers"
    )

    vertical_layer = require_string(
        pin_layers_raw,
        "vertical",
        "top_integration.pin_layers"
    )

    # Check that core area lies inside die area.
    if (
        core_area["llx_um"] < die_area["llx_um"]
        or core_area["lly_um"] < die_area["lly_um"]
        or core_area["urx_um"] > die_area["urx_um"]
        or core_area["ury_um"] > die_area["ury_um"]
    ):
        raise ValueError(
            "The top-level core area must lie "
            "inside the die area."
        )

    macros: list[dict[str, Any]] = []
    instance_names: set[str] = set()

    for index, macro_raw in enumerate(macros_raw):

        context = f"top_integration.macros[{index}]"

        if not isinstance(macro_raw, dict):
            raise ValueError(
                f"{context} must be a JSON object."
            )

        module = require_string(
            macro_raw,
            "module",
            context
        )

        instance = require_string(
            macro_raw,
            "instance",
            context
        )

        lef_relative = require_string(
            macro_raw,
            "lef",
            context
        )

        orientation = require_string(
            macro_raw,
            "orientation",
            context
        )

        x_um = require_number(
            macro_raw,
            "x_um",
            context
        )

        y_um = require_number(
            macro_raw,
            "y_um",
            context
        )

        if instance in instance_names:
            raise ValueError(
                f"Duplicate macro instance name: {instance}"
            )

        instance_names.add(instance)

        lef_path = PROJECT_ROOT / lef_relative

        require_file(
            lef_path,
            f"Macro LEF for {instance}"
        )

        macros.append(
            {
                "module": module,
                "instance": instance,
                "lef_path": lef_path,
                "x_um": x_um,
                "y_um": y_um,
                "orientation": orientation,
            }
        )

    return {
        "top_module": top_module,
        "die_area": die_area,
        "core_area": core_area,
        "horizontal_layer": horizontal_layer,
        "vertical_layer": vertical_layer,
        "macros": macros,
    }


# ==========================================================
# Generate OpenROAD TCL
# ==========================================================

def generate_tcl(
    config: dict[str, Any],
    top_config: dict[str, Any]
) -> str:
    """Generate the top-level integration TCL."""

    tech_lef = PROJECT_ROOT / config.get(
        "tech_lef_file",
        "inputs/NangateOpenCellLibrary.tech.lef"
    )

    standard_cell_lef = PROJECT_ROOT / config.get(
        "lef_file",
        "inputs/NangateOpenCellLibrary.macro.mod.lef"
    )

    liberty_file = PROJECT_ROOT / config.get(
        "lib_file",
        "inputs/NangateOpenCellLibrary_typical.lib"
    )

    require_file(
        tech_lef,
        "Technology LEF"
    )

    require_file(
        standard_cell_lef,
        "Standard-cell LEF"
    )

    require_file(
        liberty_file,
        "Liberty file"
    )

    require_file(
        TOP_WRAPPER_FILE,
        "Top-wrapper Verilog"
    )

    site_name = config.get(
        "site",
        "FreePDK45_38x28_10R_NP_162NW_34O"
    )

    if not isinstance(site_name, str) or not site_name.strip():
        raise ValueError(
            "The site value in config.json must "
            "be a non-empty string."
        )

    top_module = top_config["top_module"]

    die_area = rectangle_to_tcl(
        top_config["die_area"]
    )

    core_area = rectangle_to_tcl(
        top_config["core_area"]
    )

    horizontal_layer = top_config["horizontal_layer"]
    vertical_layer = top_config["vertical_layer"]

    output_def = (
        TOP_RESULTS_DIR /
        f"{top_module}_macros_placed.def"
    )

    output_odb = (
        TOP_RESULTS_DIR /
        f"{top_module}_macros_placed.odb"
    )

    lines: list[str] = [
        "# ==========================================================",
        "# ARYA UPDATE TOP V1",
        "# Automatically generated top-level hierarchical flow",
        "# Do not edit this TCL manually.",
        "# Modify config.json and regenerate instead.",
        "# ==========================================================",
        "",
        "# === Create output directories ===",
        f"file mkdir {project_relative(TOP_RESULTS_DIR)}",
        f"file mkdir {project_relative(TOP_REPORTS_DIR)}",
        "",
        "# === Read technology and standard-cell libraries ===",
        f"read_lef {project_relative(tech_lef)}",
        f"read_lef {project_relative(standard_cell_lef)}",
        f"read_liberty {project_relative(liberty_file)}",
        "",
        "# === Read hardened macro LEFs ===",
    ]

    for macro in top_config["macros"]:
        lines.append(
            f"read_lef "
            f"{project_relative(macro['lef_path'])}"
        )

    lines.extend(
        [
            "",
            "# === Read and link top-level wrapper ===",
            f"read_verilog "
            f"{project_relative(TOP_WRAPPER_FILE)}",
            f"link_design {top_module}",
            "",
            "# === Create top-level floorplan ===",
            "initialize_floorplan \\",
            f'  -die_area "{die_area}" \\',
            f'  -core_area "{core_area}" \\',
            f"  -site {site_name}",
            "",
            "# initialize_floorplan removes existing tracks.",
            "# Therefore routing tracks are created afterward.",
            "make_tracks",
            "",
            "# === Config-driven macro placement ===",
        ]
    )

    for macro in top_config["macros"]:
        lines.extend(
            [
                (
                    f"# Module: {macro['module']}, "
                    f"Instance: {macro['instance']}"
                ),
                (
                    f"place_macro "
                    f"-macro_name {macro['instance']} "
                    f"-location "
                    f"{{{macro['x_um']:g} "
                    f"{macro['y_um']:g}}} "
                    f"-orientation {macro['orientation']} "
                    f"-exact"
                ),
                "",
            ]
        )

    lines.extend(
        [
            "# === Place top-level IO pins ===",
            (
                f"place_pins "
                f"-hor_layers {horizontal_layer} "
                f"-ver_layers {vertical_layer}"
            ),
            "",
            "# === Check placement ===",
            "check_placement -verbose",
            "report_design_area",
            "",
            "# === Write top-level results ===",
            f"write_def {project_relative(output_def)}",
            f"write_db {project_relative(output_odb)}",
            "",
            'puts "=============================================="',
            'puts "TOP-LEVEL MACRO INTEGRATION COMPLETED"',
            f'puts "DEF: {project_relative(output_def)}"',
            f'puts "ODB: {project_relative(output_odb)}"',
            'puts "=============================================="',
            "",
        ]
    )

    return "\n".join(lines)


# ==========================================================
# Main function
# ==========================================================

def main() -> int:
    """Run the generator."""

    config_path = DEFAULT_CONFIG_PATH

    if len(sys.argv) > 2:
        print(
            "Usage:\n"
            "  python scripts/generate_top_flow.py\n"
            "  python scripts/generate_top_flow.py "
            "configs/config.json"
        )
        return 1

    if len(sys.argv) == 2:
        supplied_path = Path(sys.argv[1])

        if supplied_path.is_absolute():
            config_path = supplied_path
        else:
            config_path = PROJECT_ROOT / supplied_path

    try:
        config = load_json(config_path)

        top_config = read_top_configuration(
            config
        )

        TOP_DIR.mkdir(
            parents=True,
            exist_ok=True
        )

        TOP_RESULTS_DIR.mkdir(
            parents=True,
            exist_ok=True
        )

        TOP_REPORTS_DIR.mkdir(
            parents=True,
            exist_ok=True
        )

        tcl_content = generate_tcl(
            config,
            top_config
        )

        OUTPUT_TCL_FILE.write_text(
            tcl_content,
            encoding="utf-8"
        )

    except (
        FileNotFoundError,
        KeyError,
        ValueError
    ) as error:

        print(f"\nERROR: {error}")
        return 1

    print("\nTop-level flow generation completed.")
    print(f"Config file : {config_path}")
    print(f"Generated TCL: {OUTPUT_TCL_FILE}")

    print("\nConfigured macro placements:")

    for macro in top_config["macros"]:
        print(
            f"  {macro['instance']:<16} "
            f"{macro['module']:<16} "
            f"({macro['x_um']:g}, "
            f"{macro['y_um']:g}) "
            f"{macro['orientation']}"
        )

    print("\nRun inside Docker from the project root:")
    print(
        "  openroad "
        "generated/top/top_wrapper_flow.tcl"
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())