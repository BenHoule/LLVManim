"""Tests for translating EventStreams into animation commands."""

from llvmanim.ingest.llvm_events import parse_ir_to_events
from llvmanim.transform.commands import build_animation_commands
from llvmanim.transform.models import EventKind, IREvent, ProgramEventStream


def _event(
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
        kind=kind,
        index_in_function=index,
        debug_line=None,
    )


def test_build_animation_commands_translates_events() -> None:
    """Test that events are correctly translated into their corresponding animation commands.
    "other" events should be filtered out by the scene graph."""
    stream = ProgramEventStream(
        source_path="<test>",
        events=[
            _event(kind="alloca"),
            _event(kind="load"),
            _event(kind="store"),
            _event(kind="call"),
            _event(kind="ret"),
            _event(kind="br"),
            _event(kind="other"),  # This should be ignored by the scene graph
        ],
    )
    commands = build_animation_commands(stream)

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
        assert cmd.event.kind != "other", "Commands should not be created for 'other' events"


def test_build_animation_commands_ignores_extra_returns_without_matching_call() -> None:
    """A single call should produce at most one matching pop across multi-ret branch IR."""
    stream = parse_ir_to_events(
        """
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
    )

    commands = build_animation_commands(stream)
    pushes = len([command for command in commands if command.action == "push_stack_frame"])
    pops = len([command for command in commands if command.action == "pop_stack_frame"])

    assert pushes == 1
    assert pops == 1
