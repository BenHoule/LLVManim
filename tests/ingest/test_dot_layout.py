"""Tests for dot_layout: DOT file → structured layout geometry."""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from llvmanim.ingest.dot_layout import (
    DotLayout,
    DotLayoutError,
    _extract_block_name,
    _parse_json_layout,
    _parse_spline_points,
    compute_dot_layout,
)

# -- _extract_block_name ------------------------------------------


def test_extract_block_name_from_record_label() -> None:
    assert _extract_block_name("{entry:\\l|  %retval = alloca\\l}") == "entry"


def test_extract_block_name_with_dot() -> None:
    assert _extract_block_name("{while.cond:\\l|  br i1 %cmp\\l}") == "while.cond"


def test_extract_block_name_plain() -> None:
    assert _extract_block_name("entry:") == "entry"


def test_extract_block_name_fallback() -> None:
    """Unrecognized formats still return something reasonable."""
    result = _extract_block_name("{unknown}")
    assert isinstance(result, str)
    assert len(result) > 0


# -- _parse_spline_points -----------------------------------------


def test_parse_spline_simple() -> None:
    points = _parse_spline_points("e,100,50 10,20 30,40 60,45 90,48")
    assert len(points) == 5
    assert points[0] == (10.0, 20.0)
    assert points[-1] == (100.0, 50.0)


def test_parse_spline_no_endpoint() -> None:
    points = _parse_spline_points("10,20 30,40 60,45")
    assert len(points) == 3
    assert points[0] == (10.0, 20.0)
    assert points[-1] == (60.0, 45.0)


def test_parse_spline_with_start_prefix() -> None:
    """Start prefix (s,...) is skipped; only data points and endpoint kept."""
    points = _parse_spline_points("s,5,10 e,100,50 10,20 30,40")
    assert len(points) == 3
    assert points[0] == (10.0, 20.0)
    assert points[-1] == (100.0, 50.0)


def test_parse_spline_empty() -> None:
    assert _parse_spline_points("") == []


# -- _parse_json_layout -------------------------------------------

_SAMPLE_JSON: dict = {
    "bb": "0,0,400,300",
    "objects": [
        {
            "_gvid": 0,
            "name": "entry",
            "label": "{entry:\\l|  ret i32 0\\l}",
            "pos": "200,250",
            "width": "3.0",
            "height": "1.5",
        },
        {
            "_gvid": 1,
            "name": "while.cond",
            "label": "{while.cond:\\l|  br i1 %cmp\\l}",
            "pos": "200,100",
            "width": "4.0",
            "height": "1.0",
        },
    ],
    "edges": [
        {
            "tail": 0,
            "head": 1,
            "pos": "e,200,120 200,230 200,200 200,170 200,140",
            "tailport": "",
        },
    ],
}


def test_parse_json_layout_nodes() -> None:
    layout = _parse_json_layout(_SAMPLE_JSON)
    assert "entry" in layout.nodes
    assert "while.cond" in layout.nodes
    assert layout.nodes["entry"].center_x == 200.0
    assert layout.nodes["entry"].center_y == 250.0


def test_parse_json_layout_node_dimensions() -> None:
    layout = _parse_json_layout(_SAMPLE_JSON)
    assert layout.nodes["entry"].width == pytest.approx(3.0 * 72)
    assert layout.nodes["entry"].height == pytest.approx(1.5 * 72)


def test_parse_json_layout_bounding_box() -> None:
    layout = _parse_json_layout(_SAMPLE_JSON)
    assert layout.bounding_box == (0.0, 0.0, 400.0, 300.0)


def test_parse_json_layout_edges() -> None:
    layout = _parse_json_layout(_SAMPLE_JSON)
    assert len(layout.edges) == 1
    assert layout.edges[0].source == "entry"
    assert layout.edges[0].target == "while.cond"


def test_parse_json_layout_edge_spline_points() -> None:
    layout = _parse_json_layout(_SAMPLE_JSON)
    points = layout.edges[0].spline_points
    assert len(points) == 5
    assert points[-1] == (200.0, 120.0)


def test_parse_json_layout_edge_labels_from_tailport() -> None:
    data = dict(_SAMPLE_JSON)
    data["edges"] = [
        {
            "tail": 0,
            "head": 1,
            "pos": "e,200,120 200,230 200,200 200,170 200,140",
            "tailport": "s0",
        },
        {
            "tail": 0,
            "head": 1,
            "pos": "e,200,120 200,230 200,200 200,170 200,140",
            "tailport": "s1",
        },
    ]
    layout = _parse_json_layout(data)
    assert layout.edges[0].label == "T"
    assert layout.edges[1].label == "F"


# -- compute_dot_layout -------------------------------------------


def test_compute_dot_layout_file_not_found() -> None:
    with pytest.raises(DotLayoutError, match="not found"):
        compute_dot_layout("/nonexistent/path.dot")


def test_compute_dot_layout_dot_not_installed(tmp_path: Path) -> None:
    dot_file = tmp_path / "test.dot"
    dot_file.write_text("digraph { a -> b }")

    with (
        patch("llvmanim.ingest.dot_layout.subprocess.run", side_effect=FileNotFoundError),
        pytest.raises(DotLayoutError, match="dot.*not found"),
    ):
        compute_dot_layout(dot_file)


def test_compute_dot_layout_dot_fails(tmp_path: Path) -> None:
    dot_file = tmp_path / "test.dot"
    dot_file.write_text("digraph { a -> b }")

    with (
        patch("llvmanim.ingest.dot_layout.find_tool", return_value="/usr/bin/dot"),
        patch(
            "llvmanim.ingest.dot_layout.subprocess.run",
            side_effect=subprocess.CalledProcessError(1, ["dot"], stderr="bad input"),
        ),
        pytest.raises(DotLayoutError, match="exited with code 1"),
    ):
        compute_dot_layout(dot_file)


def test_compute_dot_layout_timeout(tmp_path: Path) -> None:
    dot_file = tmp_path / "test.dot"
    dot_file.write_text("digraph { a -> b }")

    with (
        patch("llvmanim.ingest.dot_layout.find_tool", return_value="/usr/bin/dot"),
        patch(
            "llvmanim.ingest.dot_layout.subprocess.run",
            side_effect=subprocess.TimeoutExpired(["dot"], 30),
        ),
        pytest.raises(DotLayoutError, match="timed out"),
    ):
        compute_dot_layout(dot_file)


def test_compute_dot_layout_bad_json(tmp_path: Path) -> None:
    dot_file = tmp_path / "test.dot"
    dot_file.write_text("digraph { a -> b }")

    mock_result = subprocess.CompletedProcess(["dot"], 0, stdout="not json", stderr="")
    with (
        patch("llvmanim.ingest.dot_layout.find_tool", return_value="/usr/bin/dot"),
        patch("llvmanim.ingest.dot_layout.subprocess.run", return_value=mock_result),
        pytest.raises(DotLayoutError, match="parse"),
    ):
        compute_dot_layout(dot_file)


def test_compute_dot_layout_integration(tmp_path: Path) -> None:
    """Integration test: run real dot on a simple graph if Graphviz is installed."""
    import shutil

    if shutil.which("dot") is None:
        pytest.skip("Graphviz 'dot' not installed")

    dot_file = tmp_path / "simple.dot"
    dot_file.write_text(
        'digraph { rankdir=TB; a [label="a"]; b [label="b"]; c [label="c"]; a -> b; b -> c; }'
    )

    layout = compute_dot_layout(dot_file)

    assert isinstance(layout, DotLayout)
    assert len(layout.nodes) == 3
    assert len(layout.edges) == 2
    assert "a" in layout.nodes
    assert "b" in layout.nodes
    assert "c" in layout.nodes
