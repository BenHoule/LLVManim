"""Tests for CFG scene graph construction from IR event streams."""

from llvmanim.ingest.llvm_events import parse_ir_to_events
from llvmanim.transform.models import BlockMetadata, CFGBlock, ProgramEventStream, SceneGraph
from llvmanim.transform.scene import (
  _animation_hint_for_block,
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
    assert graph.nodes[0].properties["function_name"] == "f"
    assert graph.nodes[0].label == "entry"


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
    block_names = {node.label for node in graph.nodes}
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
    assert graph.nodes[0].properties["role"] == "entry"


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
    node_map = {n.label: n for n in graph.nodes}
    assert node_map["done"].properties["role"] == "exit"


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
    node_map = {n.label: n for n in graph.nodes}
    assert node_map["entry"].properties["role"] == "branch"


def test_build_scene_graph_block_carries_memory_ops() -> None:
    """Alloca/load/store events are captured in properties['memory_ops']."""
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
    mem_opcodes = [e.opcode for e in graph.nodes[0].properties["memory_ops"]]
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
    node_map = {n.label: n for n in graph.nodes}
    assert node_map["merge"].properties["role"] == "merge"
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
    node_map = {n.label: n for n in graph.nodes}
    assert node_map["left"].properties["role"] == "linear"
    assert node_map["left"].animation_hint == "highlight_block"


def test_build_scene_graph_deduplicates_duplicate_branch_targets() -> None:
    """A branch that names the same target twice should produce one unique edge."""
    stream = parse_ir_to_events(
        """
        define void @f() {
        entry:
          %cond = icmp eq i32 0, 0
          br i1 %cond, label %done, label %done
        done:
          ret void
        }
        """
    )

    graph = build_scene_graph(stream)
    edges = [(edge.source, edge.target) for edge in graph.edges]

    assert edges == [("f::entry", "f::done")]


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


# ── Analysis metadata integration ──────────────────────────────────


def test_loop_header_metadata_overrides_animation_hint() -> None:
    """A block marked as loop header gets the pulse_loop_header hint."""
    stream = parse_ir_to_events("""
        define void @f() {
        entry:
          br label %loop
        loop:
          %cond = icmp eq i32 0, 0
          br i1 %cond, label %loop, label %exit
        exit:
          ret void
        }
    """)
    metadata = {
        "f::loop": BlockMetadata(is_loop_header=True, loop_depth=1, loop_id="L0"),
    }
    graph = build_scene_graph(stream, analysis_metadata=metadata)
    node_map = {n.label: n for n in graph.nodes}

    assert node_map["loop"].properties["is_loop_header"] is True
    assert node_map["loop"].animation_hint == "pulse_loop_header"


def test_metadata_applies_domtree_fields() -> None:
    """Dominator-tree fields are copied onto matching blocks."""
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
    metadata = {
        "f::entry": BlockMetadata(dom_depth=0),
        "f::yes": BlockMetadata(idom="f::entry", dom_depth=1),
        "f::no": BlockMetadata(idom="f::entry", dom_depth=1),
    }
    graph = build_scene_graph(stream, analysis_metadata=metadata)
    node_map = {n.label: n for n in graph.nodes}

    assert node_map["yes"].properties["idom"] == "f::entry"
    assert node_map["yes"].properties["dom_depth"] == 1
    assert node_map["no"].properties["idom"] == "f::entry"
    assert node_map["entry"].properties["dom_depth"] == 0


def test_metadata_applies_loop_fields() -> None:
    """Loop metadata fields are copied onto matching blocks."""
    stream = parse_ir_to_events("""
        define void @f() {
        entry:
          br label %header
        header:
          %cond = icmp eq i32 0, 0
          br i1 %cond, label %body, label %exit
        body:
          br label %header
        exit:
          ret void
        }
    """)
    metadata = {
        "f::header": BlockMetadata(
            is_loop_header=True,
            loop_depth=1,
            loop_id="loop_0",
            is_backedge_target=True,
        ),
        "f::body": BlockMetadata(loop_depth=1, loop_id="loop_0"),
    }
    graph = build_scene_graph(stream, analysis_metadata=metadata)
    node_map = {n.label: n for n in graph.nodes}

    assert node_map["header"].properties["is_loop_header"] is True
    assert node_map["header"].properties["loop_id"] == "loop_0"
    assert node_map["header"].properties["is_backedge_target"] is True
    assert node_map["body"].properties["loop_depth"] == 1
    assert node_map["body"].properties["loop_id"] == "loop_0"


def test_metadata_ignores_unknown_block_ids() -> None:
    """Metadata for blocks not in the graph is silently ignored."""
    stream = parse_ir_to_events("""
        define void @f() {
        entry:
          ret void
        }
    """)
    metadata = {
        "f::nonexistent": BlockMetadata(dom_depth=5),
    }
    graph = build_scene_graph(stream, analysis_metadata=metadata)

    assert len(graph.nodes) == 1
    assert graph.nodes[0].properties["dom_depth"] == 0  # unchanged


def test_no_metadata_preserves_original_behavior() -> None:
    """Without metadata, roles and hints are derived from topology alone."""
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
    graph_without = build_scene_graph(stream)
    graph_with_none = build_scene_graph(stream, analysis_metadata=None)
    graph_with_empty = build_scene_graph(stream, analysis_metadata={})

    def _snapshot(g: SceneGraph) -> set[tuple[str, str, str]]:
        return {(n.label, n.properties["role"], n.animation_hint) for n in g.nodes}

    assert _snapshot(graph_without) == _snapshot(graph_with_none) == _snapshot(graph_with_empty)



# ── T/F edge labels from ingest layer ──────────────────────────────


def test_scene_graph_preserves_edge_labels() -> None:
    """Edge labels (T/F) from cfg_edges are preserved in the scene graph."""
    stream = parse_ir_to_events("""
        define void @f(i1 %cond) {
        entry:
          br i1 %cond, label %yes, label %no
        yes:
          ret void
        no:
          ret void
        }
    """)
    graph = build_scene_graph(stream)
    labels = {e.label for e in graph.edges}
    assert labels == {"T", "F"}


# ── stack mode (mode="stack") ──────────────────────────────────


def _stack_event(fn, kind, text, idx, *, opcode=None, operands=None):
    from llvmanim.transform.models import IREvent
    return IREvent(
        function_name=fn,
        block_name="entry",
        opcode=opcode or kind,
        text=text,
        kind=kind,
        index_in_function=idx,
        debug_line=None,
        operands=operands or [],
    )


def test_stack_scene_graph_empty_stream() -> None:
    """An empty stream produces an empty scene graph."""
    stream = ProgramEventStream(source_path="<test>")
    graph = build_scene_graph(stream, mode="stack", entry="main")
    assert graph.nodes == []
    assert graph.edges == []
    assert graph.commands == []


def test_stack_scene_graph_single_function() -> None:
    """A single function with one alloca produces a frame, a slot, and commands."""
    stream = ProgramEventStream(
        source_path="<test>",
        events=[
            _stack_event("main", "alloca", "%x = alloca i32", 0),
            _stack_event("main", "ret", "ret i32 0", 1),
        ],
    )
    graph = build_scene_graph(stream, mode="stack", entry="main")

    frame_nodes = [n for n in graph.nodes if n.kind == "stack_frame"]
    slot_nodes = [n for n in graph.nodes if n.kind == "stack_slot"]
    assert len(frame_nodes) == 1
    assert len(slot_nodes) == 1

    assert frame_nodes[0].label == "main"
    assert slot_nodes[0].label == "%x"

    actions = [c.action for c in graph.commands]
    assert actions == ["push_stack_frame", "create_stack_slot", "pop_stack_frame"]


def test_stack_scene_graph_callee_descent() -> None:
    """Calls descend into defined callees and create call edges."""
    stream = ProgramEventStream(
        source_path="<test>",
        events=[
            _stack_event("main", "call", "call void @foo()", 0),
            _stack_event("main", "ret", "ret i32 0", 1),
            _stack_event("foo", "alloca", "%y = alloca i32", 0),
            _stack_event("foo", "ret", "ret void", 1),
        ],
    )
    graph = build_scene_graph(stream, mode="stack", entry="main")

    frame_nodes = [n for n in graph.nodes if n.kind == "stack_frame"]
    assert len(frame_nodes) == 2
    frame_labels = {n.label for n in frame_nodes}
    assert frame_labels == {"main", "foo"}

    call_edges = [e for e in graph.edges if e.kind == "call"]
    assert len(call_edges) == 1
    assert "main" in call_edges[0].source
    assert "foo" in call_edges[0].target

    actions = [c.action for c in graph.commands]
    assert actions == [
        "push_stack_frame",  # main
        "push_stack_frame",  # foo
        "create_stack_slot",  # %y in foo
        "pop_stack_frame",   # foo
        "pop_stack_frame",   # main
    ]


def test_stack_scene_graph_skips_external_functions() -> None:
    """External (undefined) callees are silently skipped."""
    stream = ProgramEventStream(
        source_path="<test>",
        events=[
            _stack_event("main", "call", "call void @external()", 0),
            _stack_event("main", "ret", "ret i32 0", 1),
        ],
    )
    graph = build_scene_graph(stream, mode="stack", entry="main")

    frame_nodes = [n for n in graph.nodes if n.kind == "stack_frame"]
    assert len(frame_nodes) == 1
    assert frame_nodes[0].label == "main"
    assert graph.edges == []


def test_stack_scene_graph_skips_llvm_intrinsics() -> None:
    """LLVM intrinsics (llvm.*) are silently skipped."""
    stream = ProgramEventStream(
        source_path="<test>",
        events=[
            _stack_event("main", "call", "call void @llvm.memcpy.p0.p0.i64(ptr %a, ptr %b, i64 8, i1 false)", 0),
            _stack_event("main", "ret", "ret i32 0", 1),
        ],
    )
    graph = build_scene_graph(stream, mode="stack", entry="main")

    frame_nodes = [n for n in graph.nodes if n.kind == "stack_frame"]
    assert len(frame_nodes) == 1


def test_stack_scene_graph_max_depth_honored() -> None:
    """max_depth=0 should only include the entry frame, not callees."""
    stream = ProgramEventStream(
        source_path="<test>",
        events=[
            _stack_event("main", "call", "call void @foo()", 0),
            _stack_event("main", "ret", "ret i32 0", 1),
            _stack_event("foo", "ret", "ret void", 0),
        ],
    )
    graph = build_scene_graph(stream, mode="stack", entry="main", max_depth=0)

    frame_nodes = [n for n in graph.nodes if n.kind == "stack_frame"]
    assert len(frame_nodes) == 1
    assert frame_nodes[0].label == "main"


def test_stack_scene_graph_include_ssa_emits_binop_compare_load() -> None:
    """include_ssa=True emits binop, compare, and load animation commands."""
    stream = ProgramEventStream(
        source_path="<test>",
        events=[
            _stack_event("main", "alloca", "%x = alloca i32", 0),
            _stack_event("main", "load", "%1 = load i32, ptr %x", 1, operands=["%x"]),
            _stack_event("main", "binop", "%mul = mul nsw i32 2, %1", 2, operands=["2", "%1"]),
            _stack_event("main", "compare", "%cmp = icmp sgt i32 %mul, 5", 3, operands=["%mul", "5"]),
            _stack_event("main", "ret", "ret i32 %mul", 4),
        ],
    )
    graph = build_scene_graph(stream, mode="stack", entry="main", include_ssa=True)

    actions = [c.action for c in graph.commands]
    assert "animate_memory_read" in actions
    assert "animate_binop" in actions
    assert "animate_compare" in actions

    # Verify operands are passed through
    binop_cmd = next(c for c in graph.commands if c.action == "animate_binop")
    assert binop_cmd.params["operands"] == ["2", "%1"]


def test_stack_scene_graph_without_ssa_skips_binop() -> None:
    """Without include_ssa, binop/compare/load events produce no commands."""
    stream = ProgramEventStream(
        source_path="<test>",
        events=[
            _stack_event("main", "binop", "%mul = mul nsw i32 2, %1", 0, operands=["2", "%1"]),
            _stack_event("main", "ret", "ret i32 0", 1),
        ],
    )
    graph = build_scene_graph(stream, mode="stack", entry="main", include_ssa=False)

    actions = [c.action for c in graph.commands]
    assert "animate_binop" not in actions


def test_stack_scene_graph_branch_events() -> None:
    """Branch events emit highlight_branch commands."""
    stream = ProgramEventStream(
        source_path="<test>",
        events=[
            _stack_event("main", "br", "br label %exit", 0),
            _stack_event("main", "ret", "ret i32 0", 1),
        ],
    )
    graph = build_scene_graph(stream, mode="stack", entry="main")

    actions = [c.action for c in graph.commands]
    assert "highlight_branch" in actions


def test_stack_scene_graph_command_targets_reference_node_ids() -> None:
    """All command targets should reference existing node IDs."""
    stream = ProgramEventStream(
        source_path="<test>",
        events=[
            _stack_event("main", "alloca", "%x = alloca i32", 0),
            _stack_event("main", "ret", "ret i32 0", 1),
        ],
    )
    graph = build_scene_graph(stream, mode="stack", entry="main")

    node_ids = {n.id for n in graph.nodes}
    for cmd in graph.commands:
        assert cmd.target in node_ids, f"Command target {cmd.target!r} not in node IDs"


def test_stack_scene_graph_slot_properties() -> None:
    """Stack slot nodes carry frame_id and function_name in properties."""
    stream = ProgramEventStream(
        source_path="<test>",
        events=[
            _stack_event("main", "alloca", "%ptr = alloca i32", 0),
            _stack_event("main", "ret", "ret i32 0", 1),
        ],
    )
    graph = build_scene_graph(stream, mode="stack", entry="main")

    slot = next(n for n in graph.nodes if n.kind == "stack_slot")
    assert slot.properties["function_name"] == "main"
    assert "frame_id" in slot.properties
    assert slot.label == "%ptr"
