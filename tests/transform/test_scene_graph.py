"""Tests for LLVM IR ingestion event extraction."""

from llvmanim.transform.models import IREvent, ProgramEventStream
from llvmanim.transform.scene import SceneGraph, build_scene_graph


def test_build_scene_graph_minimal_ir() -> None:
    """Scene graph builds without error on minimal IR."""
    stream = ProgramEventStream(
        source_path="<test>",
        events=[
            IREvent(
                function_name="main",
                block_name="entry",
                opcode="alloca",
                text="%x = alloca i32",
                kind="alloca",
                index_in_function=0,
                debug_line=None,
                operands=["i32"],
            )
        ],
    )

    graph = build_scene_graph(stream)
    assert isinstance(graph, SceneGraph)
    assert len(graph.nodes) == 1

    node = graph.nodes[0]
    assert node.event.kind == "alloca"
