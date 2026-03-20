"""Tests for Graphviz and JSON export helpers."""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

from llvmanim.ingest import parse_ir_to_events
from llvmanim.present import export_cfg_dot, export_scene_graph_json
from llvmanim.present.graphviz_export import _gv_id, export_cfg_png
from llvmanim.transform.models import SceneGraph, TraceOverlay
from llvmanim.transform.scene import build_scene_graph


def test_export_scene_graph_json(tmp_path: Path, branch_graph: SceneGraph) -> None:
    output = tmp_path / "scene_graph.json"

    export_scene_graph_json(branch_graph, output)

    assert output.exists()
    text = output.read_text(encoding="utf-8")
    assert "f::entry" in text
    assert "f::yes" in text
    assert "f::no" in text


def test_export_scene_graph_json_has_expected_top_level_shape(tmp_path: Path, branch_graph: SceneGraph) -> None:
    """JSON export should include top-level nodes/edges arrays with stable keys."""
    output = tmp_path / "scene_graph.json"

    export_scene_graph_json(branch_graph, output)

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert set(payload) == {"nodes", "edges"}
    assert isinstance(payload["nodes"], list)
    assert isinstance(payload["edges"], list)
    assert len(payload["nodes"]) == 3
    assert len(payload["edges"]) == 2


def test_export_scene_graph_json_includes_edge_labels(tmp_path: Path, branch_graph: SceneGraph) -> None:
    """JSON edge entries should include T/F labels from conditional branches."""
    output = tmp_path / "scene_graph.json"
    export_scene_graph_json(branch_graph, output)
    payload = json.loads(output.read_text(encoding="utf-8"))
    edge_labels = {e["label"] for e in payload["edges"]}
    assert edge_labels == {"T", "F"}


def test_export_scene_graph_json_preserves_event_operands_and_debug_line(tmp_path: Path) -> None:
    """Event payload should preserve operand lists and debug_line nullability."""
    stream = parse_ir_to_events("""
        define void @f() {
        entry:
          %x = alloca i32
          store i32 7, ptr %x
          %v = load i32, ptr %x
          ret void
        }
    """)
    graph = build_scene_graph(stream)
    output = tmp_path / "scene_graph.json"

    export_scene_graph_json(graph, output)

    payload = json.loads(output.read_text(encoding="utf-8"))
    entry = next(node for node in payload["nodes"] if node["id"] == "f::entry")
    events = entry["block"]["events"]

    assert len(events) >= 4
    assert all("operands" in event for event in events)
    assert all(isinstance(event["operands"], list) for event in events)
    assert all("debug_line" in event for event in events)
    assert all(event["debug_line"] is None for event in events)


def test_export_scene_graph_json_accepts_string_output_path(tmp_path: Path, branch_graph: SceneGraph) -> None:
    """export_scene_graph_json should accept both Path and string paths."""
    output = tmp_path / "scene_graph_via_string.json"

    export_scene_graph_json(branch_graph, str(output))

    assert output.exists()


def test_export_cfg_dot(tmp_path: Path, branch_graph: SceneGraph) -> None:
    output = tmp_path / "cfg.dot"

    export_cfg_dot(branch_graph, output)

    assert output.exists()
    text = output.read_text(encoding="utf-8")
    assert '"f::entry" -> "f::yes"' in text
    assert '"f::entry" -> "f::no"' in text


def test_gv_id_sanitizes_special_characters() -> None:
    """_gv_id replaces characters that are invalid in graphviz IDs."""
    assert _gv_id("main::while.cond") == "main__while_cond"
    assert _gv_id("f::entry") == "f__entry"
    assert _gv_id("already_safe") == "already_safe"


def test_export_cfg_png_returns_false_when_graphviz_unavailable(tmp_path: Path, branch_graph: SceneGraph) -> None:
    """export_cfg_png returns False gracefully when the graphviz package is not installed."""
    with patch.dict(sys.modules, {"graphviz": None, "graphviz.backend": None}):
        result = export_cfg_png(branch_graph, tmp_path / "cfg")
    assert result is False


# ── Overlay-aware Graphviz export ─────────────────────────────────


def _branch_graph_with_overlay(branch_graph: SceneGraph) -> SceneGraph:
    """Return branch_graph with an overlay marking entry→yes as traversed."""
    branch_graph.overlay = TraceOverlay(
        visited_nodes=["f::entry", "f::yes"],
        traversed_edges=[("f::entry", "f::yes")],
        entry_order=["f::entry", "f::yes"],
        termination_reason="ret",
    )
    return branch_graph


def test_export_dot_overlay_highlights_visited_nodes(tmp_path: Path, branch_graph: SceneGraph) -> None:
    """Visited nodes receive a green fill when overlay is present."""
    graph = _branch_graph_with_overlay(branch_graph)
    output = tmp_path / "cfg.dot"

    export_cfg_dot(graph, output)

    text = output.read_text(encoding="utf-8")
    # Visited nodes get green fill
    assert '#d4edda' in text
    # Unvisited node (f::no) gets gray fill
    assert '#e0e0e0' in text


def test_export_dot_overlay_highlights_traversed_edges(tmp_path: Path, branch_graph: SceneGraph) -> None:
    """Traversed edges get bold/colored styling; others get dashed gray."""
    graph = _branch_graph_with_overlay(branch_graph)
    output = tmp_path / "cfg.dot"

    export_cfg_dot(graph, output)

    text = output.read_text(encoding="utf-8")
    # Traversed edge entry→yes has blue styling
    assert '#0056b3' in text
    assert 'penwidth=2.0' in text
    # Non-traversed edge entry→no has gray dashed styling
    assert '#cccccc' in text
    assert 'dashed' in text


def test_export_dot_no_overlay_is_plain(tmp_path: Path, branch_graph: SceneGraph) -> None:
    """Without overlay, DOT has no fill or edge style attributes."""
    output = tmp_path / "cfg.dot"

    export_cfg_dot(branch_graph, output)

    text = output.read_text(encoding="utf-8")
    assert 'fillcolor' not in text
    assert 'penwidth' not in text
    assert 'dashed' not in text


def test_export_dot_overlay_preserves_all_nodes_and_edges(tmp_path: Path, branch_graph: SceneGraph) -> None:
    """Overlay never removes base graph structure; all 3 nodes and 2 edges remain."""
    graph = _branch_graph_with_overlay(branch_graph)
    output = tmp_path / "cfg.dot"

    export_cfg_dot(graph, output)

    text = output.read_text(encoding="utf-8")
    assert '"f::entry"' in text
    assert '"f::yes"' in text
    assert '"f::no"' in text
    assert '"f::entry" -> "f::yes"' in text
    assert '"f::entry" -> "f::no"' in text


def test_export_cfg_png_returns_true_when_graphviz_available(tmp_path: Path, branch_graph: SceneGraph) -> None:
    """export_cfg_png calls graphviz and returns True when the package is present."""
    graph = branch_graph

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


def test_export_cfg_png_returns_false_when_dot_executable_missing(tmp_path: Path, branch_graph: SceneGraph) -> None:
    """export_cfg_png returns False when the dot executable is not found."""
    from graphviz.backend.execute import ExecutableNotFound

    with patch("graphviz.Digraph.render", side_effect=ExecutableNotFound(["dot"])):
        result = export_cfg_png(branch_graph, tmp_path / "cfg")
    assert result is False


def test_export_cfg_png_returns_false_when_dot_process_fails(tmp_path: Path, branch_graph: SceneGraph) -> None:
    """export_cfg_png returns False when graphviz render process returns an error."""
    from graphviz.backend.execute import CalledProcessError

    with patch("graphviz.Digraph.render", side_effect=CalledProcessError(1, ["dot"])):
        result = export_cfg_png(branch_graph, tmp_path / "cfg")
    assert result is False


def test_export_cfg_png_uses_sanitized_ids_for_nodes_and_edges(tmp_path: Path, branch_graph: SceneGraph) -> None:
    """export_cfg_png should pass Graphviz-safe IDs to dot.node() and dot.edge()."""
    graph = branch_graph

    mock_dot = MagicMock()
    mock_gv = MagicMock()
    mock_gv.Digraph.return_value = mock_dot
    mock_gv_backend = MagicMock()
    mock_gv_backend.CalledProcessError = type("CalledProcessError", (Exception,), {})
    mock_gv_backend.ExecutableNotFound = type("ExecutableNotFound", (Exception,), {})

    with patch.dict(sys.modules, {"graphviz": mock_gv, "graphviz.backend": mock_gv_backend}):
        result = export_cfg_png(graph, tmp_path / "cfg")

    assert result is True

    node_ids = {call.args[0] for call in mock_dot.node.call_args_list}
    edge_pairs = {(call.args[0], call.args[1]) for call in mock_dot.edge.call_args_list}

    assert "f__entry" in node_ids
    assert "f__yes" in node_ids
    assert "f__no" in node_ids
    assert ("f__entry", "f__yes") in edge_pairs
    assert ("f__entry", "f__no") in edge_pairs


# ── T/F edge labels in DOT export ─────────────────────────────────


def test_export_dot_includes_tf_edge_labels(tmp_path: Path, branch_graph: SceneGraph) -> None:
    """DOT export should include T/F labels on conditional branch edges."""
    output = tmp_path / "cfg.dot"
    export_cfg_dot(branch_graph, output)
    text = output.read_text(encoding="utf-8")
    assert 'label="T"' in text
    assert 'label="F"' in text


def test_export_dot_overlay_includes_tf_labels(tmp_path: Path, branch_graph: SceneGraph) -> None:
    """T/F labels should also appear when overlay styling is active."""
    branch_graph.overlay = TraceOverlay(
        visited_nodes=["f::entry", "f::yes"],
        traversed_edges=[("f::entry", "f::yes")],
        entry_order=["f::entry", "f::yes"],
        termination_reason="ret",
    )
    output = tmp_path / "cfg.dot"
    export_cfg_dot(branch_graph, output)
    text = output.read_text(encoding="utf-8")
    assert 'label="T"' in text
    assert 'label="F"' in text
