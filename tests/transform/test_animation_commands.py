"""Tests for translating EventStreams into animation commands."""

from llvmanim.transform.commands import build_animation_commands
from llvmanim.transform.models import EventKind, IREvent, ProgramEventStream
from llvmanim.transform.scene import build_scene_graph


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


def test_build_animation_commands_translates_events() -> None:
    """Test that events are correctly translated into their corresponding animation commands.
    "other" events should be filtered out by the scene graph."""
    stream = ProgramEventStream(
        source_path="<test>",
        events=[
            _make_event(kind="alloca"),
            _make_event(kind="load"),
            _make_event(kind="store"),
            _make_event(kind="call"),
            _make_event(kind="ret"),
            _make_event(kind="br"),
            _make_event(kind="other"),  # This should be ignored by the scene graph
        ],
    )
    graph = build_scene_graph(stream)
    commands = build_animation_commands(graph)

    assert len(commands) == 6, (
        "Should create one command for each supported event kind, excluding 'other'"
    )
    for cmd, expected_kind in zip(
        commands,
        [
            "create_stack_slot",
            "animate_memory_read",
            "animate_memory_write",
            "push_stack_frame",
            "pop_stack_frame",
            "highlight_branch",
        ],
        strict=True,
    ):
        assert cmd.action == expected_kind, f"Expected action {expected_kind}, got {cmd.action}"
        assert cmd.node.event.kind != "other", "Commands should not be created for 'other' events"
