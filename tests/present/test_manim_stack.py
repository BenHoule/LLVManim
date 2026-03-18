"""Tests for Manim Mobject construction from FrameStackView."""

from manim import Rectangle, Text, VGroup

from llvmanim.present.manim_stack import frame_to_mobject, stack_to_mobject
from llvmanim.present.render_stack_model import FrameStackView, StackFrameView, StackSlotView

# ---------------------------------------------------------------------------
# frame_to_mobject
# ---------------------------------------------------------------------------


def test_frame_to_mobject_returns_vgroup() -> None:
    frame = StackFrameView(function_name="main", slots=[])
    mob = frame_to_mobject(frame)
    assert isinstance(mob, VGroup)


def test_frame_to_mobject_contains_rectangle() -> None:
    frame = StackFrameView(function_name="main", slots=[])
    mob = frame_to_mobject(frame)
    rects = [m for m in mob if isinstance(m, Rectangle)]
    assert len(rects) == 1


def test_frame_to_mobject_contains_function_name_label() -> None:
    frame = StackFrameView(function_name="main", slots=[])
    mob = frame_to_mobject(frame)
    texts = [m for m in mob if isinstance(m, Text)]
    assert any(t.text == "main" for t in texts)


def test_frame_to_mobject_contains_slot_labels() -> None:
    frame = StackFrameView(
        function_name="f",
        slots=[StackSlotView(name="%x"), StackSlotView(name="%y")],
    )
    mob = frame_to_mobject(frame)
    texts = [m for m in mob if isinstance(m, Text)]
    slot_texts = {t.text for t in texts}
    assert "%x" in slot_texts
    assert "%y" in slot_texts


def test_frame_to_mobject_no_slots_has_one_text() -> None:
    frame = StackFrameView(function_name="f", slots=[])
    mob = frame_to_mobject(frame)
    texts = [m for m in mob if isinstance(m, Text)]
    assert len(texts) == 1


def test_frame_to_mobject_n_slots_has_n_plus_one_texts() -> None:
    frame = StackFrameView(
        function_name="f",
        slots=[StackSlotView(name="%a"), StackSlotView(name="%b"), StackSlotView(name="%c")],
    )
    mob = frame_to_mobject(frame)
    texts = [m for m in mob if isinstance(m, Text)]
    assert len(texts) == 4  # function label + 3 slots


# ---------------------------------------------------------------------------
# stack_to_mobject
# ---------------------------------------------------------------------------


def test_stack_to_mobject_returns_vgroup() -> None:
    stack = FrameStackView(frames=[])
    mob = stack_to_mobject(stack)
    assert isinstance(mob, VGroup)


def test_stack_to_mobject_empty_stack_is_empty() -> None:
    mob = stack_to_mobject(FrameStackView(frames=[]))
    assert len(mob) == 0


def test_stack_to_mobject_has_one_group_per_frame() -> None:
    stack = FrameStackView(
        frames=[
            StackFrameView(function_name="main", slots=[]),
            StackFrameView(function_name="f", slots=[]),
        ]
    )
    mob = stack_to_mobject(stack)
    assert len(mob) == 2
    assert all(isinstance(m, VGroup) for m in mob)


def test_stack_to_mobject_frame_order_matches_input() -> None:
    """Bottom of stack is index 0, top is last."""
    stack = FrameStackView(
        frames=[
            StackFrameView(function_name="outer", slots=[]),
            StackFrameView(function_name="inner", slots=[]),
        ]
    )
    mob = stack_to_mobject(stack)
    outer_texts = [m for m in mob[0] if isinstance(m, Text)]
    inner_texts = [m for m in mob[1] if isinstance(m, Text)]
    assert any(t.text == "outer" for t in outer_texts)
    assert any(t.text == "inner" for t in inner_texts)
