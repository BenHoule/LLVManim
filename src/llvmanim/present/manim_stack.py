"""Manim Mobject construction from stack view models."""

from __future__ import annotations

from manim import DOWN, Animation, FadeIn, FadeOut, Rectangle, Scene, Text, Transform, VGroup

from llvmanim.present.render_stack_model import FrameStackView, RenderStep, StackFrameView

_FRAME_WIDTH = 3.5
_SLOT_HEIGHT = 0.5
_LABEL_FONT_SIZE = 24
_SLOT_FONT_SIZE = 20


def frame_to_mobject(frame: StackFrameView) -> VGroup:
    """Convert a single stack frame into a VGroup of a rectangle and text labels.

    The rectangle height scales with the number of slots. The function name
    label appears at the top; one label per slot follows below it.
    """
    n_slots = len(frame.slots)
    frame_height = _SLOT_HEIGHT * (1 + n_slots)

    rect = Rectangle(width=_FRAME_WIDTH, height=frame_height)

    name_label = Text(frame.function_name, font_size=_LABEL_FONT_SIZE)
    name_label.move_to(rect.get_top() + DOWN * (_SLOT_HEIGHT * 0.5))

    slot_labels: list[Text] = []
    for i, slot in enumerate(frame.slots):
        label = Text(slot.name, font_size=_SLOT_FONT_SIZE)
        label.move_to(rect.get_top() + DOWN * (_SLOT_HEIGHT * (1.5 + i)))
        slot_labels.append(label)

    return VGroup(rect, name_label, *slot_labels)


def stack_to_mobject(stack: FrameStackView) -> VGroup:
    """Convert a full stack snapshot into a VGroup of per-frame VGroups.

    Frames are ordered bottom-to-top visually: index 0 at the bottom, the
    top-of-stack frame last (highest on screen).
    """
    if not stack.frames:
        return VGroup()

    groups = [frame_to_mobject(frame) for frame in stack.frames]

    # Stack bottom sits first; arrange upward so the first frame is lowest.
    groups[0].move_to((0, 0, 0))
    for i in range(1, len(groups)):
        groups[i].next_to(groups[i - 1], DOWN, buff=0)

    return VGroup(*groups)


class StackMobjectManager:
    """Tracks on-screen stack frame Mobjects and produces animations for each RenderStep.

    One VGroup per stack frame is kept in `current_mobjects` in bottom-to-top
    order. Call `apply(step)` for each RenderStep; it returns the list of
    Manim animations to play for that step. The Scene only needs to call
    `self.play(*mgr.apply(step))`.
    """

    def __init__(self) -> None:
        self.current_mobjects: list[VGroup] = []

    def apply(self, step: RenderStep) -> list[Animation]:
        if step.action == "push_stack_frame":
            return self._push(step)
        if step.action == "pop_stack_frame":
            return self._pop()
        if step.action == "create_stack_slot":
            return self._create_slot(step)
        return []

    def _push(self, step: RenderStep) -> list[Animation]:
        new_frame = step.state.frames[-1]
        mob = frame_to_mobject(new_frame)
        if self.current_mobjects:
            mob.next_to(self.current_mobjects[-1], DOWN, buff=0)
        self.current_mobjects.append(mob)
        return [FadeIn(mob)]

    def _pop(self) -> list[Animation]:
        if not self.current_mobjects:
            return []
        mob = self.current_mobjects.pop()
        return [FadeOut(mob)]

    def _create_slot(self, step: RenderStep) -> list[Animation]:
        if not self.current_mobjects:
            return []
        old_mob = self.current_mobjects[-1]
        new_mob = frame_to_mobject(step.state.frames[-1])
        new_mob.move_to(old_mob)
        self.current_mobjects[-1] = new_mob
        return [Transform(old_mob, new_mob)]


class StackAnimationScene(Scene):
    """Manim Scene that animates a stack visualization driven by LLVManimScene steps.

    Pass a LLVManimScene to the constructor; call render() or let the CLI
    invoke it. construct() drives StackMobjectManager and plays each animation.
    """

    def __init__(self, llvmanim_scene, **kwargs) -> None:
        super().__init__(**kwargs)
        self.llvmanim_scene = llvmanim_scene
        self.manager = StackMobjectManager()

    def construct(self) -> None:
        for step in self.llvmanim_scene.steps:
            animations = self.manager.apply(step)
            if animations:
                self.play(*animations)

