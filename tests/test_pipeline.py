"""Tests for the full pipeline from EventStreams to animation commands."""

from llvmanim.ingest.llvm_events import parse_ir_to_events
from llvmanim.transform.commands import build_animation_commands
from llvmanim.transform.scene import build_scene_graph

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


def test_pipeline_from_ir_to_commands() -> None:
    """Test the full pipeline from raw events to final animation commands."""
    stream = parse_ir_to_events(_ALL_KINDS_IR, source_path="<test_ir>")
    graph = build_scene_graph(stream)
    commands = build_animation_commands(graph)
    assert len(commands) > 0, "Commands should be generated from the IR events"

    for cmd, expected_kind in zip(
        commands,
        [
            "create_stack_slot",  # alloca
            "animate_memory_write",  # store
            "animate_memory_read",  # load
            "highlight_branch",  # br (icmp skipped since it's "other")
            "push_stack_frame",  # call
            "pop_stack_frame",  # ret
            "pop_stack_frame",  # ret (This could be an issue since we have two rets, but for this test we just want to ensure all commands are generated)
        ],
        strict=True,
    ):
        assert cmd.action == expected_kind, f"Expected action {expected_kind}, got {cmd.action}"
        assert cmd.node.event.kind != "other", "Commands should not be created for 'other' events"
