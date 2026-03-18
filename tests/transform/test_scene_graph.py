"""Tests for CFG scene graph construction from IR event streams."""

from llvmanim.ingest.llvm_events import parse_ir_to_events
from llvmanim.transform.models import CFGBlock, ProgramEventStream, SceneGraph
from llvmanim.transform.scene import (
  _animation_hint_for_block,
  _extract_edges,
  build_scene_graph,
)


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


def test_build_scene_graph_assigns_merge_role() -> None:
    """A block targeted by two different branches gets role='merge' and animation_hint='converge'."""
    stream = parse_ir_to_events("""
        define void @f() {
        entry:
          %cond = icmp eq i32 0, 0
          br i1 %cond, label %left, label %right
        left:
          br label %merge
        right:
          br label %merge
        merge:
          br label %end
        end:
          ret void
        }
    """)
    graph = build_scene_graph(stream)
    node_map = {n.block.name: n for n in graph.nodes}
    assert node_map["merge"].role == "merge"
    assert node_map["merge"].animation_hint == "converge"


def test_build_scene_graph_linear_block_gets_highlight_hint() -> None:
    """A linear block with no memory ops gets animation_hint='highlight_block'."""
    stream = parse_ir_to_events("""
        define void @f() {
        entry:
          %cond = icmp eq i32 0, 0
          br i1 %cond, label %left, label %right
        left:
          br label %merge
        right:
          br label %merge
        merge:
          br label %end
        end:
          ret void
        }
    """)
    graph = build_scene_graph(stream)
    node_map = {n.block.name: n for n in graph.nodes}
    assert node_map["left"].role == "linear"
    assert node_map["left"].animation_hint == "highlight_block"


def test_extract_edges_skips_empty_blocks() -> None:
    """Edge extraction should ignore blocks with no events instead of failing."""
    empty_block = CFGBlock(id="f::empty", name="empty", function_name="f", events=[])
    ret_block = CFGBlock(
        id="f::retblock",
        name="retblock",
        function_name="f",
        events=[
            parse_ir_to_events(
                """
                define void @f() {
                retblock:
                  ret void
                }
                """
            ).events[0]
        ],
    )

    edges = _extract_edges(
        {
            ("f", "empty"): empty_block,
            ("f", "retblock"): ret_block,
        }
    )

    assert edges == []


def test_animation_hint_for_linear_memory_block() -> None:
  """Linear blocks with memory ops should use the memory-activity hint."""
  block = CFGBlock(id="f::entry", name="entry", function_name="f")
  block.role = "linear"
  block.memory_ops = [
    parse_ir_to_events(
      """
      define void @f() {
      entry:
        %x = alloca i32
        ret void
      }
      """
    ).events[0]
  ]

  assert _animation_hint_for_block(block) == "show_memory_activity"
