"""Tests for cfg_edge_io JSON import/export."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from llvmanim.ingest.cfg_edge_io import CFGEdgeIOError, load_cfg_edges, save_cfg_edges
from llvmanim.transform.models import CFGEdge

# ── load_cfg_edges ────────────────────────────────────────────────


def test_load_valid_edges(tmp_path: Path) -> None:
    data = {
        "version": 1,
        "source": "test.ll",
        "functions": [
            {
                "name": "main",
                "blocks": [
                    {"name": "entry", "id": "main::entry", "successors": ["main::exit"]},
                    {"name": "exit", "id": "main::exit", "successors": []},
                ],
            }
        ],
    }
    p = tmp_path / "cfg.json"
    p.write_text(json.dumps(data))

    edges = load_cfg_edges(p)

    assert len(edges) == 1
    assert edges[0] == CFGEdge(source="main::entry", target="main::exit")


def test_load_deduplicates_edges(tmp_path: Path) -> None:
    data = {
        "version": 1,
        "source": "",
        "functions": [
            {
                "name": "f",
                "blocks": [
                    {
                        "name": "a",
                        "id": "f::a",
                        "successors": ["f::b", "f::b"],  # duplicate
                    },
                ],
            }
        ],
    }
    p = tmp_path / "cfg.json"
    p.write_text(json.dumps(data))

    edges = load_cfg_edges(p)
    assert len(edges) == 1


def test_load_rejects_bad_json(tmp_path: Path) -> None:
    p = tmp_path / "bad.json"
    p.write_text("{not valid json")

    with pytest.raises(CFGEdgeIOError, match="Invalid JSON"):
        load_cfg_edges(p)


def test_load_rejects_non_object(tmp_path: Path) -> None:
    p = tmp_path / "bad.json"
    p.write_text(json.dumps([1, 2, 3]))

    with pytest.raises(CFGEdgeIOError, match="root must be a JSON object"):
        load_cfg_edges(p)


def test_load_rejects_wrong_version(tmp_path: Path) -> None:
    p = tmp_path / "bad.json"
    p.write_text(json.dumps({"version": 99, "functions": []}))

    with pytest.raises(CFGEdgeIOError, match="Unsupported CFG edge file version"):
        load_cfg_edges(p)


def test_load_rejects_missing_version(tmp_path: Path) -> None:
    p = tmp_path / "bad.json"
    p.write_text(json.dumps({"functions": []}))

    with pytest.raises(CFGEdgeIOError, match="Unsupported CFG edge file version"):
        load_cfg_edges(p)


def test_load_rejects_missing_functions(tmp_path: Path) -> None:
    p = tmp_path / "bad.json"
    p.write_text(json.dumps({"version": 1}))

    with pytest.raises(CFGEdgeIOError, match="'functions' must be a list"):
        load_cfg_edges(p)


def test_load_rejects_function_without_name(tmp_path: Path) -> None:
    p = tmp_path / "bad.json"
    p.write_text(json.dumps({"version": 1, "functions": [{"blocks": []}]}))

    with pytest.raises(CFGEdgeIOError, match="must have a 'name' field"):
        load_cfg_edges(p)


def test_load_rejects_block_without_id(tmp_path: Path) -> None:
    p = tmp_path / "bad.json"
    p.write_text(
        json.dumps(
            {
                "version": 1,
                "functions": [{"name": "f", "blocks": [{"name": "b"}]}],
            }
        )
    )

    with pytest.raises(CFGEdgeIOError, match="must have an 'id' field"):
        load_cfg_edges(p)


# ── save_cfg_edges ────────────────────────────────────────────────


def test_save_produces_valid_json(tmp_path: Path) -> None:
    edges = [
        CFGEdge(source="main::entry", target="main::then"),
        CFGEdge(source="main::entry", target="main::else"),
        CFGEdge(source="main::then", target="main::exit"),
        CFGEdge(source="main::else", target="main::exit"),
    ]
    p = tmp_path / "out.json"
    save_cfg_edges(edges, p, source="test.ll")

    data = json.loads(p.read_text())
    assert data["version"] == 1
    assert data["source"] == "test.ll"
    assert len(data["functions"]) == 1
    assert data["functions"][0]["name"] == "main"


def test_save_round_trip(tmp_path: Path) -> None:
    original = [
        CFGEdge(source="f::a", target="f::b"),
        CFGEdge(source="f::b", target="f::c"),
        CFGEdge(source="f::a", target="f::c"),
    ]
    p = tmp_path / "rt.json"
    save_cfg_edges(original, p)

    loaded = load_cfg_edges(p)
    assert set((e.source, e.target) for e in loaded) == set(
        (e.source, e.target) for e in original
    )


def test_save_multi_function(tmp_path: Path) -> None:
    edges = [
        CFGEdge(source="foo::entry", target="foo::exit"),
        CFGEdge(source="bar::entry", target="bar::exit"),
    ]
    p = tmp_path / "multi.json"
    save_cfg_edges(edges, p)

    data = json.loads(p.read_text())
    func_names = [f["name"] for f in data["functions"]]
    assert "foo" in func_names
    assert "bar" in func_names


def test_save_predecessors_populated(tmp_path: Path) -> None:
    edges = [
        CFGEdge(source="f::a", target="f::b"),
        CFGEdge(source="f::c", target="f::b"),
    ]
    p = tmp_path / "pred.json"
    save_cfg_edges(edges, p)

    data = json.loads(p.read_text())
    blocks = {b["name"]: b for b in data["functions"][0]["blocks"]}
    assert set(blocks["b"]["predecessors"]) == {"f::a", "f::c"}
