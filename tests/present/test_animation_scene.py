"""Tests for StackAnimationScene: thin Manim Scene driving StackMobjectManager."""

from unittest.mock import patch

from manim import FadeIn, FadeOut, Scene, Transform

from llvmanim.present.manim_stack import StackAnimationScene, StackMobjectManager
from llvmanim.present.render_stack_model import (
    FrameStackView,
    RenderStep,
    StackFrameView,
    StackSlotView,
)
from llvmanim.present.scene_builder import LLVManimScene
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
# Class structure
# ---------------------------------------------------------------------------


def test_stack_animation_scene_is_manim_scene() -> None:
    scene = StackAnimationScene(LLVManimScene(steps=[]))
    assert isinstance(scene, Scene)


def test_stack_animation_scene_has_manager() -> None:
    scene = StackAnimationScene(LLVManimScene(steps=[]))
    assert isinstance(scene.manager, StackMobjectManager)


def test_stack_animation_scene_stores_llvmanim_scene() -> None:
    llvmanim_scene = LLVManimScene(steps=[])
    scene = StackAnimationScene(llvmanim_scene)
    assert scene.llvmanim_scene is llvmanim_scene


# ---------------------------------------------------------------------------
# construct() dispatches correct animation types
# ---------------------------------------------------------------------------


def test_construct_calls_play_for_push() -> None:
    steps = [_step("push_stack_frame", "f", "call", frames=[
        StackFrameView(function_name="f", slots=[]),
    ])]
    scene = StackAnimationScene(LLVManimScene(steps=steps))
    with patch.object(scene, "play") as mock_play:
        scene.construct()
    mock_play.assert_called_once()
    assert isinstance(mock_play.call_args[0][0], FadeIn)


def test_construct_calls_play_for_pop() -> None:
    push = _step("push_stack_frame", "f", "call", frames=[
        StackFrameView(function_name="f", slots=[]),
    ])
    pop = _step("pop_stack_frame", "f", "ret", frames=[])
    scene = StackAnimationScene(LLVManimScene(steps=[push, pop]))
    with patch.object(scene, "play") as mock_play:
        scene.construct()
    assert mock_play.call_count == 2
    assert isinstance(mock_play.call_args_list[1][0][0], FadeOut)


def test_construct_calls_play_for_create_slot() -> None:
    push = _step("push_stack_frame", "f", "call", frames=[
        StackFrameView(function_name="f", slots=[]),
    ])
    slot = _step("create_stack_slot", "f", "alloca", "%x = alloca i32", frames=[
        StackFrameView(function_name="f", slots=[StackSlotView(name="%x")]),
    ])
    scene = StackAnimationScene(LLVManimScene(steps=[push, slot]))
    with patch.object(scene, "play") as mock_play:
        scene.construct()
    assert mock_play.call_count == 2
    assert isinstance(mock_play.call_args_list[1][0][0], Transform)


def test_construct_skips_play_for_non_stack_actions() -> None:
    steps = [
        _step("highlight_branch", "f", "br", frames=[]),
        _step("animate_memory_read", "f", "load", frames=[]),
    ]
    scene = StackAnimationScene(LLVManimScene(steps=steps))
    with patch.object(scene, "play") as mock_play:
        scene.construct()
    mock_play.assert_not_called()


def test_construct_empty_steps_does_not_call_play() -> None:
    scene = StackAnimationScene(LLVManimScene(steps=[]))
    with patch.object(scene, "play") as mock_play:
        scene.construct()
    mock_play.assert_not_called()
