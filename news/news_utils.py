# Standard Imports
from typing import Dict, Any, List
from pathlib import Path

# Third Party Imports
import yaml

# Local Imports


def load_config(config_path: Path) -> Dict[str, Any]:
    """
    Load YAML configuration from disk

    Why this exists
    - Centralizing config loading prevents "config drift" where different modules parse YAML differently
    - Fail fast with clear messages when config.yaml is missing or malformed
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found at: {config_path}")

    with config_path.open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    if not isinstance(cfg, dict):
        raise ValueError(
            "config.yaml must parse into a dictionary at the top level")

    return cfg


def require_section(cfg: Dict[str, Any], section: str) -> Dict[str, Any]:
    """
    Enforce a required top-level config section

    Why this exists
    - This produces an actionable error tied to config.yaml structure
    """
    value = cfg.get(section)
    if not isinstance(value, dict):
        raise ValueError(
            f"config.yaml must contain a top-level '{section}' mapping")
    return value


def require_str(section: Dict[str, Any], key: str) -> str:
    value = section.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"config.yaml: '{key}' must be a non-empty string")
    return value.strip()


def require_float(section: Dict[str, Any], key: str) -> float:
    value = section.get(key)
    try:
        return float(value) # type: ignore
    except Exception as e:
        raise ValueError(
            f"config.yaml: '{key}' must be a number. Got '{value}'") from e
    

def require_int(section: Dict[str, Any], key: str) -> int:
    value = section.get(key)
    try:
        return int(value) # type: ignore
    except Exception as e:
        raise ValueError(
            f"config.yaml: '{key}' must be an integer. Got '{value}'") from e


def require_list(section: Dict[str, Any], key: str) -> List[str]:
    value = section.get(key)
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(
            f"config.yaml: '{key}' must be a list. Got type={type(value)}")
    out: List[str] = []
    for item in value:
        if isinstance(item, str) and item.strip():
            out.append(item.strip())
    return out


def require_dict(section: Dict[str, Any], key: str) -> Dict[str, str]:
    value = section.get(key)
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError(
            f"config.yaml: '{key}' must be a dict. Got type={type(value)}")
    out: Dict[str, str] = {}
    for k, v in value.items():
        if isinstance(k, str) and isinstance(v, str):
            out[k] = v
    return out


def resolve_repo_path(project_root: Path, relative_path: str, 
                      ensure_parent: bool = False) -> Path:
    if not isinstance(relative_path, str) or not relative_path.strip():
        raise ValueError("config.yaml: path values must be non-empty strings")
    resolved = project_root / relative_path.strip()
    if ensure_parent:
        resolved.parent.mkdir(parents=True, exist_ok=True)
    return resolved