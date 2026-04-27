"""Tests for trace_io JSON import/export."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from llvmanim.ingest.trace_io import TraceIOError, load_trace, save_trace
from llvmanim.transform.models import TraceOverlay

# -- load_trace ----------------------------------------------------


def test_load_valid_trace(tmp_path: Path) -> None:
    data = {
        "version": 1,
        "source": "test.ll",
        "entry_order": ["f::a", "f::b", "f::c"],
        "visited_nodes": ["f::a", "f::b", "f::c"],
        "traversed_edges": [["f::a", "f::b"], ["f::b", "f::c"]],
        "termination_reason": "ret",
    }
    p = tmp_path / "trace.json"
    p.write_text(json.dumps(data))

    overlay = load_trace(p)

    assert overlay.entry_order == ["f::a", "f::b", "f::c"]
    assert overlay.visited_nodes == ["f::a", "f::b", "f::c"]
    assert overlay.traversed_edges == [("f::a", "f::b"), ("f::b", "f::c")]
    assert overlay.termination_reason == "ret"


def test_load_derives_visited_nodes_when_absent(tmp_path: Path) -> None:
    """visited_nodes is derived from entry_order when not in JSON."""
    data = {
        "version": 1,
        "source": "",
        "entry_order": ["f::a", "f::b", "f::a", "f::b", "f::c"],
        "traversed_edges": [],
        "termination_reason": "",
    }
    p = tmp_path / "trace.json"
    p.write_text(json.dumps(data))

    overlay = load_trace(p)

    assert overlay.visited_nodes == ["f::a", "f::b", "f::c"]


def test_load_derives_traversed_edges_when_absent(tmp_path: Path) -> None:
    """traversed_edges derived from consecutive entry_order pairs."""
    data = {
        "version": 1,
        "source": "",
        "entry_order": ["f::a", "f::b", "f::a", "f::c"],
        "termination_reason": "",
    }
    p = tmp_path / "trace.json"
    p.write_text(json.dumps(data))

    overlay = load_trace(p)

    assert overlay.traversed_edges == [("f::a", "f::b"), ("f::b", "f::a"), ("f::a", "f::c")]


def test_load_deduplicates_traversed_edges(tmp_path: Path) -> None:
    data = {
        "version": 1,
        "source": "",
        "entry_order": [],
        "traversed_edges": [["f::a", "f::b"], ["f::a", "f::b"]],
        "termination_reason": "",
    }
    p = tmp_path / "trace.json"
    p.write_text(json.dumps(data))

    overlay = load_trace(p)

    assert overlay.traversed_edges == [("f::a", "f::b")]


def test_load_rejects_bad_json(tmp_path: Path) -> None:
    p = tmp_path / "bad.json"
    p.write_text("{not valid")

    with pytest.raises(TraceIOError, match="Invalid JSON"):
        load_trace(p)


def test_load_rejects_non_object(tmp_path: Path) -> None:
    p = tmp_path / "bad.json"
    p.write_text(json.dumps([1, 2, 3]))

    with pytest.raises(TraceIOError, match="root must be a JSON object"):
        load_trace(p)


def test_load_rejects_wrong_version(tmp_path: Path) -> None:
    p = tmp_path / "bad.json"
    p.write_text(json.dumps({"version": 99, "entry_order": []}))

    with pytest.raises(TraceIOError, match="Unsupported trace file version"):
        load_trace(p)


def test_load_rejects_missing_version(tmp_path: Path) -> None:
    p = tmp_path / "bad.json"
    p.write_text(json.dumps({"entry_order": []}))

    with pytest.raises(TraceIOError, match="Unsupported trace file version"):
        load_trace(p)


def test_load_rejects_missing_entry_order(tmp_path: Path) -> None:
    p = tmp_path / "bad.json"
    p.write_text(json.dumps({"version": 1}))

    with pytest.raises(TraceIOError, match="'entry_order' must be a list"):
        load_trace(p)


def test_load_rejects_entry_order_not_list(tmp_path: Path) -> None:
    p = tmp_path / "bad.json"
    p.write_text(json.dumps({"version": 1, "entry_order": "not-a-list"}))

    with pytest.raises(TraceIOError, match="'entry_order' must be a list"):
        load_trace(p)


def test_load_rejects_visited_nodes_not_list(tmp_path: Path) -> None:
    p = tmp_path / "bad.json"
    p.write_text(json.dumps({"version": 1, "entry_order": [], "visited_nodes": "bad"}))

    with pytest.raises(TraceIOError, match="'visited_nodes' must be a list"):
        load_trace(p)


def test_load_rejects_traversed_edges_not_list(tmp_path: Path) -> None:
    p = tmp_path / "bad.json"
    p.write_text(json.dumps({"version": 1, "entry_order": [], "traversed_edges": "bad"}))

    with pytest.raises(TraceIOError, match="'traversed_edges' must be a list"):
        load_trace(p)


def test_load_rejects_malformed_edge_pair(tmp_path: Path) -> None:
    p = tmp_path / "bad.json"
    p.write_text(json.dumps({"version": 1, "entry_order": [], "traversed_edges": [["a"]]}))

    with pytest.raises(TraceIOError, match="must be a \\[source, target\\] pair"):
        load_trace(p)


def test_load_rejects_non_string_termination_reason(tmp_path: Path) -> None:
    p = tmp_path / "bad.json"
    p.write_text(json.dumps({"version": 1, "entry_order": [], "termination_reason": 42}))

    with pytest.raises(TraceIOError, match="'termination_reason' must be a string"):
        load_trace(p)


def test_load_defaults_termination_reason_to_empty(tmp_path: Path) -> None:
    data = {"version": 1, "source": "", "entry_order": ["f::a"]}
    p = tmp_path / "trace.json"
    p.write_text(json.dumps(data))

    overlay = load_trace(p)

    assert overlay.termination_reason == ""


# -- save_trace ----------------------------------------------------


def test_save_produces_valid_json(tmp_path: Path) -> None:
    overlay = TraceOverlay(
        visited_nodes=["f::a", "f::b"],
        traversed_edges=[("f::a", "f::b")],
        entry_order=["f::a", "f::b"],
        termination_reason="ret",
    )
    p = tmp_path / "out.json"
    save_trace(overlay, p, source="test.ll")

    data = json.loads(p.read_text())
    assert data["version"] == 1
    assert data["source"] == "test.ll"
    assert data["entry_order"] == ["f::a", "f::b"]
    assert data["traversed_edges"] == [["f::a", "f::b"]]
    assert data["termination_reason"] == "ret"


def test_save_round_trip(tmp_path: Path) -> None:
    original = TraceOverlay(
        visited_nodes=["f::a", "f::b", "f::c"],
        traversed_edges=[("f::a", "f::b"), ("f::b", "f::c"), ("f::b", "f::a")],
        entry_order=["f::a", "f::b", "f::c", "f::b", "f::a"],
        termination_reason="ret",
    )
    p = tmp_path / "rt.json"
    save_trace(original, p)

    loaded = load_trace(p)

    assert loaded.entry_order == original.entry_order
    assert loaded.visited_nodes == original.visited_nodes
    assert set(loaded.traversed_edges) == set(original.traversed_edges)
    assert loaded.termination_reason == original.termination_reason


def test_load_double_trace_fixture() -> None:
    """Load the hand-crafted double.c trace fixture."""
    fixture = Path(__file__).parent / "testdata" / "double_trace.json"
    overlay = load_trace(fixture)

    assert "main::entry" in overlay.visited_nodes
    assert "main::while.cond" in overlay.visited_nodes
    assert "main::while.body" in overlay.visited_nodes
    assert "main::while.end" in overlay.visited_nodes
    assert overlay.entry_order[0] == "main::entry"
    assert overlay.entry_order[-1] == "main::while.end"
    assert overlay.termination_reason == "ret"
    # 7 loop iterations: entry + 8 cond + 7 body + end = 17 entries
    assert len(overlay.entry_order) == 17
