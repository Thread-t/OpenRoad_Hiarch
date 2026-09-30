import json
from pathlib import Path


def get_project_root() -> Path:
    """Returns the absolute project root directory."""

    # ARYA UPDATE V1:
    # flow_utils.py is stored inside the scripts directory.
    # Therefore, the project root is one directory above scripts.
    return Path(__file__).resolve().parent.parent


def tcl_path(path: str | Path) -> str:
    """Converts any path to a POSIX-style string with forward slashes for TCL/OpenROAD."""
    return Path(path).as_posix()

DEFAULT_CONFIG = {
    "top_wrapper_module": "top_wrapper",
}

def deep_update(base_dict: dict, update_dict: dict) -> dict:
    """Recursively merges user configuration dictionaries into defaults."""
    for k, v in update_dict.items():
        if isinstance(v, dict) and k in base_dict and isinstance(base_dict[k], dict):
            deep_update(base_dict[k], v)
        else:
            base_dict[k] = v
    return base_dict

def load_and_validate_config(config_path: str | Path = "configs/config.json") -> dict:
    """Loads, merges with defaults, and validates the configuration JSON."""
    root = get_project_root()
    full_path = root / config_path if not Path(config_path).is_absolute() else Path(config_path)
    
    config = DEFAULT_CONFIG.copy()
    if full_path.exists():
        with open(full_path, "r") as f:
            user_config = json.load(f)
            deep_update(config, user_config)
            
    def require_string(val, name):
        if not isinstance(val, str) or not val:
            raise ValueError(f"Configuration error: '{name}' must be a non-empty string.")
        return val

    if "top_wrapper_module" in config:
        require_string(config["top_wrapper_module"], "top_wrapper_module")

    return config