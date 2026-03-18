"""Tests for LLVM IR ingestion event extraction."""

from enum import StrEnum

from llvmanim.transform.models import EventKind, IREvent, ProgramEventStream
from llvmanim.transform.scene import SceneGraph, build_scene_graph


class _FAIL_MSG(StrEnum):
    """Centralized failure messages for test assertions in this module."""

    INSTANCE = "build_scene_graph should return a SceneGraph instance"
    ORDER = "Scene graph should preserve the order of events from the event stream"
    NODES = "Scene graph should include all non-'other' events from the event stream"
    EVENT = "Scene node should not modify IREvent data from the event stream"


def _make_event(
    function_name: str = "<test_fn>",
    block_name: str = "<test_block>",
    kind: EventKind = "other",
    opcode: str | None = None,
    index: int = 0,
) -> IREvent:
    """Helper to create a simple IREvent with specified kind and optional opcode."""
    return IREvent(
        function_name=function_name,
        block_name=block_name,
        opcode=opcode or kind,
        text=f"<test {kind}>",
        kind=kind,  # type: ignore[arg-type]
        index_in_function=index,
        debug_line=None,
    )


def test_build_scene_graph_empty_stream() -> None:
    """Scene graph builds without error on an empty event stream."""
    stream = ProgramEventStream(source_path="<test>", events=[])
    graph = build_scene_graph(stream)
    assert isinstance(graph, SceneGraph), _FAIL_MSG.INSTANCE
    assert len(graph.nodes) == 0, "Scene graph should have no nodes when event stream is empty"


def test_build_scene_graph_minimal_ir() -> None:
    """Scene graph builds without error on minimal IR."""
    event = _make_event(kind="alloca")
    stream = ProgramEventStream(source_path="<test>", events=[event])

    graph = build_scene_graph(stream)
    assert isinstance(graph, SceneGraph), _FAIL_MSG.INSTANCE
    assert len(graph.nodes) == 1, _FAIL_MSG.NODES

    node = graph.nodes[0]
    assert node.event is event, "Scene node should carry the IREvent from the event stream"
    assert node.event.kind == "alloca", _FAIL_MSG.EVENT


def test_build_scene_graph_excludes_other() -> None:
    """Scene graph excludes events with kind 'other'."""
    stream = ProgramEventStream(
        source_path="<test>",
        events=[
            _make_event(kind="alloca"),
            _make_event(kind="other"),
        ],
    )
    graph = build_scene_graph(stream)
    assert isinstance(graph, SceneGraph), _FAIL_MSG.INSTANCE
    assert len(graph.nodes) == 1, _FAIL_MSG.NODES

    node = graph.nodes[0]
    assert node.event.kind == "alloca", _FAIL_MSG.EVENT


# NEEDS TO BE UPDATED AS WE ADD MORE KINDS TO THE PARSER
def test_build_scene_graph_all_kinds() -> None:
    """Scene graph includes all events of supported kinds and excludes 'other'."""
    kinds: list[EventKind] = ["alloca", "load", "store", "call", "ret", "br", "other"]
    events = [_make_event(kind=kind) for kind in kinds]
    stream = ProgramEventStream(source_path="<test>", events=events)

    graph = build_scene_graph(stream)
    assert isinstance(graph, SceneGraph), _FAIL_MSG.INSTANCE
    assert len(graph.nodes) == 6, _FAIL_MSG.NODES

    for node in graph.nodes:
        assert node.event.kind in kinds and node.event.kind != "other", (
            "Scene graph should include all supported kinds and exclude 'other'"
        )


def test_build_scene_graph_keeps_event_order() -> None:
    """Scene graph preserves the order of events."""
    stream = ProgramEventStream(
        source_path="<test>",
        events=[
            _make_event(kind="alloca"),
            _make_event(kind="store"),
            _make_event(kind="load"),
        ],
    )

    graph = build_scene_graph(stream)
    assert isinstance(graph, SceneGraph), _FAIL_MSG.INSTANCE
    assert len(graph.nodes) == 3, _FAIL_MSG.NODES

    first_node = graph.nodes[0]
    second_node = graph.nodes[1]
    third_node = graph.nodes[2]
    assert first_node.event.kind == "alloca", "First node should have index 0"
    assert second_node.event.kind == "store", "Second node should have index 1"
    assert third_node.event.kind == "load", "Third node should have index 2"


def test_function_names_property() -> None:
    """function_names property returns the set of function names in the scene graph."""
    stream = ProgramEventStream(
        source_path="<test>",
        events=[
            _make_event(function_name="<f1>", kind="call"),
            _make_event(function_name="<f2>", kind="alloca"),
            _make_event(function_name="<f1>", kind="load"),
        ],
    )

    graph = build_scene_graph(stream)
    assert isinstance(graph, SceneGraph), _FAIL_MSG.INSTANCE

    function_names = graph.function_names
    assert function_names == {"<f1>", "<f2>"}, (
        "function_names should return the unique set of function names in the scene graph"
    )


def test_get_function_nodes() -> None:
    """get_function_nodes retrieves all nodes for a given function name."""
    stream = ProgramEventStream(
        source_path="<test>",
        events=[
            _make_event(function_name="<f1>", kind="alloca", index=0),
            _make_event(function_name="<f1>", kind="alloca", index=1),
            _make_event(function_name="<f1>", kind="alloca", index=2),
            _make_event(function_name="<f2>", kind="alloca", index=0),
            _make_event(function_name="<f2>", kind="alloca", index=1),
            _make_event(function_name="<f2>", kind="alloca", index=2),
        ],
    )

    graph = build_scene_graph(stream)
    assert isinstance(graph, SceneGraph), _FAIL_MSG.INSTANCE

    for function_name in ["<f1>", "<f2>"]:
        function_nodes = graph.get_function_nodes(function_name)
        assert len(function_nodes) == 3, (
            f"get_function_nodes should return all nodes for {function_name}"
        )
        for i, node in enumerate(function_nodes):
            assert node.event.function_name == function_name, (
                f"Node should belong to {function_name}"
            )
            assert node.event.index_in_function == i, _FAIL_MSG.ORDER

    empty_nodes = graph.get_function_nodes("<nonexistent>")
    assert len(empty_nodes) == 0, (
        "get_function_nodes should return an empty list for a function name with no nodes"
    )


def test_block_names_property() -> None:
    """block_names property returns the set of block names in the scene graph."""
    stream = ProgramEventStream(
        source_path="<test>",
        events=[
            _make_event(block_name="<b1>", kind="alloca"),
            _make_event(block_name="<b2>", kind="alloca"),
            _make_event(block_name="<b1>", kind="alloca"),
        ],
    )

    graph = build_scene_graph(stream)
    assert isinstance(graph, SceneGraph), _FAIL_MSG.INSTANCE

    block_names = graph.block_names
    assert block_names == {"<b1>", "<b2>"}, (
        "block_names should return the unique set of block names in the scene graph"
    )


def test_get_block_nodes() -> None:
    """get_block_nodes retrieves all nodes for a given function and block name."""
    stream = ProgramEventStream(
        source_path="<test>",
        events=[
            _make_event(function_name="<f1>", block_name="<b1>", kind="alloca", index=0),
            _make_event(function_name="<f1>", block_name="<b1>", kind="alloca", index=1),
            _make_event(function_name="<f1>", block_name="<b2>", kind="alloca", index=2),
            _make_event(function_name="<f2>", block_name="<b1>", kind="alloca", index=0),
            _make_event(function_name="<f2>", block_name="<b2>", kind="alloca", index=1),
            _make_event(function_name="<f2>", block_name="<b2>", kind="alloca", index=2),
        ],
    )

    graph = build_scene_graph(stream)
    assert isinstance(graph, SceneGraph), _FAIL_MSG.INSTANCE

    assert len(graph.get_block_nodes("<f1>", "<b1>")) == 2, (
        "get_block_nodes should return all nodes for function <f1> and block <b1>"
    )
    assert len(graph.get_block_nodes("<f1>", "<b2>")) == 1, (
        "get_block_nodes should return all nodes for function <f1> and block <b2>"
    )
    assert len(graph.get_block_nodes("<f2>", "<b1>")) == 1, (
        "get_block_nodes should return all nodes for function <f2> and block <b1>"
    )
    assert len(graph.get_block_nodes("<f2>", "<b2>")) == 2, (
        "get_block_nodes should return all nodes for function <f2> and block <b2>"
    )

    for function_name in ["<f1>", "<f2>"]:
        for block_name in ["<b1>", "<b2>"]:
            block_nodes = graph.get_block_nodes(function_name, block_name)
            for node in block_nodes:
                assert node.event.block_name == block_name, f"Node should belong to {block_name}"

    empty_nodes = graph.get_block_nodes("<nonexistent>", "<nonexistent>")
    assert len(empty_nodes) == 0, (
        "get_block_nodes should return an empty list for a function and block name with no nodes"
    )
