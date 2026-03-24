"""Stack-frame animation renderer driven by a SceneGraph's command list.

``StackRenderer`` is a :class:`CommandDrivenScene` subclass that registers
handlers for stack-related actions: push/pop frames, create slots, and
optionally animate SSA operations.  It replaces ``RichStackSceneBadge``
and ``RichStackSceneSpotlight`` in the unified pipeline.
"""

from __future__ import annotations

from manim import (
    BLUE_D,
    BOLD,
    DOWN,
    GOLD_D,
    GREEN_C,
    GREY_B,
    MAROON_D,
    PURPLE_D,
    RIGHT,
    TEAL_D,
    UP,
    WHITE,
    YELLOW,
    FadeIn,
    FadeOut,
    ManimColor,
    Rectangle,
    Text,
    VGroup,
)

from llvmanim.ingest.display_lines import clean_ir_line
from llvmanim.present.command_driven_scene import CommandDrivenScene
from llvmanim.transform.models import AnimationCommand, SceneGraph

# ── Layout constants ────────────────────────────────────────────────────────────

_SLOT_W = 4.0
_HEADER_H = 0.55
_SLOT_H = 0.62
_GAP = 0.04
_STACK_TOP_Y = 2.6

_PALETTE: list[ManimColor] = [BLUE_D, GREEN_C, TEAL_D, GOLD_D, MAROON_D, PURPLE_D]


# ── Mobject factories ───────────────────────────────────────────────────────────

def _frame_header(func_name: str, color: ManimColor, width: float = _SLOT_W) -> VGroup:
    """Opaque coloured header bar labelled @func_name."""
    rect = Rectangle(
        width=width,
        height=_HEADER_H,
        fill_color=color,
        fill_opacity=0.85,
        stroke_color=color,
        stroke_width=2,
    )
    label = Text(f"@{func_name}", font="Monospace", font_size=22, color=WHITE, weight=BOLD)
    label.move_to(rect)
    return VGroup(rect, label)


def _slot_cell(slot_text: str, color: ManimColor, width: float = _SLOT_W) -> VGroup:
    """Single alloca-slot row tinted with the owning frame's colour."""
    rect = Rectangle(
        width=width,
        height=_SLOT_H,
        fill_color=color,
        fill_opacity=0.18,
        stroke_color=color,
        stroke_width=1.5,
    )
    label = Text(slot_text, font="Monospace", font_size=19)
    label.move_to(rect)
    return VGroup(rect, label)


# ── StackRenderer ───────────────────────────────────────────────────────────────

class StackRenderer(CommandDrivenScene):
    """Command-driven stack-frame animation scene.

    Parameters
    ----------
    graph:
        A SceneGraph produced by ``build_stack_scene_graph()``.
    speed:
        Animation speed multiplier.
    title:
        Title text shown at the top.
    """

    _STACK_X: float = 0.5
    _SLOT_WIDTH: float = _SLOT_W

    def __init__(
        self,
        graph: SceneGraph,
        speed: float = 1.0,
        title: str = "Call Stack  /  LLVManim",
        **kwargs: object,
    ) -> None:
        super().__init__(graph, speed=speed, title=title, **kwargs)

        self._cursor_y: float = _STACK_TOP_Y
        self._depth: int = 0
        self._frame_stack: list[tuple[VGroup, list[VGroup]]] = []
        self._frame_names: list[str] = []

        self._register_handler("push_stack_frame", self._handle_push)
        self._register_handler("pop_stack_frame", self._handle_pop)
        self._register_handler("create_stack_slot", self._handle_alloca)
        self._register_handler("highlight_branch", self._handle_branch)

    def _setup_chrome(self) -> None:
        super()._setup_chrome()
        col_label = Text("Stack  (grows \u2193)", font_size=21, color=GREY_B)
        col_label.move_to(RIGHT * self._STACK_X + UP * 2.85)
        self.add(col_label)

    # ── Handlers ────────────────────────────────────────────────────────────

    def _color(self) -> ManimColor:
        return _PALETTE[self._depth % len(_PALETTE)]

    def _handle_push(self, cmd: AnimationCommand) -> None:
        func_name = cmd.params.get("function_name", "")
        color = self._color()
        mob = _frame_header(func_name, color, width=self._SLOT_WIDTH)
        mob.move_to(RIGHT * self._STACK_X + UP * (self._cursor_y - _HEADER_H / 2))
        self._cursor_y -= _HEADER_H + _GAP
        self._depth += 1
        self._frame_stack.append((mob, []))
        self._frame_names.append(func_name)
        mob[1].set_color(YELLOW)
        self.play(FadeIn(mob, shift=DOWN * 0.25), run_time=self._rt(0.5))
        self.play(mob[1].animate.set_color(WHITE), run_time=self._rt(0.35))

    def _handle_pop(self, cmd: AnimationCommand) -> None:
        if not self._frame_stack:
            return
        if self._frame_names:
            self._frame_names.pop()
        header, slots = self._frame_stack.pop()
        self._depth -= 1
        self._cursor_y += _HEADER_H + _GAP + len(slots) * (_SLOT_H + _GAP)
        mobs_out = slots[::-1] + [header]
        self.play(*[FadeOut(m, shift=UP * 0.2) for m in mobs_out], run_time=self._rt(0.55))

    def _handle_alloca(self, cmd: AnimationCommand) -> None:
        if not self._frame_stack:
            return
        slot_text = cmd.event.text if cmd.event else cmd.params.get("slot_name", "")
        display_text = clean_ir_line(slot_text)
        color = _PALETTE[(self._depth - 1) % len(_PALETTE)]
        mob = _slot_cell(display_text, color, width=self._SLOT_WIDTH)
        mob.move_to(RIGHT * self._STACK_X + UP * (self._cursor_y - _SLOT_H / 2))
        self._cursor_y -= _SLOT_H + _GAP
        self._frame_stack[-1][1].append(mob)
        mob[1].set_color(YELLOW)
        self.play(FadeIn(mob, shift=DOWN * 0.15), run_time=self._rt(0.4))
        self.play(mob[1].animate.set_color(WHITE), run_time=self._rt(0.35))

    def _handle_branch(self, cmd: AnimationCommand) -> None:
        """Highlight-branch is currently a visual no-op in the stack renderer."""
