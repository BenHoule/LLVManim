"""Unit tests for derive_cfg_trace (transform.trace)."""

from __future__ import annotations

from llvmanim.transform.models import SceneEdge, SceneGraph, SceneNode
from llvmanim.transform.trace import derive_cfg_trace

# -- derive_cfg_trace ------------------------------------------------


def _loop_graph() -> SceneGraph:
    """Build a graph modelling double.ll's main: entry → while.cond ⇄ while.body → while.end."""
    return SceneGraph(
        nodes=[
            SceneNode(id="main::entry", label="entry", kind="cfg_block"),
            SceneNode(id="main::while.cond", label="while.cond", kind="cfg_block"),
            SceneNode(id="main::while.body", label="while.body", kind="cfg_block"),
            SceneNode(id="main::while.end", label="while.end", kind="cfg_block"),
        ],
        edges=[
            SceneEdge(source="main::entry", target="main::while.cond"),
            SceneEdge(source="main::while.cond", target="main::while.body", label="T"),
            SceneEdge(source="main::while.cond", target="main::while.end", label="F"),
            SceneEdge(source="main::while.body", target="main::while.cond"),
        ],
    )


def test_derive_cfg_trace_linear() -> None:
    """A simple entry → exit graph produces a 2-step trace."""
    graph = SceneGraph(
        nodes=[
            SceneNode(id="f::entry", label="entry", kind="cfg_block"),
            SceneNode(id="f::exit", label="exit", kind="cfg_block"),
        ],
        edges=[SceneEdge(source="f::entry", target="f::exit")],
    )
    overlay = derive_cfg_trace(graph, function="f")
    assert overlay.entry_order == ["f::entry", "f::exit"]
    assert overlay.visited_nodes == ["f::entry", "f::exit"]
    assert overlay.traversed_edges == [("f::entry", "f::exit")]
    assert overlay.termination_reason == "ret"


def test_derive_cfg_trace_loop_respects_max_iterations() -> None:
    graph = _loop_graph()
    overlay = derive_cfg_trace(graph, function="main", max_loop_iterations=3)

    body_visits = overlay.entry_order.count("main::while.body")
    assert body_visits == 3
    assert overlay.entry_order[-1] == "main::while.end"
    assert overlay.termination_reason == "ret"


def test_derive_cfg_trace_default_loop_iterations() -> None:
    graph = _loop_graph()
    overlay = derive_cfg_trace(graph, function="main")
    body_visits = overlay.entry_order.count("main::while.body")
    assert body_visits == 7  # default max_loop_iterations


def test_derive_cfg_trace_prefers_true_branch() -> None:
    """When a conditional branch has T and F labels, T is taken first."""
    graph = _loop_graph()
    overlay = derive_cfg_trace(graph, function="main", max_loop_iterations=1)

    cond_idx = overlay.entry_order.index("main::while.cond")
    assert overlay.entry_order[cond_idx + 1] == "main::while.body"


def test_derive_cfg_trace_visited_nodes_are_unique() -> None:
    graph = _loop_graph()
    overlay = derive_cfg_trace(graph, function="main", max_loop_iterations=3)
    assert len(overlay.visited_nodes) == len(set(overlay.visited_nodes))


def test_derive_cfg_trace_unknown_function_returns_empty() -> None:
    graph = _loop_graph()
    overlay = derive_cfg_trace(graph, function="nonexistent")
    assert overlay.entry_order == []
    assert overlay.visited_nodes == []
