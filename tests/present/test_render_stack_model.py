"""Tests for build_render_steps: stack state snapshots from animation commands."""


from llvmanim.present.render_stack_model import (
    FrameStackView,
    RenderStep,
    StackFrameView,
    StackSlotView,
    build_render_steps,
)
from llvmanim.transform.commands import AnimationCommand
from llvmanim.transform.models import IREvent


def _event(function_name: str, opcode: str, text: str = "") -> IREvent:
    return IREvent(
        function_name=function_name,
        block_name="entry",
        opcode=opcode,
        text=text,
        kind="other",
        index_in_function=0,
        debug_line=None,
    )


def _cmd(action, event: IREvent) -> AnimationCommand:
    return AnimationCommand(action=action, event=event)


# ---------------------------------------------------------------------------
# Structural types
# ---------------------------------------------------------------------------


def test_stack_slot_view_has_name() -> None:
    slot = StackSlotView(name="%x")
    assert slot.name == "%x"


def test_stack_frame_view_has_function_name_and_slots() -> None:
    frame = StackFrameView(function_name="main", slots=[])
    assert frame.function_name == "main"
    assert frame.slots == []


def test_frame_stack_view_has_frames() -> None:
    stack = FrameStackView(frames=[])
    assert stack.frames == []


def test_render_step_carries_action_event_and_state() -> None:
    event = _event("main", "call")
    state = FrameStackView(frames=[])
    step = RenderStep(action="push_stack_frame", event=event, state=state)
    assert step.action == "push_stack_frame"
    assert step.event is event
    assert step.state is state


# ---------------------------------------------------------------------------
# build_render_steps
# ---------------------------------------------------------------------------


def test_build_render_steps_empty_returns_empty() -> None:
    assert build_render_steps([]) == []


def test_build_render_steps_push_adds_frame() -> None:
    event = _event("f", "call")
    steps = build_render_steps([_cmd("push_stack_frame", event)])

    assert len(steps) == 1
    assert steps[0].action == "push_stack_frame"
    assert len(steps[0].state.frames) == 1
    assert steps[0].state.frames[0].function_name == "f"


def test_build_render_steps_pop_removes_top_frame() -> None:
    push_event = _event("f", "call")
    pop_event = _event("f", "ret")
    steps = build_render_steps(
        [
            _cmd("push_stack_frame", push_event),
            _cmd("pop_stack_frame", pop_event),
        ]
    )

    assert len(steps) == 2
    assert len(steps[0].state.frames) == 1
    assert len(steps[1].state.frames) == 0


def test_build_render_steps_create_stack_slot_adds_slot_to_top_frame() -> None:
    push_event = _event("f", "call")
    alloca_event = _event("f", "alloca", "%x = alloca i32")
    steps = build_render_steps(
        [
            _cmd("push_stack_frame", push_event),
            _cmd("create_stack_slot", alloca_event),
        ]
    )

    assert len(steps) == 2
    frame = steps[1].state.frames[-1]
    assert len(frame.slots) == 1
    assert frame.slots[0].name == "%x"


def test_build_render_steps_multiple_frames_nested() -> None:
    """Calling g from f produces two stacked frames."""
    steps = build_render_steps(
        [
            _cmd("push_stack_frame", _event("f", "call")),
            _cmd("push_stack_frame", _event("g", "call")),
        ]
    )

    assert len(steps[1].state.frames) == 2
    assert steps[1].state.frames[0].function_name == "f"
    assert steps[1].state.frames[1].function_name == "g"


def test_build_render_steps_state_is_snapshot() -> None:
    """Each step carries an independent snapshot of the stack, not a shared reference."""
    push_event = _event("f", "call")
    pop_event = _event("f", "ret")
    steps = build_render_steps(
        [
            _cmd("push_stack_frame", push_event),
            _cmd("pop_stack_frame", pop_event),
        ]
    )

    # Step 0 captured 1 frame; step 1 captured 0 — they must not share the same list
    assert len(steps[0].state.frames) == 1
    assert len(steps[1].state.frames) == 0
    assert steps[0].state.frames is not steps[1].state.frames


def test_build_render_steps_non_stack_actions_still_produce_steps() -> None:
    """Actions like highlight_branch and animate_memory_read still generate a step."""
    event = _event("f", "br")
    steps = build_render_steps([_cmd("highlight_branch", event)])

    assert len(steps) == 1
    assert steps[0].action == "highlight_branch"
