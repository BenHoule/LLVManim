"""Tests for CFG scene graph construction from IR event streams."""

from llvmanim.ingest.llvm_events import parse_ir_to_events
from llvmanim.transform.models import ProgramEventStream, SceneGraph
from llvmanim.transform.scene import build_scene_graph


def test_build_scene_graph_empty_stream() -> None:
    """Scene graph builds without error on an empty event stream."""
    stream = ProgramEventStream(source_path="<test>")
    graph = build_scene_graph(stream)
    assert isinstance(graph, SceneGraph)
    assert len(graph.nodes) == 0
    assert len(graph.edges) == 0


def test_build_scene_graph_single_block() -> None:
    """A function with one block produces one node and no edges."""
    stream = parse_ir_to_events("""
        define void @f() {
        entry:
          %x = alloca i32
          ret void
        }
    """)
    graph = build_scene_graph(stream)
    assert len(graph.nodes) == 1
    assert len(graph.edges) == 0
    assert graph.nodes[0].block.function_name == "f"
    assert graph.nodes[0].block.name == "entry"


def test_build_scene_graph_groups_events_by_block() -> None:
    """Events in different blocks produce one node per block."""
    stream = parse_ir_to_events("""
        define void @f() {
        entry:
          %cond = icmp eq i32 0, 0
          br i1 %cond, label %yes, label %no
        yes:
          ret void
        no:
          ret void
        }
    """)
    graph = build_scene_graph(stream)
    block_names = {node.block.name for node in graph.nodes}
    assert block_names == {"entry", "yes", "no"}


def test_build_scene_graph_extracts_cfg_edges() -> None:
    """A conditional branch produces two outgoing edges."""
    stream = parse_ir_to_events("""
        define void @f() {
        entry:
          %cond = icmp eq i32 0, 0
          br i1 %cond, label %yes, label %no
        yes:
          ret void
        no:
          ret void
        }
    """)
    graph = build_scene_graph(stream)
    assert len(graph.edges) == 2
    sources = {e.source for e in graph.edges}
    targets = {e.target for e in graph.edges}
    assert sources == {"f::entry"}
    assert targets == {"f::yes", "f::no"}


def test_build_scene_graph_assigns_entry_role() -> None:
    """The first block (indegree=0) gets the 'entry' role."""
    stream = parse_ir_to_events("""
        define void @f() {
        entry:
          ret void
        }
    """)
    graph = build_scene_graph(stream)
    assert graph.nodes[0].role == "entry"


def test_build_scene_graph_assigns_exit_role() -> None:
    """A block ending in ret gets the 'exit' role."""
    stream = parse_ir_to_events("""
        define void @f() {
        entry:
          %cond = icmp eq i32 0, 0
          br i1 %cond, label %done, label %done
        done:
          ret void
        }
    """)
    graph = build_scene_graph(stream)
    node_map = {n.block.name: n for n in graph.nodes}
    assert node_map["done"].role == "exit"


def test_build_scene_graph_assigns_branch_role() -> None:
    """A block with two outgoing edges gets the 'branch' role."""
    stream = parse_ir_to_events("""
        define void @f() {
        entry:
          %cond = icmp eq i32 0, 0
          br i1 %cond, label %yes, label %no
        yes:
          ret void
        no:
          ret void
        }
    """)
    graph = build_scene_graph(stream)
    node_map = {n.block.name: n for n in graph.nodes}
    assert node_map["entry"].role == "branch"


def test_build_scene_graph_block_carries_memory_ops() -> None:
    """Alloca/load/store events are captured in block.memory_ops."""
    stream = parse_ir_to_events("""
        define void @f() {
        entry:
          %x = alloca i32
          store i32 42, ptr %x
          %v = load i32, ptr %x
          ret void
        }
    """)
    graph = build_scene_graph(stream)
    assert len(graph.nodes) == 1
    mem_opcodes = [e.opcode for e in graph.nodes[0].block.memory_ops]
    assert "alloca" in mem_opcodes
    assert "store" in mem_opcodes
    assert "load" in mem_opcodes
