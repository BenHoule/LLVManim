"""Tests for package/module entrypoints executed via `python -m ...`."""

from __future__ import annotations

import runpy
from importlib import import_module
from unittest.mock import patch

import pytest


def test_package_dunder_main_exits_with_cli_main_code() -> None:
    """`python -m llvmanim` should forward to cli.main.main() exit code."""
    with patch("llvmanim.cli.main.main", return_value=7), pytest.raises(SystemExit) as excinfo:
        runpy.run_module("llvmanim.__main__", run_name="__main__")

    assert excinfo.value.code == 7


def test_cli_dunder_main_exits_with_cli_main_code() -> None:
    """`python -m llvmanim.cli` should forward to cli.main.main() exit code."""
    with patch("llvmanim.cli.main.main", return_value=11), pytest.raises(SystemExit) as excinfo:
        runpy.run_module("llvmanim.cli.__main__", run_name="__main__")

    assert excinfo.value.code == 11


def test_package_dunder_main_import_has_no_side_effect_exit() -> None:
    """Importing llvmanim.__main__ as a module should not raise SystemExit."""
    mod = import_module("llvmanim.__main__")
    assert mod is not None


def test_cli_dunder_main_import_has_no_side_effect_exit() -> None:
    """Importing llvmanim.cli.__main__ as a module should not raise SystemExit."""
    mod = import_module("llvmanim.cli.__main__")
    assert mod is not None
