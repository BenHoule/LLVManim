"""Tests for the full pipeline from EventStreams to animation commands."""

from llvmanim.ingest.llvm_events import parse_ir_to_events
from llvmanim.transform.commands import build_animation_commands
from llvmanim.transform.scene import build_scene_graph

# ---------------------------------------------------------------------------
# CFG pipeline (block-level graph, edges, roles)
# ---------------------------------------------------------------------------

# Minimal IR exercising every supported EventKind plus one "other" (icmp).
_ALL_KINDS_IR = """
define void @f(ptr %p) {
entry:
  %x = alloca i32
  store i32 99, ptr %x
  %v = load i32, ptr %x
  %cond = icmp eq i32 %v, 0
  br i1 %cond, label %yes, label %no
yes:
  call void @g()
  ret void
no:
  ret void
}

declare void @g()
"""


def test_cfg_pipeline_produces_blocks_and_edges() -> None:
    """CFG pipeline: IR → SceneGraph has correct block count and edges."""
    stream = parse_ir_to_events(_ALL_KINDS_IR, source_path="<test_ir>")
    graph = build_scene_graph(stream)
    # IR has 3 basic blocks: entry, yes, no
    assert len(graph.nodes) == 3, "Expected 3 CFG blocks (entry, yes, no)"
    # entry branches to both yes and no
    assert len(graph.edges) == 2, "Expected 2 CFG edges from the conditional branch"


# ---------------------------------------------------------------------------
# Stack animation pipeline (event-level commands)
# ---------------------------------------------------------------------------


def test_stack_animation_pipeline_from_ir_to_commands() -> None:
    """Stack animation pipeline: IR → AnimationCommands has correct actions."""
    stream = parse_ir_to_events(_ALL_KINDS_IR, source_path="<test_ir>")
    commands = build_animation_commands(stream)
    assert len(commands) > 0, "Commands should be generated from the IR events"

    for cmd, expected_kind in zip(
        commands,
        [
            "create_stack_slot",  # alloca
            "animate_memory_write",  # store
            "animate_memory_read",  # load
            "highlight_branch",  # br (icmp skipped since it's "other")
            "push_stack_frame",  # call
            "pop_stack_frame",  # ret (yes block)
            "pop_stack_frame",  # ret (no block) — known gap: two pops for one logical call
        ],
        strict=True,
    ):
        assert cmd.action == expected_kind, f"Expected action {expected_kind}, got {cmd.action}"
        assert cmd.event.kind != "other", "Commands should not be created for 'other' events"
