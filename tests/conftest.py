"""Shared pytest fixtures and baseline test taxonomy markers."""

from __future__ import annotations

from pathlib import Path

import pytest

from llvmanim.ingest.llvm_events import parse_ir_to_events
from llvmanim.transform.models import ProgramEventStream, SceneGraph
from llvmanim.transform.scene import build_scene_graph

_ALL_KINDS_IR = """
define void @f(ptr %p) {
entry:
  %x = alloca i32
  store i32 99, ptr %x
  %v = load i32, ptr %x
  %sum = add i32 %v, 1
  %cond = icmp eq i32 %v, 0
  %tmp = zext i1 %cond to i32
  br i1 %cond, label %yes, label %no
yes:
  call void @g()
  ret void
no:
  ret void
}

declare void @g()
"""

_BRANCH_IR = """
define void @f(ptr %p) {
entry:
  %x = alloca i32
  %cond = icmp eq i32 1, 1
  br i1 %cond, label %yes, label %no
yes:
  ret void
no:
  ret void
}
"""

_MINIMAL_IR = """
define i32 @f() {
entry:
  ret i32 0
}
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


@pytest.fixture
def minimal_stream() -> ProgramEventStream:
    """Pre-parsed stream from a minimal single-block IR function."""
    return parse_ir_to_events(_MINIMAL_IR)


@pytest.fixture
def branch_stream() -> ProgramEventStream:
    """Pre-parsed stream from a two-branch IR function (entry → yes/no)."""
    return parse_ir_to_events(_BRANCH_IR)


@pytest.fixture
def branch_graph(branch_stream: ProgramEventStream) -> SceneGraph:
    """Pre-built scene graph from branch_stream: 3 nodes, 2 edges."""
    return build_scene_graph(branch_stream)


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Apply baseline markers by path to enable phased taxonomy adoption."""
    for item in items:
        nodeid = item.nodeid

        if nodeid.startswith("tests/ingest/") or nodeid.startswith("tests/transform/"):
            item.add_marker(pytest.mark.unit)

        if nodeid.startswith("tests/render/"):
            item.add_marker(pytest.mark.integration)

        if nodeid == "tests/render/test_exports.py" or nodeid.startswith(
            "tests/render/test_exports.py::"
        ):
            item.add_marker(pytest.mark.contract)

        if nodeid.startswith("tests/cli/") or nodeid.startswith("tests/test_pipeline.py"):
            item.add_marker(pytest.mark.integration)

        if nodeid.startswith("tests/test_entrypoints.py"):
            item.add_marker(pytest.mark.e2e)
