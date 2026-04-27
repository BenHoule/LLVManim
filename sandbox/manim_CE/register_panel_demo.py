"""
SSA Bridge Panel prototype -- Manim Community Edition.

3-column Spotlight layout: IR Source | SSA Values | Stack.

The middle column shows symbolic SSA computation results for binop, compare,
and load operations.  Values persist until their owning stack frame is popped.

The ``display_value`` field is the *only* thing the renderer reads.  Today a
symbolic formatter produces strings like ``2 x %2``; a future runtime-trace
integration can swap in numeric values (e.g. ``84``) without touching any
rendering code.

Run (low quality, fast preview):
    uv run manim -pql sandbox/manim_CE/register_panel_demo.py RegisterPanelDemo

Run (high quality):
    uv run manim -qh sandbox/manim_CE/register_panel_demo.py RegisterPanelDemo

TODO: When numeric runtime values become available (e.g. extended
      SanitizerCoverage trace), swap _format_display_value() to return
      concrete values.  The rendering pipeline only reads display_value
      so no other code needs to change.
"""

from __future__ import annotations

import re
from typing import NamedTuple

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
    Scene,
    SurroundingRectangle,
    Text,
    VGroup,
)

# ── Data model ─────────────────────────────────────────────────────────────────


class _RegEntry(NamedTuple):
    """One SSA value displayed in the bridge panel.

    ``display_value`` is the **only** field the renderer reads for the label
    text.  Today it holds a symbolic expression; in the future it can hold a
    concrete numeric string from a runtime trace -- no rendering changes needed.
    """

    name: str  # SSA result name, e.g. "%mul"
    display_value: str  # symbolic now ("2 x %2"), numeric later ("84")
    op_type: str  # "binop" | "compare" | "load"
    owning_frame: str  # function name -- cleared on pop


# ── Symbolic expression formatter (the single swap-point for future numerics) ─


_BINOP_SYMBOLS: dict[str, str] = {
    "add": "+",
    "sub": "−",
    "mul": "×",
    "udiv": "÷",
    "sdiv": "÷",
    "urem": "%",
    "srem": "%",
    "shl": "<<",
    "lshr": ">>",
    "ashr": ">>",
    "and": "&",
    "or": "|",
    "xor": "^",
    "fadd": "+",
    "fsub": "−",
    "fmul": "×",
    "fdiv": "÷",
    "frem": "%",
}

_CMP_PREDICATES: dict[str, str] = {
    "eq": "==",
    "ne": "!=",
    "slt": "<",
    "sle": "<=",
    "sgt": ">",
    "sge": ">=",
    "ult": "<",
    "ule": "<=",
    "ugt": ">",
    "uge": ">=",
    # float predicates
    "oeq": "==",
    "one": "!=",
    "olt": "<",
    "ole": "<=",
    "ogt": ">",
    "oge": ">=",
    "ueq": "==",
    "une": "!=",
}


def _extract_ssa_name(ir_text: str) -> str:
    """Extract the LHS SSA name from an instruction like ``%mul = mul ...``."""
    m = re.match(r"(%[\w.]+)\s*=", ir_text.strip())
    return m.group(1) if m else ""


def _extract_opcode(ir_text: str) -> str:
    """Extract the opcode from after the ``=`` sign."""
    m = re.match(r"%[\w.]+\s*=\s*(\w+)", ir_text.strip())
    return m.group(1) if m else ""


def _format_binop(ir_text: str, operands: list[str]) -> str:
    opcode = _extract_opcode(ir_text)
    sym = _BINOP_SYMBOLS.get(opcode, opcode)
    if len(operands) >= 2:
        return f"{operands[0]} {sym} {operands[1]}"
    return ir_text.split("=", 1)[-1].strip()


def _format_compare(ir_text: str, operands: list[str]) -> str:
    # Extract predicate from text like "icmp slt i32 %2, 100"
    m = re.search(r"(?:icmp|fcmp)\s+(\w+)", ir_text)
    pred = m.group(1) if m else ""
    sym = _CMP_PREDICATES.get(pred, pred)
    if len(operands) >= 2:
        return f"{operands[0]} {sym} {operands[1]}"
    return ir_text.split("=", 1)[-1].strip()


def _format_load(operands: list[str]) -> str:
    if operands:
        return f"load {operands[0]}"
    return "load ?"


def _format_display_value(action: str, ir_text: str, operands: list[str]) -> str:
    """Produce the human-readable display string for an SSA value.

    **This is the single function to swap when numeric runtime values arrive.**
    Today it returns symbolic expressions; in the future, return
    ``str(concrete_value)`` here and nothing else changes.
    """
    if action == "binop":
        return _format_binop(ir_text, operands)
    if action == "compare":
        return _format_compare(ir_text, operands)
    if action == "load":
        return _format_load(operands)
    return ir_text


# ── Hardcoded IR registry (double.ll) ─────────────────────────────────────────

_IR_REGISTRY: dict[str, dict] = {
    "main": {
        "lines": [
            "define i32 @main() {",
            "entry:",
            "  %retval = alloca i32",
            "  %r = alloca i32",
            "  %p = alloca ptr",
            "  %call = call ptr @malloc(i64 4)",
            "  store ptr %call, ptr %p",
            "  call void @init(ptr %p)",
            "  br label %while.cond",
            "while.cond:",
            "  %1 = load ptr, ptr %p",
            "  %2 = load i32, ptr %1",
            "  %cmp = icmp slt i32 %2, 100",
            "  br i1 %cmp, %while.body, %while.end",
            "while.body:",
            "  %call1 = call i32 @double_1(ptr %p)",
            "  br label %while.cond",
            "while.end:",
            "  %3 = load i32, ptr %r",
            "  ret i32 %3",
            "}",
        ],
        "event_map": {
            "%retval = alloca": 2,
            "%r = alloca": 3,
            "%p = alloca": 4,
            "%1 = load ptr": 10,
            "%2 = load i32": 11,
            "%cmp = icmp": 12,
            "%3 = load i32": 18,
            "ret i32": 19,
        },
        "call_sites": {
            "init": 7,
            "double_1": 15,
        },
    },
    "init": {
        "lines": [
            "define void @init(ptr %p) {",
            "entry:",
            "  %p.addr = alloca ptr",
            "  store ptr %p, ptr %p.addr",
            "  %0 = load ptr, ptr %p.addr",
            "  store i32 1, ptr %0",
            "  ret void",
            "}",
        ],
        "event_map": {
            "%p.addr = alloca": 2,
            "%0 = load ptr": 4,
            "ret void": 6,
        },
        "call_sites": {},
    },
    "double_1": {
        "lines": [
            "define i32 @double_1(ptr %p) {",
            "entry:",
            "  %p.addr = alloca ptr",
            "  %tmp = alloca i32",
            "  store ptr %p, ptr %p.addr",
            "  %0 = load ptr, ptr %p.addr",
            "  %1 = load i32, ptr %0",
            "  store i32 %1, ptr %tmp",
            "  %2 = load i32, ptr %tmp",
            "  %mul = mul nsw i32 2, %2",
            "  %3 = load ptr, ptr %p.addr",
            "  store i32 %mul, ptr %3",
            "  %4 = load ptr, ptr %p.addr",
            "  %5 = load i32, ptr %4",
            "  ret i32 %5",
            "}",
        ],
        "event_map": {
            "%p.addr = alloca": 2,
            "%tmp = alloca": 3,
            "%2 = load i32": 8,
            "%mul = mul": 9,
            "%5 = load i32": 13,
            "ret i32": 14,
        },
        "call_sites": {},
    },
}

# ── Hardcoded execution trace (double.ll: main → init → double_1 loop) ────────
#
# Format: (action, func_name, ir_text, operands)
# Actions: "push", "alloca", "pop", "binop", "compare", "load"
#
# This models one loop iteration:
#   main entry → call init → init body → ret → call double_1 → double_1 body →
#   ret → while.cond check → while.end → ret

_TRACE: list[tuple[str, str, str, list[str]]] = [
    # ── @main entry ──
    ("push", "main", "", []),
    ("alloca", "main", "%retval = alloca i32", []),
    ("alloca", "main", "%r = alloca i32", []),
    ("alloca", "main", "%p = alloca ptr", []),
    # ── call @init ──
    ("push", "init", "", []),
    ("alloca", "init", "%p.addr = alloca ptr", []),
    ("load", "init", "%0 = load ptr, ptr %p.addr", ["%p.addr"]),
    ("pop", "init", "ret void", []),
    # ── call @double_1 ──
    ("push", "double_1", "", []),
    ("alloca", "double_1", "%p.addr = alloca ptr", []),
    ("alloca", "double_1", "%tmp = alloca i32", []),
    ("load", "double_1", "%2 = load i32, ptr %tmp", ["%tmp"]),
    ("binop", "double_1", "%mul = mul nsw i32 2, %2", ["2", "%2"]),
    ("pop", "double_1", "ret i32 %5", []),
    # ── back in @main: while.cond check ──
    ("load", "main", "%2 = load i32, ptr %1", ["%1"]),
    ("compare", "main", "%cmp = icmp slt i32 %2, 100", ["%2", "100"]),
    # ── while.end: return ──
    ("pop", "main", "ret i32 %3", []),
]


# ── Layout constants ───────────────────────────────────────────────────────────

_SLOT_W = 3.2  # width of every stack cell (narrower for 3-col)
_HEADER_H = 0.55
_SLOT_H = 0.55
_GAP = 0.04
_STACK_TOP_Y = 2.4

_PALETTE: list[ManimColor] = [BLUE_D, GREEN_C, TEAL_D, GOLD_D, MAROON_D, PURPLE_D]

# Column positions
_IR_PANEL_X = -4.8
_SSA_PANEL_X = 0.0
_STACK_X = 4.8

# IR panel
_IR_LINE_SPACING = 0.32
_IR_FONT_SIZE = 12
_IR_PANEL_TOP_Y = 2.2

# SSA panel
_SSA_ROW_W = 3.2
_SSA_ROW_H = 0.42
_SSA_GAP = 0.04
_SSA_TOP_Y = 2.2
_SSA_FONT_SIZE = 14

# Op-type → tint colour for SSA rows
_OP_COLORS: dict[str, ManimColor] = {
    "binop": GREEN_C,
    "compare": GOLD_D,
    "load": BLUE_D,
}


# ── Mobject factories ──────────────────────────────────────────────────────────


def _frame_header(func_name: str, color: ManimColor) -> VGroup:
    rect = Rectangle(
        width=_SLOT_W,
        height=_HEADER_H,
        fill_color=color,
        fill_opacity=0.85,
        stroke_color=color,
        stroke_width=2,
    )
    label = Text(f"@{func_name}", font="Monospace", font_size=20, color=WHITE, weight=BOLD)
    label.move_to(rect)
    return VGroup(rect, label)


def _slot_cell(slot_text: str, color: ManimColor) -> VGroup:
    rect = Rectangle(
        width=_SLOT_W,
        height=_SLOT_H,
        fill_color=color,
        fill_opacity=0.18,
        stroke_color=color,
        stroke_width=1.5,
    )
    label = Text(slot_text, font="Monospace", font_size=16)
    label.move_to(rect)
    return VGroup(rect, label)


def _ssa_row(name: str, display_value: str, color: ManimColor) -> VGroup:
    """Build an SSA value row for the bridge panel.

    The label text reads ``name = display_value``.  The renderer only uses
    ``display_value`` -- this is the future-proofing seam for numeric values.
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


# ── IR panel helpers ───────────────────────────────────────────────────────────


def _build_ir_panel(func_name: str) -> VGroup:
    entry = _IR_REGISTRY.get(func_name, {})
    lines: list[str] = entry.get("lines", [f"(no IR for {func_name})"])
    group = VGroup()
    for i, line in enumerate(lines):
        txt = Text(line, font="Monospace", font_size=_IR_FONT_SIZE)
        txt.move_to((_IR_PANEL_X, _IR_PANEL_TOP_Y - i * _IR_LINE_SPACING, 0))
        txt.align_to((_IR_PANEL_X - 2.2, 0, 0), direction=LEFT)
        group.add(txt)
    return group


def _cursor_line_index(func_name: str, ir_text: str) -> int:
    entry = _IR_REGISTRY.get(func_name, {})
    event_map: dict[str, int] = entry.get("event_map", {})
    for fragment, idx in event_map.items():
        if fragment and fragment in ir_text:
            return idx
    return 0


def _call_site_line(caller_func: str, callee_func: str) -> int:
    entry = _IR_REGISTRY.get(caller_func, {})
    return entry.get("call_sites", {}).get(callee_func, 0)


# ── Scene ──────────────────────────────────────────────────────────────────────


class RegisterPanelDemo(Scene):
    """3-column Spotlight layout: IR Source | SSA Values | Stack.

    Binop, compare, and load operations produce SSA value rows in the middle
    panel.  Rows persist until their owning stack frame is popped.

    Visual design
    ─────────────
    - IR cursor (yellow SurroundingRectangle) tracks the current instruction
    - SSA rows appear with a yellow flash then settle to their op-type colour
    - Stack frames use the existing push/alloca/pop mechanics from stack_demo
    """

    def construct(self) -> None:
        # ── State ──
        self._cursor_y: float = _STACK_TOP_Y
        self._depth: int = 0
        self._frame_stack: list[tuple[VGroup, list[VGroup]]] = []
        self._frame_names: list[str] = []
        # SSA panel state: list of (mobject, owning_function)
        self._ssa_entries: list[tuple[VGroup, str]] = []
        self._ssa_cursor_y: float = _SSA_TOP_Y

        self._setup_chrome()
        self._run_trace()
        self.wait(1.0)

    # ── Chrome ─────────────────────────────────────────────────────────────

    def _setup_chrome(self) -> None:
        # Title
        title = Text("Call Stack  /  double.ll", font_size=28, weight=BOLD)
        title.to_edge(UP, buff=0.25)
        self.add(title)

        rule = Line(
            title.get_bottom() + DOWN * 0.10 + LEFT * 7.1,
            title.get_bottom() + DOWN * 0.10 + RIGHT * 7.1,
            color=GREY_D,
            stroke_width=1,
        )
        self.add(rule)

        # Vertical dividers
        div1_x = -2.0
        div2_x = 2.5
        for x in (div1_x, div2_x):
            self.add(
                Line(
                    UP * 3.3 + RIGHT * x,
                    DOWN * 4.0 + RIGHT * x,
                    color=GREY_D,
                    stroke_width=1,
                )
            )

        # Column headers
        ir_lbl = Text("IR Source", font_size=19, color=GREY_B)
        ir_lbl.move_to((_IR_PANEL_X, 2.7, 0))
        self.add(ir_lbl)

        ssa_lbl = Text("SSA Values", font_size=19, color=GREY_B)
        ssa_lbl.move_to((_SSA_PANEL_X, 2.7, 0))
        self.add(ssa_lbl)

        stack_lbl = Text("Stack  (grows ↓)", font_size=19, color=GREY_B)
        stack_lbl.move_to((_STACK_X, 2.7, 0))
        self.add(stack_lbl)

        # IR panel -- starts with @main
        self._ir_panel: VGroup = _build_ir_panel("main")
        self.add(self._ir_panel)
        self._ir_cursor = SurroundingRectangle(
            self._ir_panel[0],
            color=YELLOW,
            buff=0.04,
            stroke_width=2,
        )
        self.add(self._ir_cursor)
        self._current_func: str = "main"
        self._call_site_stack: list[tuple[str, int]] = []

    # ── IR cursor ──────────────────────────────────────────────────────────

    def _advance_cursor(self, line_index: int) -> None:
        safe_idx = min(line_index, len(self._ir_panel) - 1)
        new_cursor = SurroundingRectangle(
            self._ir_panel[safe_idx],
            color=YELLOW,
            buff=0.04,
            stroke_width=2,
        )
        self.play(self._ir_cursor.animate.become(new_cursor), run_time=0.25)

    def _swap_panel(self, new_func: str, target_line: int = 0) -> None:
        new_panel = _build_ir_panel(new_func)
        self.play(FadeTransform(self._ir_panel, new_panel), run_time=0.35)
        self._ir_panel = new_panel
        self._current_func = new_func
        safe_idx = min(target_line, len(self._ir_panel) - 1)
        new_cursor = SurroundingRectangle(
            self._ir_panel[safe_idx],
            color=YELLOW,
            buff=0.04,
            stroke_width=2,
        )
        self.play(FadeTransform(self._ir_cursor, new_cursor), run_time=0.2)
        self._ir_cursor = new_cursor

    def _ir_step(self, action: str, func_name: str, ir_text: str) -> None:
        """Advance IR cursor for the current action (push/alloca/pop/load/binop/compare)."""
        bare = func_name.lstrip("@")

        if action == "push":
            call_line = _call_site_line(self._current_func, bare)
            self._advance_cursor(call_line)
            self._call_site_stack.append((self._current_func, call_line))
            self._swap_panel(bare, target_line=0)

        elif action == "pop":
            idx = _cursor_line_index(bare, ir_text)
            self._advance_cursor(idx)
            if self._call_site_stack:
                restore_func, restore_line = self._call_site_stack.pop()
                self._swap_panel(restore_func, target_line=restore_line)

        elif action in ("alloca", "load", "binop", "compare"):
            idx = _cursor_line_index(bare, ir_text)
            self._advance_cursor(idx)

    # ── Stack mechanics ────────────────────────────────────────────────────

    def _color(self) -> ManimColor:
        return _PALETTE[self._depth % len(_PALETTE)]

    def _push(self, func_name: str) -> None:
        color = self._color()
        mob = _frame_header(func_name, color)
        mob.move_to(RIGHT * _STACK_X + UP * (self._cursor_y - _HEADER_H / 2))
        self._cursor_y -= _HEADER_H + _GAP
        self._depth += 1
        self._frame_stack.append((mob, []))
        self._frame_names.append(func_name)
        mob[1].set_color(YELLOW)
        self.play(FadeIn(mob, shift=DOWN * 0.2), run_time=0.4)
        self.play(mob[1].animate.set_color(WHITE), run_time=0.25)

    def _alloca(self, slot_text: str) -> None:
        if not self._frame_stack:
            return
        color = _PALETTE[(self._depth - 1) % len(_PALETTE)]
        mob = _slot_cell(slot_text, color)
        mob.move_to(RIGHT * _STACK_X + UP * (self._cursor_y - _SLOT_H / 2))
        self._cursor_y -= _SLOT_H + _GAP
        self._frame_stack[-1][1].append(mob)
        mob[1].set_color(YELLOW)
        self.play(FadeIn(mob, shift=DOWN * 0.12), run_time=0.35)
        self.play(mob[1].animate.set_color(WHITE), run_time=0.25)

    def _pop(self, func_name: str) -> None:
        if not self._frame_stack:
            return
        if self._frame_names:
            self._frame_names.pop()
        header, slots = self._frame_stack.pop()
        self._depth -= 1
        self._cursor_y += _HEADER_H + _GAP + len(slots) * (_SLOT_H + _GAP)
        mobs_out = slots[::-1] + [header]

        # Also fade out SSA entries owned by this function
        ssa_out = [mob for mob, owner in self._ssa_entries if owner == func_name]
        self._ssa_entries = [(m, o) for m, o in self._ssa_entries if o != func_name]

        all_out = mobs_out + ssa_out
        self.play(*[FadeOut(m, shift=UP * 0.15) for m in all_out], run_time=0.5)

        # Reclaim SSA panel Y space: shift remaining rows up
        if ssa_out:
            reclaim = len(ssa_out) * (_SSA_ROW_H + _SSA_GAP)
            self._ssa_cursor_y += reclaim
            remaining = [mob for mob, _ in self._ssa_entries]
            if remaining:
                self.play(
                    *[m.animate.shift(UP * reclaim) for m in remaining],
                    run_time=0.25,
                )

    # ── SSA bridge panel ───────────────────────────────────────────────────

    def _add_ssa_value(
        self, action: str, ir_text: str, operands: list[str], func_name: str
    ) -> None:
        """Parse the instruction, format the display value, and animate a new SSA row."""
        name = _extract_ssa_name(ir_text)
        if not name:
            return

        display_value = _format_display_value(action, ir_text, operands)
        color = _OP_COLORS.get(action, GREY_B)

        mob = _ssa_row(name, display_value, color)
        mob.move_to((_SSA_PANEL_X, self._ssa_cursor_y - _SSA_ROW_H / 2, 0))
        self._ssa_cursor_y -= _SSA_ROW_H + _SSA_GAP

        self._ssa_entries.append((mob, func_name))

        # Yellow flash on arrive, then settle to resting colour
        mob[1].set_color(YELLOW)
        self.play(FadeIn(mob, shift=DOWN * 0.1), run_time=0.3)
        self.play(mob[1].animate.set_color(WHITE), run_time=0.2)

    # ── Main loop ──────────────────────────────────────────────────────────

    def _run_trace(self) -> None:
        for action, func_name, ir_text, operands in _TRACE:
            # Advance IR cursor first
            self._ir_step(action, func_name, ir_text)

            if action == "push":
                self._push(func_name)
            elif action == "alloca":
                self._alloca(ir_text)
            elif action == "pop":
                self._pop(func_name)
            elif action in ("binop", "compare", "load"):
                self._add_ssa_value(action, ir_text, operands, func_name)
