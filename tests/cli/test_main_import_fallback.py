"""Import-time fallback behavior tests for llvmanim.cli.main."""

from __future__ import annotations

import importlib
import sys
from types import ModuleType


def test_cli_main_sets_manim_config_none_when_config_import_fails() -> None:
    """If `from manim import config` fails, module should set manim_config to None."""
    import llvmanim.cli.main as cli_main

    fake_manim = ModuleType("manim")
    saved_manim = sys.modules.get("manim")
    sys.modules["manim"] = fake_manim
    try:
        importlib.reload(cli_main)
        assert cli_main.manim_config is None
    finally:
        if saved_manim is None:
            sys.modules.pop("manim", None)
        else:
            sys.modules["manim"] = saved_manim
        importlib.reload(cli_main)
