"""Stack-frame animation renderer driven by a SceneGraph's command list.

``StackRenderer`` is a :class:`CommandDrivenScene` subclass that registers
handlers for stack-related actions: push/pop frames, create slots, and
optionally animate SSA operations.  It replaces ``RichStackSceneBadge``
and ``RichStackSceneSpotlight`` in the unified pipeline.

Three display modes are supported via the *ir_mode* parameter:

  basic      — Stack-only layout with yellow-flash badge on arriving cells.
  rich       — Two-column layout (IR Source | Stack) with a yellow
               SurroundingRectangle cursor that advances to the current
               instruction and FadeTransforms to the callee's IR on call/ret.
  rich-ssa   — Three-column layout (IR Source | SSA Values | Stack).  Binop,
               compare, and load operations produce SSA value rows in the
               centre panel that persist until their owning frame pops.
"""

from __future__ import annotations

from manim import (
    BLUE_D,
    BOLD,
    DOWN,
    GOLD_D,
    GREEN_C,
    GREY_B,
    GREY_D,
    LEFT,
    MAROON_D,
    PURPLE_D,
    RIGHT,
    TEAL_D,
    UP,
    WHITE,
    YELLOW,
    FadeIn,
    FadeOut,
    FadeTransform,
    Line,
    ManimColor,
    Rectangle,
    SurroundingRectangle,
    Text,
    VGroup,
)

from llvmanim.ingest.display_lines import clean_ir_line
from llvmanim.render.command_driven_scene import CommandDrivenScene
from llvmanim.render.ssa_formatting import (
    OP_COLORS,
    extract_ssa_name,
    format_display_value,
)
from llvmanim.transform.models import AnimationCommand, SceneGraph

# ── Layout constants ────────────────────────────────────────────────────────────

_SLOT_W = 4.0
_HEADER_H = 0.55
_SLOT_H = 0.62
_GAP = 0.04
_STACK_TOP_Y = 2.6

_PALETTE: list[ManimColor] = [BLUE_D, GREEN_C, TEAL_D, GOLD_D, MAROON_D, PURPLE_D]

# IR panel layout (2-column mode)
_IR_PANEL_X = -3.5
_IR_LINE_SPACING = 0.40
_IR_FONT_SIZE = 13
_IR_PANEL_TOP_Y = 2.2
_IR_VIEWPORT_BOT = -3.5

# SSA panel constants
_SSA_PANEL_X = 0.0
_SSA_ROW_W = 3.2
_SSA_ROW_H = 0.42
_SSA_GAP = 0.04
_SSA_TOP_Y = 2.2
_SSA_FONT_SIZE = 14

# 3-column layout overrides (rich-ssa mode)
_3COL_STACK_X = 4.8
_3COL_SLOT_W = 3.2
_3COL_IR_PANEL_X = -4.8
_3COL_IR_FONT_SIZE = 12
_3COL_IR_LINE_SPACING = 0.32
_3COL_DIV1_X = -2.0
_3COL_DIV2_X = 2.5


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


# ── IR panel helpers ────────────────────────────────────────────────────────────


def _build_ir_panel(func_name: str, ir_registry: dict[str, list[str]]) -> VGroup:
    """Build a monospaced VGroup of Text lines for *func_name*'s IR source.

    Each submobject is a single line's Text so that
    ``panel[line_index].get_center()`` gives the correct cursor target.
    """
    lines = ir_registry.get(func_name, [f"(no IR available for @{func_name})"])
    group = VGroup()
    for i, line in enumerate(lines):
        txt = Text(line, font="Monospace", font_size=_IR_FONT_SIZE)
        txt.move_to((_IR_PANEL_X, _IR_PANEL_TOP_Y - i * _IR_LINE_SPACING, 0))
        txt.align_to((_IR_PANEL_X - 2.6, 0, 0), direction=LEFT)
        group.add(txt)
    return group


def _find_line_idx(ir_lines: list[str], text: str) -> int:
    """Return the index of the first display line that contains *text*.

    Both sides are cleaned with ``clean_ir_line`` so that debug metadata
    differences between the event text and the file text don't cause misses.
    Returns 0 if not found.
    """
    clean_text = clean_ir_line(" " + text).strip()
    for i, line in enumerate(ir_lines):
        if clean_text and clean_text in line:
            return i
    return 0


def _call_site_idx(ir_lines: list[str], callee: str) -> int:
    """Return the line index of the call to @callee in *ir_lines*, or 0."""
    for i, line in enumerate(ir_lines):
        if "call" in line and f"@{callee}" in line:
            return i
    return 0


def _ssa_row(name: str, display_value: str, color: ManimColor) -> VGroup:
    """Build an SSA value row for the bridge panel.

    The label text reads ``name = display_value``.
    """
    rect = Rectangle(
        width=_SSA_ROW_W,
        height=_SSA_ROW_H,
        fill_color=color,
        fill_opacity=0.15,
        stroke_color=color,
        stroke_width=1.5,
    )
    label = Text(f"{name} = {display_value}", font="Monospace", font_size=_SSA_FONT_SIZE)
    label.move_to(rect)
    return VGroup(rect, label)


# ── StackRenderer ───────────────────────────────────────────────────────────────

class StackRenderer(CommandDrivenScene):
    """Command-driven stack-frame animation scene.

    Parameters
    ----------
    graph:
        A SceneGraph produced by ``build_scene_graph(stream, mode="stack")``.
    speed:
        Animation speed multiplier.
    title:
        Title text shown at the top.
    ir_mode:
        ``"basic"`` (stack only), ``"rich"`` (IR + stack), or
        ``"rich-ssa"`` (IR + SSA + stack).
    display_lines:
        Mapping of function name to list of IR source display lines.
        Required for ``rich`` and ``rich-ssa`` modes.
    """

    _STACK_X: float = 0.5
    _SLOT_WIDTH: float = _SLOT_W

    def __init__(
        self,
        graph: SceneGraph,
        speed: float = 1.0,
        title: str = "Call Stack  /  LLVManim",
        *,
        ir_mode: str = "basic",
        display_lines: dict[str, list[str]] | None = None,
        **kwargs: object,
    ) -> None:
        super().__init__(graph, speed=speed, title=title, **kwargs)

        self._ir_mode = ir_mode
        self._ir_registry: dict[str, list[str]] = display_lines or {}

        # Adjust layout for rich modes
        if ir_mode == "rich-ssa":
            self._STACK_X = _3COL_STACK_X
            self._SLOT_WIDTH = _3COL_SLOT_W
        elif ir_mode == "rich":
            self._STACK_X = 3.0

        self._cursor_y: float = _STACK_TOP_Y
        self._depth: int = 0
        self._frame_stack: list[tuple[VGroup, list[VGroup]]] = []
        self._frame_names: list[str] = []

        self._register_handler("push_stack_frame", self._handle_push)
        self._register_handler("pop_stack_frame", self._handle_pop)
        self._register_handler("create_stack_slot", self._handle_alloca)
        self._register_handler("highlight_branch", self._handle_branch)

        if ir_mode == "rich-ssa":
            self._register_handler("animate_binop", self._handle_ssa)
            self._register_handler("animate_compare", self._handle_ssa)
            self._register_handler("animate_memory_read", self._handle_ssa)

    def _setup_chrome(self) -> None:
        super()._setup_chrome()
        if self._ir_mode in ("rich", "rich-ssa"):
            self._setup_ir_chrome()
        else:
            col_label = Text("Stack  (grows \u2193)", font_size=21, color=GREY_B)
            col_label.move_to(RIGHT * self._STACK_X + UP * 2.85)
            self.add(col_label)

    def _setup_ir_chrome(self) -> None:
        """Set up the IR panel, dividers, and column labels for rich modes."""
        if self._ir_mode == "rich-ssa":
            ir_x = _3COL_IR_PANEL_X
            div1 = Line(
                (_3COL_DIV1_X, 3.5, 0), (_3COL_DIV1_X, -4.0, 0),
                color=GREY_D, stroke_width=1,
            )
            div2 = Line(
                (_3COL_DIV2_X, 3.5, 0), (_3COL_DIV2_X, -4.0, 0),
                color=GREY_D, stroke_width=1,
            )
            self.add(div1, div2)
            ssa_lbl = Text("SSA Values", font_size=21, color=GREY_B)
            ssa_lbl.move_to((_SSA_PANEL_X, 2.85, 0))
            self.add(ssa_lbl)
        else:
            ir_x = _IR_PANEL_X
            vdiv = Line(UP * 3.5, DOWN * 4.0, color=GREY_D, stroke_width=1)
            self.add(vdiv)

        ir_lbl = Text("IR Source", font_size=21, color=GREY_B)
        ir_lbl.move_to((ir_x, 2.85, 0))
        self.add(ir_lbl)

        stack_lbl = Text("Stack  (grows \u2193)", font_size=21, color=GREY_B)
        stack_lbl.move_to(RIGHT * self._STACK_X + UP * 2.85)
        self.add(stack_lbl)

        # Initialise the IR panel to the first pushed function.
        first_func = next(
            (cmd.params.get("function_name", "main")
             for cmd in self._graph.commands
             if cmd.action == "push_stack_frame"),
            "main",
        )

        self._ir_panel: VGroup = _build_ir_panel(first_func, self._ir_registry)
        if self._ir_mode == "rich-ssa":
            self._reposition_ir_panel(self._ir_panel)
        self.add(self._ir_panel)
        self._ir_cursor = SurroundingRectangle(
            self._ir_panel[0], color=YELLOW, buff=0.06, stroke_width=2
        )
        self.add(self._ir_cursor)

        self._current_func: str = first_func
        self._call_site_stack: list[tuple[str, int]] = []
        self._panel_scroll: float = 0.0

        # SSA panel state
        self._ssa_cursor_y: float = _SSA_TOP_Y
        self._ssa_entries: list[tuple[VGroup, str]] = []

    # ── IR panel methods ────────────────────────────────────────────────────

    def _scroll_to_line(self, idx: int) -> None:
        """Shift the panel (and cursor) so that line *idx* is within the viewport."""
        spacing = _3COL_IR_LINE_SPACING if self._ir_mode == "rich-ssa" else _IR_LINE_SPACING
        line_y = _IR_PANEL_TOP_Y - idx * spacing + self._panel_scroll
        if _IR_VIEWPORT_BOT <= line_y <= _IR_PANEL_TOP_Y + spacing:
            return
        target_y = (_IR_PANEL_TOP_Y + _IR_VIEWPORT_BOT) / 2
        delta = target_y - line_y
        self.play(
            self._ir_panel.animate.shift(UP * delta),
            self._ir_cursor.animate.shift(UP * delta),
            run_time=self._rt(0.25),
        )
        self._panel_scroll += delta

    def _swap_panel(self, new_func: str, target_line: int = 0) -> None:
        """FadeTransform the current IR panel to *new_func*'s panel."""
        new_panel = _build_ir_panel(new_func, self._ir_registry)
        if self._ir_mode == "rich-ssa":
            self._reposition_ir_panel(new_panel)
        self.play(FadeTransform(self._ir_panel, new_panel), run_time=self._rt(0.4))
        self._ir_panel = new_panel
        self._current_func = new_func
        self._panel_scroll = 0.0
        safe_idx = min(target_line, len(self._ir_panel) - 1)
        new_cursor = SurroundingRectangle(
            self._ir_panel[safe_idx], color=YELLOW, buff=0.06, stroke_width=2
        )
        self.play(FadeTransform(self._ir_cursor, new_cursor), run_time=self._rt(0.25))
        self._ir_cursor = new_cursor
        self._scroll_to_line(safe_idx)

    def _advance_cursor(self, line_index: int) -> None:
        """Scroll the panel if needed, then animate the cursor to *line_index*."""
        safe_idx = min(line_index, len(self._ir_panel) - 1)
        self._scroll_to_line(safe_idx)
        new_cursor = SurroundingRectangle(
            self._ir_panel[safe_idx], color=YELLOW, buff=0.06, stroke_width=2
        )
        self.play(self._ir_cursor.animate.become(new_cursor), run_time=self._rt(0.3))

    def _reposition_ir_panel(self, panel: VGroup) -> None:
        """Shift an IR panel to 3-column layout position."""
        for i, line_mob in enumerate(panel):
            line_mob.move_to((_3COL_IR_PANEL_X, _IR_PANEL_TOP_Y - i * _3COL_IR_LINE_SPACING, 0))
            line_mob.align_to((_3COL_IR_PANEL_X - 2.2, 0, 0), direction=LEFT)
            line_mob.set(font_size=_3COL_IR_FONT_SIZE)

    # ── IR cursor integration ───────────────────────────────────────────────

    def _ir_on_push(self, func_name: str) -> None:
        """Move IR cursor to call site and swap panel to callee."""
        if self._ir_mode not in ("rich", "rich-ssa"):
            return
        caller_lines = self._ir_registry.get(self._current_func, [])
        call_line = _call_site_idx(caller_lines, func_name)
        self._advance_cursor(call_line)
        self._call_site_stack.append((self._current_func, call_line))
        self._swap_panel(func_name, target_line=0)

    def _ir_on_alloca(self, ir_text: str) -> None:
        """Move IR cursor to the alloca instruction."""
        if self._ir_mode not in ("rich", "rich-ssa"):
            return
        ir_lines = self._ir_registry.get(self._current_func, [])
        idx = _find_line_idx(ir_lines, ir_text)
        self._advance_cursor(idx)

    def _ir_on_pop(self, ir_text: str) -> None:
        """Move IR cursor to ret, then restore caller panel."""
        if self._ir_mode not in ("rich", "rich-ssa"):
            return
        ir_lines = self._ir_registry.get(self._current_func, [])
        idx = _find_line_idx(ir_lines, ir_text)
        self._advance_cursor(idx)
        if self._call_site_stack:
            restore_func, restore_line = self._call_site_stack.pop()
            self._swap_panel(restore_func, target_line=restore_line)

    def _ir_on_ssa(self, ir_text: str) -> None:
        """Move IR cursor to the SSA instruction."""
        if self._ir_mode not in ("rich", "rich-ssa"):
            return
        ir_lines = self._ir_registry.get(self._current_func, [])
        idx = _find_line_idx(ir_lines, ir_text)
        self._advance_cursor(idx)

    # ── Handlers ────────────────────────────────────────────────────────────

    def _color(self) -> ManimColor:
        return _PALETTE[self._depth % len(_PALETTE)]

    def _handle_push(self, cmd: AnimationCommand) -> None:
        func_name = cmd.params.get("function_name", "")
        self._ir_on_push(func_name)
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
        ir_text = cmd.event.text if cmd.event else ""
        self._ir_on_pop(ir_text)
        popped_func = self._frame_names.pop() if self._frame_names else ""
        header, slots = self._frame_stack.pop()
        self._depth -= 1
        self._cursor_y += _HEADER_H + _GAP + len(slots) * (_SLOT_H + _GAP)
        mobs_out = slots[::-1] + [header]
        mobs_out.extend(self._ssa_pop_cleanup(popped_func))
        self.play(*[FadeOut(m, shift=UP * 0.2) for m in mobs_out], run_time=self._rt(0.55))
        self._ssa_after_pop()

    def _handle_alloca(self, cmd: AnimationCommand) -> None:
        if not self._frame_stack:
            return
        slot_text = cmd.event.text if cmd.event else cmd.params.get("slot_name", "")
        self._ir_on_alloca(slot_text)
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

    def _handle_ssa(self, cmd: AnimationCommand) -> None:
        """Handle animate_binop / animate_compare / animate_memory_read."""
        ir_text = cmd.event.text if cmd.event else ""
        self._ir_on_ssa(ir_text)
        action_map = {
            "animate_binop": "binop",
            "animate_compare": "compare",
            "animate_memory_read": "load",
        }
        action = action_map.get(cmd.action, cmd.action)
        operands = cmd.params.get("operands", [])
        func_name = self._frame_names[-1] if self._frame_names else ""
        self._add_ssa_value(action, ir_text, operands, func_name)

    # ── SSA panel methods ───────────────────────────────────────────────────

    def _add_ssa_value(
        self, action: str, ir_text: str, operands: list[str], func_name: str
    ) -> None:
        """Parse the instruction, format the display value, and animate a new SSA row."""
        name = extract_ssa_name(ir_text)
        if not name:
            return
        display_value = format_display_value(action, ir_text, operands)
        color = OP_COLORS.get(action, GREY_B)
        mob = _ssa_row(name, display_value, color)
        mob.move_to((_SSA_PANEL_X, self._ssa_cursor_y - _SSA_ROW_H / 2, 0))
        self._ssa_cursor_y -= _SSA_ROW_H + _SSA_GAP
        self._ssa_entries.append((mob, func_name))
        mob[1].set_color(YELLOW)
        self.play(FadeIn(mob, shift=DOWN * 0.1), run_time=self._rt(0.3))
        self.play(mob[1].animate.set_color(WHITE), run_time=self._rt(0.2))

    def _ssa_pop_cleanup(self, func_name: str) -> list[VGroup]:
        """Return SSA mobs owned by *func_name* for fade-out."""
        if self._ir_mode != "rich-ssa":
            return []
        ssa_out = [mob for mob, owner in self._ssa_entries if owner == func_name]
        self._ssa_entries = [(m, o) for m, o in self._ssa_entries if o != func_name]
        if ssa_out:
            self._ssa_cursor_y += len(ssa_out) * (_SSA_ROW_H + _SSA_GAP)
        return ssa_out

    def _ssa_after_pop(self) -> None:
        """Relayout remaining SSA entries after a pop fade-out."""
        if self._ir_mode != "rich-ssa" or not self._ssa_entries:
            return
        new_y = _SSA_TOP_Y
        anims = []
        for mob, _ in self._ssa_entries:
            target_y = new_y - _SSA_ROW_H / 2
            delta = target_y - mob.get_center()[1]
            if abs(delta) > 0.001:
                anims.append(mob.animate.shift(UP * delta))
            new_y -= _SSA_ROW_H + _SSA_GAP
        self._ssa_cursor_y = new_y
        if anims:
            self.play(*anims, run_time=self._rt(0.25))
