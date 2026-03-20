"""Tests for analysis_metadata_io JSON import/export."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from llvmanim.ingest.analysis_metadata_io import (
    AnalysisMetadataIOError,
    load_analysis_metadata,
    save_analysis_metadata,
)
from llvmanim.transform.models import BlockMetadata

# ── load_analysis_metadata ────────────────────────────────────────


def test_load_valid_metadata(tmp_path: Path) -> None:
    data = {
        "version": 1,
        "source": "test.ll",
        "functions": [
            {
                "name": "main",
                "blocks": [
                    {
                        "id": "main::entry",
                        "idom": None,
                        "dom_depth": 0,
                        "is_loop_header": False,
                    },
                    {
                        "id": "main::loop",
                        "idom": "main::entry",
                        "dom_depth": 1,
                        "is_loop_header": True,
                        "loop_depth": 1,
                        "loop_id": "loop_0",
                        "is_backedge_target": True,
                    },
                ],
            }
        ],
    }
    p = tmp_path / "meta.json"
    p.write_text(json.dumps(data))

    result = load_analysis_metadata(p)

    assert len(result) == 2
    assert result["main::entry"] == BlockMetadata()
    assert result["main::loop"] == BlockMetadata(
        idom="main::entry",
        dom_depth=1,
        is_loop_header=True,
        loop_depth=1,
        loop_id="loop_0",
        is_backedge_target=True,
    )


def test_load_partial_metadata_domtree_only(tmp_path: Path) -> None:
    """Load metadata with only domtree fields — loop fields default."""
    data = {
        "version": 1,
        "source": "",
        "functions": [
            {
                "name": "f",
                "blocks": [
                    {"id": "f::entry", "idom": None, "dom_depth": 0},
                    {"id": "f::body", "idom": "f::entry", "dom_depth": 1},
                ],
            }
        ],
    }
    p = tmp_path / "meta.json"
    p.write_text(json.dumps(data))

    result = load_analysis_metadata(p)

    assert result["f::body"].idom == "f::entry"
    assert result["f::body"].dom_depth == 1
    assert result["f::body"].is_loop_header is False
    assert result["f::body"].loop_depth == 0


def test_load_partial_metadata_loop_only(tmp_path: Path) -> None:
    """Load metadata with only loop fields — domtree fields default."""
    data = {
        "version": 1,
        "source": "",
        "functions": [
            {
                "name": "f",
                "blocks": [
                    {"id": "f::header", "is_loop_header": True, "loop_depth": 1, "loop_id": "L0"},
                ],
            }
        ],
    }
    p = tmp_path / "meta.json"
    p.write_text(json.dumps(data))

    result = load_analysis_metadata(p)

    assert result["f::header"].idom is None
    assert result["f::header"].dom_depth == 0
    assert result["f::header"].is_loop_header is True
    assert result["f::header"].loop_depth == 1
    assert result["f::header"].loop_id == "L0"


def test_load_rejects_invalid_json(tmp_path: Path) -> None:
    p = tmp_path / "bad.json"
    p.write_text("not json")

    with pytest.raises(AnalysisMetadataIOError, match="Invalid JSON"):
        load_analysis_metadata(p)


def test_load_rejects_non_dict_root(tmp_path: Path) -> None:
    p = tmp_path / "bad.json"
    p.write_text(json.dumps([1, 2, 3]))

    with pytest.raises(AnalysisMetadataIOError, match="root must be a JSON object"):
        load_analysis_metadata(p)


def test_load_rejects_wrong_version(tmp_path: Path) -> None:
    p = tmp_path / "bad.json"
    p.write_text(json.dumps({"version": 99, "functions": []}))

    with pytest.raises(AnalysisMetadataIOError, match="Unsupported.*version"):
        load_analysis_metadata(p)


def test_load_rejects_missing_functions(tmp_path: Path) -> None:
    p = tmp_path / "bad.json"
    p.write_text(json.dumps({"version": 1}))

    with pytest.raises(AnalysisMetadataIOError, match="'functions' must be a list"):
        load_analysis_metadata(p)


def test_load_rejects_function_without_name(tmp_path: Path) -> None:
    p = tmp_path / "bad.json"
    p.write_text(json.dumps({"version": 1, "functions": [{"blocks": []}]}))

    with pytest.raises(AnalysisMetadataIOError, match="must have a 'name' field"):
        load_analysis_metadata(p)


def test_load_rejects_function_without_blocks_list(tmp_path: Path) -> None:
    p = tmp_path / "bad.json"
    p.write_text(json.dumps({"version": 1, "functions": [{"name": "f"}]}))

    with pytest.raises(AnalysisMetadataIOError, match="'blocks' must be a list"):
        load_analysis_metadata(p)


def test_load_rejects_block_without_id(tmp_path: Path) -> None:
    p = tmp_path / "bad.json"
    p.write_text(
        json.dumps(
            {"version": 1, "functions": [{"name": "f", "blocks": [{"name": "entry"}]}]}
        )
    )

    with pytest.raises(AnalysisMetadataIOError, match="must have an 'id' field"):
        load_analysis_metadata(p)


# ── save_analysis_metadata ────────────────────────────────────────


def test_save_and_load_round_trip(tmp_path: Path) -> None:
    original = {
        "main::entry": BlockMetadata(idom=None, dom_depth=0),
        "main::loop": BlockMetadata(
            idom="main::entry",
            dom_depth=1,
            is_loop_header=True,
            loop_depth=1,
            loop_id="L0",
            is_backedge_target=True,
        ),
        "main::exit": BlockMetadata(idom="main::entry", dom_depth=1),
    }

    p = tmp_path / "meta.json"
    save_analysis_metadata(original, p, source="test.ll")

    loaded = load_analysis_metadata(p)

    assert loaded == original


def test_save_omits_default_fields(tmp_path: Path) -> None:
    """Save should only serialize non-default fields to keep JSON compact."""
    meta = {"f::entry": BlockMetadata()}
    p = tmp_path / "meta.json"
    save_analysis_metadata(meta, p)

    data = json.loads(p.read_text())
    block = data["functions"][0]["blocks"][0]

    assert "idom" not in block
    assert "dom_depth" not in block
    assert "is_loop_header" not in block


def test_save_includes_source(tmp_path: Path) -> None:
    p = tmp_path / "meta.json"
    save_analysis_metadata({}, p, source="my_file.ll")

    data = json.loads(p.read_text())
    assert data["source"] == "my_file.ll"
    assert data["version"] == 1
