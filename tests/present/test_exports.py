"""Tests for Graphviz and JSON export helpers."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

from llvmanim.ingest import parse_ir_to_events
from llvmanim.present import export_cfg_dot, export_scene_graph_json
from llvmanim.present.graphviz_export import _gv_id, export_cfg_png
from llvmanim.transform.models import SceneGraph
from llvmanim.transform.scene import build_scene_graph


def _build_graph() -> SceneGraph:
    """Return a small two-branch SceneGraph for use across export tests."""
    stream = parse_ir_to_events("""
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
    """)
    return build_scene_graph(stream)


def test_export_scene_graph_json(tmp_path: Path) -> None:
    graph = _build_graph()
    output = tmp_path / "scene_graph.json"

    export_scene_graph_json(graph, output)

    assert output.exists()
    text = output.read_text(encoding="utf-8")
    assert "f::entry" in text
    assert "f::yes" in text
    assert "f::no" in text


def test_export_cfg_dot(tmp_path: Path) -> None:
    graph = _build_graph()
    output = tmp_path / "cfg.dot"

    export_cfg_dot(graph, output)

    assert output.exists()
    text = output.read_text(encoding="utf-8")
    assert '"f::entry" -> "f::yes"' in text
    assert '"f::entry" -> "f::no"' in text


def test_gv_id_sanitizes_special_characters() -> None:
    """_gv_id replaces characters that are invalid in graphviz IDs."""
    assert _gv_id("main::while.cond") == "main__while_cond"
    assert _gv_id("f::entry") == "f__entry"
    assert _gv_id("already_safe") == "already_safe"


def test_export_cfg_png_returns_false_when_graphviz_unavailable(tmp_path: Path) -> None:
    """export_cfg_png returns False gracefully when the graphviz package is not installed."""
    graph = _build_graph()
    with patch.dict(sys.modules, {"graphviz": None, "graphviz.backend": None}):
        result = export_cfg_png(graph, tmp_path / "cfg")
    assert result is False


def test_export_cfg_png_returns_true_when_graphviz_available(tmp_path: Path) -> None:
    """export_cfg_png calls graphviz and returns True when the package is present."""
    graph = _build_graph()

    mock_dot = MagicMock()
    mock_gv = MagicMock()
    mock_gv.Digraph.return_value = mock_dot
    mock_gv_backend = MagicMock()
    mock_gv_backend.CalledProcessError = type("CalledProcessError", (Exception,), {})
    mock_gv_backend.ExecutableNotFound = type("ExecutableNotFound", (Exception,), {})

    with patch.dict(sys.modules, {"graphviz": mock_gv, "graphviz.backend": mock_gv_backend}):
        result = export_cfg_png(graph, tmp_path / "cfg")

    assert result is True
    mock_dot.render.assert_called_once()


def test_export_cfg_png_returns_false_when_dot_executable_missing(tmp_path: Path) -> None:
    """export_cfg_png returns False when the dot executable is not found."""
    from graphviz.backend.execute import ExecutableNotFound

    graph = _build_graph()
    with patch("graphviz.Digraph.render", side_effect=ExecutableNotFound(["dot"])):
        result = export_cfg_png(graph, tmp_path / "cfg")
    assert result is False
