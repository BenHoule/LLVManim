"""Tests for StackMobjectManager: animation production from RenderStep transitions."""

from manim import FadeIn, FadeOut, Transform

from llvmanim.present.manim_stack import StackMobjectManager
from llvmanim.present.render_stack_model import (
    FrameStackView,
    RenderStep,
    StackFrameView,
    StackSlotView,
)
from llvmanim.transform.commands import ActionKind
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


def _step(action: ActionKind, function_name: str, opcode: str, text: str = "", frames: list[StackFrameView] | None = None) -> RenderStep:
    return RenderStep(
        action=action,
        event=_event(function_name, opcode, text),
        state=FrameStackView(frames=frames or []),
    )


# ---------------------------------------------------------------------------
# Initial state
# ---------------------------------------------------------------------------


def test_manager_starts_empty() -> None:
    mgr = StackMobjectManager()
    assert mgr.current_mobjects == []


# ---------------------------------------------------------------------------
# push_stack_frame
# ---------------------------------------------------------------------------


def test_push_returns_fade_in() -> None:
    mgr = StackMobjectManager()
    step = _step("push_stack_frame", "f", "call", frames=[
        StackFrameView(function_name="f", slots=[]),
    ])
    animations = mgr.apply(step)
    assert len(animations) == 1
    assert isinstance(animations[0], FadeIn)


def test_push_adds_to_current_mobjects() -> None:
    mgr = StackMobjectManager()
    step = _step("push_stack_frame", "f", "call", frames=[
        StackFrameView(function_name="f", slots=[]),
    ])
    mgr.apply(step)
    assert len(mgr.current_mobjects) == 1


def test_push_twice_adds_two_mobjects() -> None:
    mgr = StackMobjectManager()
    mgr.apply(_step("push_stack_frame", "f", "call", frames=[
        StackFrameView(function_name="f", slots=[]),
    ]))
    mgr.apply(_step("push_stack_frame", "g", "call", frames=[
        StackFrameView(function_name="f", slots=[]),
        StackFrameView(function_name="g", slots=[]),
    ]))
    assert len(mgr.current_mobjects) == 2


# ---------------------------------------------------------------------------
# pop_stack_frame
# ---------------------------------------------------------------------------


def test_pop_returns_fade_out() -> None:
    mgr = StackMobjectManager()
    mgr.apply(_step("push_stack_frame", "f", "call", frames=[
        StackFrameView(function_name="f", slots=[]),
    ]))
    step = _step("pop_stack_frame", "f", "ret", frames=[])
    animations = mgr.apply(step)
    assert len(animations) == 1
    assert isinstance(animations[0], FadeOut)


def test_pop_removes_from_current_mobjects() -> None:
    mgr = StackMobjectManager()
    mgr.apply(_step("push_stack_frame", "f", "call", frames=[
        StackFrameView(function_name="f", slots=[]),
    ]))
    mgr.apply(_step("pop_stack_frame", "f", "ret", frames=[]))
    assert len(mgr.current_mobjects) == 0


def test_pop_on_empty_stack_returns_no_animations() -> None:
    mgr = StackMobjectManager()
    animations = mgr.apply(_step("pop_stack_frame", "f", "ret", frames=[]))
    assert animations == []


# ---------------------------------------------------------------------------
# create_stack_slot
# ---------------------------------------------------------------------------


def test_create_slot_returns_transform() -> None:
    mgr = StackMobjectManager()
    mgr.apply(_step("push_stack_frame", "f", "call", frames=[
        StackFrameView(function_name="f", slots=[]),
    ]))
    step = _step("create_stack_slot", "f", "alloca", "%x = alloca i32", frames=[
        StackFrameView(function_name="f", slots=[StackSlotView(name="%x")]),
    ])
    animations = mgr.apply(step)
    assert len(animations) == 1
    assert isinstance(animations[0], Transform)


def test_create_slot_does_not_change_mobject_count() -> None:
    mgr = StackMobjectManager()
    mgr.apply(_step("push_stack_frame", "f", "call", frames=[
        StackFrameView(function_name="f", slots=[]),
    ]))
    before = len(mgr.current_mobjects)
    mgr.apply(_step("create_stack_slot", "f", "alloca", "%x = alloca i32", frames=[
        StackFrameView(function_name="f", slots=[StackSlotView(name="%x")]),
    ]))
    assert len(mgr.current_mobjects) == before


# ---------------------------------------------------------------------------
# Non-stack actions produce no animations
# ---------------------------------------------------------------------------


def test_highlight_branch_returns_no_animations() -> None:
    mgr = StackMobjectManager()
    step = _step("highlight_branch", "f", "br", frames=[])
    animations = mgr.apply(step)
    assert animations == []


def test_animate_memory_read_returns_no_animations() -> None:
    mgr = StackMobjectManager()
    step = _step("animate_memory_read", "f", "load", frames=[])
    animations = mgr.apply(step)
    assert animations == []
