"""Shared pytest fixtures and baseline test taxonomy markers."""

from __future__ import annotations

from pathlib import Path

import pytest

_ALL_KINDS_IR = """
define void @f(ptr %p) {
entry:
  %x = alloca i32
  store i32 99, ptr %x
  %v = load i32, ptr %x
  %cond = icmp eq i32 %v, 0
  br i1 %cond, label %yes, label %no
yes:
  call void @g()
  ret void
no:
  ret void
}

declare void @g()
"""


@pytest.fixture
def all_kinds_ir() -> str:
    """Canonical tiny IR snippet exercising each currently supported EventKind."""
    return _ALL_KINDS_IR


@pytest.fixture
def double_ll_path() -> Path:
    """Path to canonical file-based ingestion fixture."""
    return Path("tests/ingest/testdata/double.ll")


@pytest.fixture
def double_ll_text(double_ll_path: Path) -> str:
    """Contents of canonical file-based ingestion fixture."""
    return double_ll_path.read_text(encoding="utf-8")


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Apply baseline markers by path to enable phased taxonomy adoption."""
    for item in items:
        nodeid = item.nodeid

        if nodeid.startswith("tests/ingest/") or nodeid.startswith("tests/transform/"):
            item.add_marker(pytest.mark.unit)

        if nodeid.startswith("tests/present/"):
            item.add_marker(pytest.mark.integration)

        if nodeid == "tests/present/test_exports.py" or nodeid.startswith(
            "tests/present/test_exports.py::"
        ):
            item.add_marker(pytest.mark.contract)

        if nodeid.startswith("tests/cli/") or nodeid.startswith("tests/test_pipeline.py"):
            item.add_marker(pytest.mark.integration)

        if nodeid.startswith("tests/test_entrypoints.py"):
            item.add_marker(pytest.mark.e2e)
