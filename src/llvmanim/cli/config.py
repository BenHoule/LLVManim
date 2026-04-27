"""
YAML configuration file support for LLVManim.

Loads a .llvmanim.yaml (or llvmanim.yaml) config file from the current directory
or any parent directory, and merges its values as CLI argument defaults.

Config file keys mirror the CLI flags (using underscores instead of hyphens).
Any key in the config file can be overridden by passing the corresponding CLI flag explicitly.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

_CONFIG_FILENAMES = [".llvmanim.yaml", ".llvmanim.yml", "llvmanim.yaml", "llvmanim.yml"]

_VALID_KEYS = {
    "ir_mode",
    "speed",
    "format",
    "gif_fps",
    "gif_width",
    "outdir",
    "yes",
    "animate",
    "preview",
    "draw",
    "json",
    "color_scheme",
    "quality",
    "disable_caching",
}

_DEFAULTS: dict[str, Any] = {
    "ir_mode": "basic",
    "speed": 1.0,
    "format": "mp4",
    "gif_fps": 12,
    "gif_width": 960,
    "outdir": ".",
    "yes": False,
    "animate": False,
    "preview": False,
    "draw": False,
    "json": False,
    "color_scheme": "dark",
    "quality": None,
    "disable_caching": False,
}


def find_config_file(start: Path | None = None) -> Path | None:
    """Walk up from start (default: cwd) looking for a config file."""
    current = (start or Path.cwd()).resolve()
    for directory in [current, *current.parents]:
        for name in _CONFIG_FILENAMES:
            candidate = directory / name
            if candidate.is_file():
                return candidate
    return None


def load_config(path: Path) -> dict[str, Any]:
    """
    Parse a YAML config file and return a dict of validated settings.
    Raises ValueError on unrecognized keys or bad values.
    """
    try:
        import yaml  # type: ignore[import]
    except ImportError as exc:
        raise ImportError(
            "PyYAML is required to load a config file. Install it with: pip install pyyaml"
        ) from exc

    with path.open("r") as f:
        raw = yaml.safe_load(f)

    if raw is None:
        return {}

    if not isinstance(raw, dict):
        raise ValueError(f"Config file must be a YAML mapping, got: {type(raw).__name__}")

    raw = {str(k): v for k, v in raw.items()}
    unknown = set(raw.keys()) - _VALID_KEYS
    if unknown:
        raise ValueError(f"Unknown config keys: {', '.join(sorted(unknown))}")

    validated: dict[str, Any] = {}

    if "ir_mode" in raw:
        val = raw["ir_mode"]
        if val not in ("basic", "rich", "rich-ssa"):
            raise ValueError(f"ir_mode must be one of: basic, rich, rich-ssa (got: {val!r})")
        validated["ir_mode"] = val

    if "speed" in raw:
        val = float(raw["speed"])
        if val <= 0:
            raise ValueError(f"speed must be a positive number (got: {val})")
        validated["speed"] = val

    if "format" in raw:
        val = raw["format"]
        if val not in ("mp4", "gif"):
            raise ValueError(f"format must be one of: mp4, gif (got: {val!r})")
        validated["format"] = val

    if "gif_fps" in raw:
        validated["gif_fps"] = max(1, int(raw["gif_fps"]))

    if "gif_width" in raw:
        validated["gif_width"] = max(64, int(raw["gif_width"]))

    if "outdir" in raw:
        validated["outdir"] = str(raw["outdir"])

    for bool_key in ("yes", "animate", "preview", "draw", "json"):
        if bool_key in raw:
            validated[bool_key] = bool(raw[bool_key])

    if "color_scheme" in raw:
        val = raw["color_scheme"]
        if val not in ("dark", "light"):
            raise ValueError(f"color_scheme must be one of: dark, light (got: {val!r})")
        validated["color_scheme"] = val

    if "quality" in raw:
        val = raw["quality"]
        if val not in ("l", "m", "h", "p", "k"):
            raise ValueError(f"quality must be one of: l, m, h, p, k (got: {val!r})")
        validated["quality"] = val

    if "disable_caching" in raw:
        validated["disable_caching"] = bool(raw["disable_caching"])

    return validated


def apply_config_defaults(args: Any, config: dict[str, Any]) -> None:
    """
    Apply config file values to parsed argparse args, but only for arguments
    that were not explicitly set on the command line (i.e. still at their default).
    """
    for key, value in config.items():
        arg_key = key.replace("-", "_")
        default = _DEFAULTS.get(key)
        current = getattr(args, arg_key, None)
        # Only override if the arg is still at its argparse default
        if current == default:
            setattr(args, arg_key, value)
