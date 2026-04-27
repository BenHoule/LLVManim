"""Tests for cfg_animation_scene helpers: _CoordMapper, _block_summary, _build_block_mob, _build_edge_mob."""

from __future__ import annotations

from llvmanim.ingest.dot_layout import DotEdgeLayout, DotLayout, DotNodeLayout
from llvmanim.render.cfg_animation_scene import (
    _block_summary,
    _build_block_mob,
    _build_edge_mob,
    _CoordMapper,
)
from llvmanim.transform.models import (
    CFGBlock,
    EventKind,
    IREvent,
    SceneEdge,
    SceneGraph,
    SceneNode,
)


def _event(fn: str, block: str, opcode: str, text: str = "", kind: EventKind = "other") -> IREvent:
    return IREvent(
        function_name=fn,
        block_name=block,
        opcode=opcode,
        text=text,
        kind=kind,
        index_in_function=0,
        debug_line=None,
    )


def _cfg_node(block: CFGBlock, hint: str = "highlight_block") -> SceneNode:
    """Create a SceneNode from a CFGBlock using a properties-based shape."""
    return SceneNode(
        id=block.id,
        label=block.name,
        kind="cfg_block",
        properties={
            "block_name": block.name,
            "function_name": block.function_name,
            "role": block.role,
            "terminator_opcode": block.terminator_opcode,
            "events": block.events,
            "memory_ops": block.memory_ops,
            "indegree": block.indegree,
            "outdegree": block.outdegree,
        },
        animation_hint=hint,
    )


def _simple_graph() -> SceneGraph:
    """Build a 2-node graph for testing."""
    entry_block = CFGBlock(
        id="f::entry",
        name="entry",
        function_name="f",
        events=[
            _event("f", "entry", "alloca", "%x = alloca i32", "alloca"),
            _event("f", "entry", "br", "br label %exit", "br"),
        ],
        terminator_opcode="br",
        role="entry",
    )
    exit_block = CFGBlock(
        id="f::exit",
        name="exit",
        function_name="f",
        events=[_event("f", "exit", "ret", "ret i32 0", "ret")],
        terminator_opcode="ret",
        role="exit",
    )
    return SceneGraph(
        nodes=[
            _cfg_node(entry_block, "fade_in_and_focus"),
            _cfg_node(exit_block, "fade_out"),
        ],
        edges=[SceneEdge(source="f::entry", target="f::exit")],
    )


def _simple_layout() -> DotLayout:
    """Build corresponding layout for the 2-node graph."""
    return DotLayout(
        nodes={
            "entry": DotNodeLayout(name="entry", center_x=200, center_y=250, width=200, height=100),
            "exit": DotNodeLayout(name="exit", center_x=200, center_y=100, width=200, height=80),
        },
        edges=[
            DotEdgeLayout(
                source="entry",
                target="exit",
                spline_points=[(200, 230), (200, 200), (200, 170), (200, 140), (200, 120)],
            ),
        ],
        bounding_box=(0, 0, 400, 300),
    )


# -- _CoordMapper -------------------------------------------------


def test_coord_mapper_center_maps_to_near_center() -> None:
    mapper = _CoordMapper((0, 0, 400, 300))
    pt = mapper.point(200, 150)
    assert abs(pt[0]) < 0.5
    assert pt[2] == 0.0


def test_coord_mapper_size_scales() -> None:
    mapper = _CoordMapper((0, 0, 400, 300))
    w, h = mapper.size(200, 100)
    assert w > 0
    assert h > 0
    assert w > h


# -- _block_summary -----------------------------------------------


def test_block_summary_ret() -> None:
    block = CFGBlock(
        id="f::exit",
        name="exit",
        function_name="f",
        events=[_event("f", "exit", "ret", "ret i32 0", "ret")],
        terminator_opcode="ret",
    )
    node = _cfg_node(block, "fade_out")
    assert "ret" in _block_summary(node)


def test_block_summary_branch() -> None:
    block = CFGBlock(
        id="f::cond",
        name="cond",
        function_name="f",
        events=[_event("f", "cond", "br", "br i1 %cmp, label %yes, label %no", "br")],
        terminator_opcode="br",
    )
    node = _cfg_node(block, "pulse_and_split")
    summary = _block_summary(node)
    assert "br i1 %cmp" in summary


def test_block_summary_call() -> None:
    block = CFGBlock(
        id="f::entry",
        name="entry",
        function_name="f",
        events=[
            _event("f", "entry", "call", "call void @helper()", "call"),
            _event("f", "entry", "ret", "ret void", "ret"),
        ],
        terminator_opcode="ret",
    )
    node = _cfg_node(block)
    summary = _block_summary(node)
    assert "call @helper" in summary


# -- _build_block_mob ---------------------------------------------


def test_build_block_mob_returns_vgroup() -> None:
    graph = _simple_graph()
    layout = _simple_layout()
    mapper = _CoordMapper(layout.bounding_box)
    mob = _build_block_mob(graph.nodes[0], layout.nodes["entry"], mapper)
    assert len(mob) >= 2  # rect + title (+ optional summary)


# -- _build_edge_mob ----------------------------------------------


def test_build_edge_mob_returns_vgroup() -> None:
    layout = _simple_layout()
    mapper = _CoordMapper(layout.bounding_box)
    mob = _build_edge_mob(layout.edges[0], mapper)
    assert len(mob) >= 2  # dashed path + arrowhead


def test_build_edge_mob_with_label() -> None:
    layout = _simple_layout()
    layout.edges[0].label = "T"
    mapper = _CoordMapper(layout.bounding_box)
    mob = _build_edge_mob(layout.edges[0], mapper)
    assert hasattr(mob, "edge_label")


def test_build_edge_mob_starts_dashed() -> None:
    layout = _simple_layout()
    mapper = _CoordMapper(layout.bounding_box)
    mob = _build_edge_mob(layout.edges[0], mapper)
    assert getattr(mob, "is_dashed", False) is True


def test_build_edge_mob_too_few_points_returns_empty() -> None:
    edge = DotEdgeLayout(source="a", target="b", spline_points=[(10, 20)])
    mapper = _CoordMapper((0, 0, 400, 300))
    mob = _build_edge_mob(edge, mapper)
    assert len(mob) == 0
