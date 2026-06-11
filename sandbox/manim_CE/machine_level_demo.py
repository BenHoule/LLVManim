"""
Machine-Level Execution Visualization -- Manim Community Edition.

Two-panel layout:
  Left  (40%): LLVM IR Source  -- cursor tracks the active instruction
  Right (60%): x86-64 CPU viz  -- styled CPU die, register file, flags, stack memory

Value tokens (floating Text) arc from the IR cursor to their destination
(register row or memory cell) to show where each value ends up in hardware.

Demo subject: ``double_1`` from ``double.ll``
  Concrete values are hardcoded (input = 1 from @init, output = 2) to make
  the flow visually obvious.

Run (low quality, fast preview):
    uv run manim -pql sandbox/manim_CE/machine_level_demo.py MachineLevelDemo

Run (high quality):
    uv run manim -qh sandbox/manim_CE/machine_level_demo.py MachineLevelDemo

TODO (future design alternatives):
  Design 1: Replace SSA panel with an x86 instruction stream (IR -> x86 stream -> hardware)
  Design 2: Add C source as left panel, shift IR to centre (C -> IR -> hardware layering)
"""

from __future__ import annotations

import math
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
    MAROON_C,
    PI,
    RIGHT,
    TEAL_D,
    UP,
    WHITE,
    YELLOW,
    ArcBetweenPoints,
    FadeIn,
    FadeOut,
    Line,
    ManimColor,
    MoveAlongPath,
    Rectangle,
    RoundedRectangle,
    Scene,
    SurroundingRectangle,
    Text,
    VGroup,
)

# ── Layout constants ───────────────────────────────────────────────────────────

# Panel horizontal split: left panel centre at -3.2, right panel centre at +3.2
_LEFT_PANEL_X = -3.2
_RIGHT_PANEL_X = 3.2
_DIVIDER_X = -0.55

# IR source panel
_IR_TOP_Y = 2.8
_IR_LINE_H = 0.31
_IR_FONT = 13
_IR_INDENT_X = _LEFT_PANEL_X - 2.5  # left-align anchor

# CPU die (right panel)
_DIE_W = 6.0
_DIE_H = 4.6
_DIE_CENTER_X = _RIGHT_PANEL_X
_DIE_CENTER_Y = 0.6

# Register file (inside die)
_REG_TOP_Y = _DIE_CENTER_Y + _DIE_H / 2 - 0.35
_REG_ROW_W = 5.4
_REG_ROW_H = 0.45
_REG_GAP = 0.07
_REG_CENTER_X = _DIE_CENTER_X

# Flags (inside die, below register file)
_FLAG_Y = _DIE_CENTER_Y - _DIE_H / 2 + 0.45
_FLAG_SQ = 0.42

# Stack memory (below die)
_MEM_TOP_Y = _DIE_CENTER_Y - _DIE_H / 2 - 0.15
_MEM_ROW_H = 0.44
_MEM_ROW_W = 5.4
_MEM_GAP = 0.06

# Colours
_COL_ARG = TEAL_D  # rdi (argument register)
_COL_GEN = GREEN_C  # rax / ecx  (general-purpose / result)
_COL_STK = GOLD_D  # rsp / rbp  (stack pointers)
_COL_FLAG_ON = MAROON_C  # flag bit when set
_COL_FLAG_OFF = GREY_D  # flag bit when clear


# ── Data model ─────────────────────────────────────────────────────────────────


class _HWRow(NamedTuple):
    """One row in the register file or stack memory table."""

    name: str  # display name (e.g. "rax / eax")
    value: str  # current value string (mutated via _update_row)
    color: ManimColor  # category colour
    name_mob: Text  # the label Text inside the row
    value_mob: Text  # the value Text inside the row (replaced on update)
    bg_rect: Rectangle  # the background rectangle (used for flash)


class _FlagBit(NamedTuple):
    """One flag bit in the FLAGS display."""

    name: str
    bg: Rectangle
    label: Text


class _Step(NamedTuple):
    """One instruction step in the walkthrough."""

    ir_index: int  # 0-based index into _IR_LINES
    x86_label: str  # x86 instruction text shown below cursor
    token_label: str  # value token text (e.g. "1", "ptr", "2×1")
    # Each token_move is (src_key, dst_key) where keys are register/memory row names
    # or special strings: "ir_cursor" = the IR cursor location
    token_moves: list[tuple[str, str]]
    # dict of {row_name: new_value} to apply after the token lands
    value_updates: dict[str, str]
    # list of flag names to light up (ZF, SF, OF, CF)
    flags_set: list[str]
    flags_clear: list[str]


# ── IR source text (double_1 only) ─────────────────────────────────────────────

_IR_LINES: list[str] = [
    "define i32 @double_1(ptr %p) {",  # 0
    "entry:",  # 1
    "  %p.addr = alloca ptr",  # 2
    "  %tmp    = alloca i32",  # 3
    "  store ptr %p, ptr %p.addr",  # 4
    "  %0 = load ptr, ptr %p.addr",  # 5
    "  %1 = load i32, ptr %0",  # 6
    "  store i32 %1, ptr %tmp",  # 7
    "  %2 = load i32, ptr %tmp",  # 8
    "  %mul = mul nsw i32 2, %2",  # 9
    "  %3 = load ptr, ptr %p.addr",  # 10
    "  store i32 %mul, ptr %3",  # 11
    "  %4 = load ptr, ptr %p.addr",  # 12
    "  %5 = load i32, ptr %4",  # 13
    "  ret i32 %5",  # 14
    "}",  # 15
]

# ── Execution steps ────────────────────────────────────────────────────────────
#
# Concrete values for one call of double_1 where the heap holds value 1:
#   rdi  = 0xABCD  (heap pointer passed by caller -- shown as "ptr")
#   *rdi = 1       (value stored in heap by @init)
#   result = 2 * 1 = 2
#
# Register name keys used in token_moves and value_updates:
#   "rdi", "rax", "ecx", "rcx", "rsp", "rbp"
#   "[rbp-8]", "[rbp-4]"

_STEPS: list[_Step] = [
    _Step(
        ir_index=2,
        x86_label="sub  rsp, 8",
        token_label="",
        token_moves=[],
        value_updates={"rsp": "rsp-8", "[rbp-8]": "??"},
        flags_set=[],
        flags_clear=[],
    ),
    _Step(
        ir_index=3,
        x86_label="sub  rsp, 4",
        token_label="",
        token_moves=[],
        value_updates={"rsp": "rsp-12", "[rbp-4]": "??"},
        flags_set=[],
        flags_clear=[],
    ),
    _Step(
        ir_index=4,
        x86_label="mov  [rbp-8], rdi",
        token_label="ptr",
        token_moves=[("rdi", "[rbp-8]")],
        value_updates={"[rbp-8]": "ptr"},
        flags_set=[],
        flags_clear=[],
    ),
    _Step(
        ir_index=5,
        x86_label="mov  rax, [rbp-8]",
        token_label="ptr",
        token_moves=[("[rbp-8]", "rax")],
        value_updates={"rax": "ptr"},
        flags_set=[],
        flags_clear=[],
    ),
    _Step(
        ir_index=6,
        x86_label="mov  ecx, [rax]",
        token_label="1",
        token_moves=[("rax", "ecx")],
        value_updates={"ecx": "1"},
        flags_set=[],
        flags_clear=[],
    ),
    _Step(
        ir_index=7,
        x86_label="mov  [rbp-4], ecx",
        token_label="1",
        token_moves=[("ecx", "[rbp-4]")],
        value_updates={"[rbp-4]": "1"},
        flags_set=[],
        flags_clear=[],
    ),
    _Step(
        ir_index=8,
        x86_label="mov  eax, [rbp-4]",
        token_label="1",
        token_moves=[("[rbp-4]", "rax")],
        value_updates={"rax": "1"},
        flags_set=[],
        flags_clear=[],
    ),
    _Step(
        ir_index=9,
        x86_label="imul  eax, eax, 2",
        token_label="2",
        token_moves=[("ir_cursor", "rax")],
        value_updates={"rax": "2"},
        flags_set=["SF"],
        flags_clear=["ZF", "OF", "CF"],
    ),
    _Step(
        ir_index=10,
        x86_label="mov  rcx, [rbp-8]",
        token_label="ptr",
        token_moves=[("[rbp-8]", "ecx")],
        value_updates={"ecx": "ptr"},
        flags_set=[],
        flags_clear=[],
    ),
    _Step(
        ir_index=11,
        x86_label="mov  [rcx], eax",
        token_label="2",
        token_moves=[("rax", "[rcx]")],
        value_updates={"[rcx]": "2"},
        flags_set=[],
        flags_clear=[],
    ),
    _Step(
        ir_index=13,
        x86_label="mov  eax, [rcx]",
        token_label="2",
        token_moves=[("[rcx]", "rax")],
        value_updates={"rax": "2"},
        flags_set=[],
        flags_clear=[],
    ),
    _Step(
        ir_index=14,
        x86_label="pop  rbp  ;  ret",
        token_label="2",
        token_moves=[("rax", "ir_cursor")],
        value_updates={},
        flags_set=[],
        flags_clear=[],
    ),
]


# ── Scene ──────────────────────────────────────────────────────────────────────


class MachineLevelDemo(Scene):
    """Machine-level execution visualization for @double_1 from double.ll.

    Left panel:  LLVM IR source with a moving SurroundingRectangle cursor.
    Right panel: Styled CPU die containing a register file and flags display,
                 with a stack memory bus below the die.  Value tokens arc from
                 the active IR line to the affected register/memory cell.
    """

    def construct(self) -> None:
        self._build_layout()
        self._run_steps()
        self.wait(1.5)

    # ── Layout construction ────────────────────────────────────────────────

    def _build_layout(self) -> None:
        # ── Title ──
        title = Text(
            "double_1  ·  LLVM IR  →  x86-64",
            font_size=26,
            weight=BOLD,
        )
        title.to_edge(UP, buff=0.18)
        self.add(title)

        rule = Line(
            LEFT * 7.1 + DOWN * 0.08,
            RIGHT * 7.1 + DOWN * 0.08,
            color=GREY_D,
            stroke_width=1,
        ).next_to(title, DOWN, buff=0.12)
        self.add(rule)

        # ── Vertical divider ──
        self.add(
            Line(
                UP * 3.6 + RIGHT * _DIVIDER_X,
                DOWN * 4.0 + RIGHT * _DIVIDER_X,
                color=GREY_D,
                stroke_width=1,
            )
        )

        # ── Panel headers ──
        ir_hdr = Text("LLVM IR Source", font_size=18, color=GREY_B)
        ir_hdr.move_to((_LEFT_PANEL_X, 3.2, 0))
        self.add(ir_hdr)

        hw_hdr = Text("x86-64 CPU", font_size=18, color=GREY_B)
        hw_hdr.move_to((_RIGHT_PANEL_X, 3.2, 0))
        self.add(hw_hdr)

        # ── IR source text ──
        self._ir_mobs: list[Text] = []
        for i, line in enumerate(_IR_LINES):
            t = Text(line, font="Monospace", font_size=_IR_FONT, color=GREY_B)
            t.move_to((_LEFT_PANEL_X, _IR_TOP_Y - i * _IR_LINE_H, 0))
            t.align_to((_IR_INDENT_X, 0, 0), LEFT)
            self._ir_mobs.append(t)
            self.add(t)

        # IR cursor -- initially placed on line 0
        self._ir_cursor = SurroundingRectangle(
            self._ir_mobs[0],
            color=YELLOW,
            buff=0.05,
            stroke_width=2,
        )
        self._ir_cursor.set_opacity(0)
        self.add(self._ir_cursor)

        # x86 annotation label (shown/hidden per step)
        self._x86_lbl = Text("", font="Monospace", font_size=11, color=GREY_B)
        self.add(self._x86_lbl)

        # # ── CPU die ──
        # die = RoundedRectangle(
        #     width=_DIE_W,
        #     height=_DIE_H,
        #     corner_radius=0.25,
        #     fill_color="#0d1117",
        #     fill_opacity=1.0,
        #     stroke_color=GREY_D,
        #     stroke_width=2,
        # )
        # die.move_to((_DIE_CENTER_X, _DIE_CENTER_Y - 0.1, 0))
        # self.add(die)

        # die_label = Text("CPU", font_size=14, color=GREY_B)
        # die_label.next_to(die, UP, buff=0.08)
        # self.add(die_label)

        # ── Register file box (inside die) ──
        self._reg_rows: dict[str, _HWRow] = {}
        reg_defs = [
            ("rdi", "ptr", _COL_ARG),  # argument register (holds heap ptr)
            ("rax / eax", "—", _COL_GEN),  # primary general-purpose / return value
            ("ecx / rcx", "—", _COL_GEN),  # secondary general-purpose
            ("rsp", "...", _COL_STK),  # stack pointer
            ("rbp", "...", _COL_STK),  # base pointer
        ]
        reg_box_h = len(reg_defs) * (_REG_ROW_H + _REG_GAP) + 0.70
        reg_box = RoundedRectangle(
            width=_REG_ROW_W + 0.3,
            height=reg_box_h,
            corner_radius=0.15,
            fill_color="#161b22",
            fill_opacity=1.0,
            stroke_color=GREY_D,
            stroke_width=1,
        )
        reg_box_top_y = _REG_TOP_Y
        reg_box.move_to((_REG_CENTER_X, reg_box_top_y - reg_box_h / 2 + 0.1, 0))
        self.add(reg_box)

        reg_box_title = Text("Register File", font_size=13, color=GREY_B)
        reg_box_title.move_to((_REG_CENTER_X, reg_box_top_y - 0.22, 0))
        self.add(reg_box_title)

        row_y = reg_box_top_y - 0.70
        for reg_name, reg_val, reg_color in reg_defs:
            row = self._make_reg_row(reg_name, reg_val, reg_color, row_y)
            self._reg_rows[reg_name] = row
            row_y -= _REG_ROW_H + _REG_GAP

        # Alias map: token destinations can use short names
        self._row_aliases: dict[str, str] = {
            "rdi": "rdi",
            "rax": "rax / eax",
            "eax": "rax / eax",
            "ecx": "ecx / rcx",
            "rcx": "ecx / rcx",
            "rsp": "rsp",
            "rbp": "rbp",
        }

        # ── Flags display (inside die, below register file) ──
        self._flags: dict[str, _FlagBit] = {}
        flag_names = ["ZF", "SF", "OF", "CF"]
        flags_label = Text("FLAGS", font_size=13, color=GREY_B)
        flags_label.move_to((_DIE_CENTER_X - 1.5, _FLAG_Y + 0.42, 0))
        self.add(flags_label)

        flag_start_x = (
            _DIE_CENTER_X - (len(flag_names) * (_FLAG_SQ + 0.12)) / 2 + _FLAG_SQ / 2 + 0.1
        )
        for i, fname in enumerate(flag_names):
            fx = flag_start_x + i * (_FLAG_SQ + 0.12)
            bg = Rectangle(
                width=_FLAG_SQ,
                height=_FLAG_SQ,
                fill_color=_COL_FLAG_OFF,
                fill_opacity=0.4,
                stroke_color=GREY_D,
                stroke_width=1,
            )
            bg.move_to((fx, _FLAG_Y, 0))
            lbl = Text(fname, font_size=10, color=GREY_B)
            lbl.move_to((fx, _FLAG_Y, 0))
            self._flags[fname] = _FlagBit(fname, bg, lbl)
            self.add(bg, lbl)

        # ── Stack memory table (below die) ──
        self._mem_rows: dict[str, _HWRow] = {}
        mem_label = Text("Stack Memory", font_size=13, color=GREY_B)
        mem_label.move_to((_DIE_CENTER_X, _MEM_TOP_Y - 0.20, 0))
        self.add(mem_label)

        mem_defs = [
            ("[rbp-8]", "—"),
            ("[rbp-4]", "—"),
            ("[rcx]", "—"),
        ]
        mem_y = _MEM_TOP_Y - 0.52
        for addr, val in mem_defs:
            row = self._make_reg_row(addr, val, BLUE_D, mem_y)
            self._mem_rows[addr] = row
            # Start hidden; fade in on alloca
            row.bg_rect.set_opacity(0)
            row.name_mob.set_opacity(0)
            row.value_mob.set_opacity(0)
            mem_y -= _MEM_ROW_H + _MEM_GAP

    def _make_reg_row(
        self,
        name: str,
        value: str,
        color: ManimColor,
        center_y: float,
    ) -> _HWRow:
        """Build a single register/memory row and add it to the scene."""
        bg = Rectangle(
            width=_REG_ROW_W,
            height=_REG_ROW_H,
            fill_color=color,
            fill_opacity=0.12,
            stroke_color=color,
            stroke_width=1.2,
        )
        bg.move_to((_REG_CENTER_X, center_y, 0))

        name_t = Text(name, font="Monospace", font_size=13, color=color)
        name_t.move_to(bg.get_left() + RIGHT * 0.55)

        val_t = Text(value, font="Monospace", font_size=14, color=WHITE)
        val_t.move_to(bg.get_right() + LEFT * 0.55)

        self.add(bg, name_t, val_t)
        return _HWRow(
            name=name,
            value=value,
            color=color,
            name_mob=name_t,
            value_mob=val_t,
            bg_rect=bg,
        )

    # ── Step execution ─────────────────────────────────────────────────────

    def _run_steps(self) -> None:
        # Fade-in the IR cursor on the first line
        self._ir_cursor.set_opacity(1)
        self._advance_cursor(0)

        for step in _STEPS:
            self._execute_step(step)

        # Final: dim cursor after ret
        self.play(self._ir_cursor.animate.set_opacity(0.2), run_time=0.4)

    def _execute_step(self, step: _Step) -> None:
        # 1. Advance cursor to active IR line
        self._advance_cursor(step.ir_index)

        # 2. Show x86 annotation below cursor
        x86_text = Text(
            step.x86_label,
            font="Monospace",
            font_size=11,
            color=GREY_B,
        )
        x86_text.next_to(self._ir_cursor, DOWN, buff=0.08)
        self.play(FadeIn(x86_text, run_time=0.2))
        self.wait(0.3)

        # 3. Handle alloca steps specially (fade in memory cells, no token)
        if step.ir_index in (2, 3):
            addr = "[rbp-8]" if step.ir_index == 2 else "[rbp-4]"
            mem_row = self._mem_rows[addr]
            self.play(
                mem_row.bg_rect.animate.set_opacity(0.35),
                mem_row.name_mob.animate.set_opacity(1.0),
                mem_row.value_mob.animate.set_opacity(1.0),
                run_time=0.45,
            )
            self._apply_value_updates(step.value_updates)

        else:
            # 4. Fly value token(s) for non-alloca steps
            for src_key, dst_key in step.token_moves:
                if step.token_label:
                    self._fly_token(step.token_label, src_key, dst_key, step.value_updates)

            # Apply any updates not covered by token flight
            remaining = {
                k: v
                for k, v in step.value_updates.items()
                if k not in {dst for _, dst in step.token_moves}
            }
            if remaining:
                self._apply_value_updates(remaining)

        # 5. Update flags
        flag_anims = []
        for fname in step.flags_set:
            fb = self._flags[fname]
            flag_anims.append(fb.bg.animate.set_fill(_COL_FLAG_ON, opacity=0.8))
            flag_anims.append(fb.label.animate.set_color(WHITE))
        for fname in step.flags_clear:
            fb = self._flags[fname]
            flag_anims.append(fb.bg.animate.set_fill(_COL_FLAG_OFF, opacity=0.4))
            flag_anims.append(fb.label.animate.set_color(GREY_B))
        if flag_anims:
            self.play(*flag_anims, run_time=0.3)

        # 6. Fade out x86 annotation; dim IR line back to grey
        self.play(
            FadeOut(x86_text, run_time=0.25),
            self._ir_mobs[step.ir_index].animate.set_color(GREY_B),
        )

    def _advance_cursor(self, ir_index: int) -> None:
        """Move the IR cursor to the given line and brighten that line."""
        target_line = self._ir_mobs[ir_index]
        target_line.set_color(WHITE)
        new_rect = SurroundingRectangle(target_line, color=YELLOW, buff=0.05, stroke_width=2)
        self.play(
            self._ir_cursor.animate.become(new_rect),
            run_time=0.3,
        )

    # ── Token flight ───────────────────────────────────────────────────────

    def _get_mob_for_key(self, key: str) -> VGroup | Text:
        """Return the Manim object corresponding to a row key."""
        if key == "ir_cursor":
            return self._ir_cursor
        resolved = self._row_aliases.get(key, key)
        if resolved in self._reg_rows:
            return self._reg_rows[resolved].bg_rect
        if key in self._mem_rows:
            return self._mem_rows[key].bg_rect
        # Fallback: return cursor
        return self._ir_cursor

    def _fly_token(
        self,
        label: str,
        src_key: str,
        dst_key: str,
        value_updates: dict[str, str],
    ) -> None:
        """Arc a value token from src to dst, then flash and update the destination."""
        src_mob = self._get_mob_for_key(src_key)
        dst_mob = self._get_mob_for_key(dst_key)
        dst_row_key = self._row_aliases.get(dst_key, dst_key)

        src_pt = src_mob.get_center()
        dst_pt = dst_mob.get_center()

        # Build arc path -- angle flips based on relative positions to avoid straight lines
        dx = dst_pt[0] - src_pt[0]
        arc_angle = PI / 4 if dx >= 0 else -PI / 4

        token = Text(label, font="Monospace", font_size=15, color=YELLOW)
        token.move_to(src_pt)

        path = ArcBetweenPoints(src_pt, dst_pt, angle=arc_angle)

        self.play(FadeIn(token, scale=0.6, run_time=0.15))
        self.play(MoveAlongPath(token, path), run_time=0.55)

        # Determine destination row color for flash
        dst_color = WHITE
        if dst_row_key in self._reg_rows:
            dst_color = self._reg_rows[dst_row_key].color
        elif dst_key in self._mem_rows:
            dst_color = self._mem_rows[dst_key].color

        # Flash destination and update value simultaneously with token fade-out
        flash_anims = [
            FadeOut(token, run_time=0.2),
            dst_mob.animate.set_fill(dst_color, opacity=0.55),
        ]
        self.play(*flash_anims)

        # Update value text
        updates_for_dst = {dst_key: v for k, v in value_updates.items() if k == dst_key}
        if dst_row_key in value_updates:
            updates_for_dst[dst_row_key] = value_updates[dst_row_key]
        self._apply_value_updates(updates_for_dst)

        # Restore destination opacity
        self.play(dst_mob.animate.set_fill(dst_color, opacity=0.12), run_time=0.3)

    def _apply_value_updates(self, updates: dict[str, str]) -> None:
        """Swap value text in-place for the given row names → new values."""
        anims = []
        new_mobs: list[tuple[_HWRow | None, Text, bool]] = []

        for key, new_val in updates.items():
            resolved = self._row_aliases.get(key, key)
            row = self._reg_rows.get(resolved) or self._mem_rows.get(key)
            if row is None:
                continue
            new_text = Text(new_val, font="Monospace", font_size=14, color=WHITE)
            new_text.move_to(row.value_mob.get_center())
            anims.append(FadeOut(row.value_mob, run_time=0.15))
            new_mobs.append((row, new_text, resolved in self._reg_rows))

        if anims:
            self.play(*anims)

        for row, new_text, is_reg in new_mobs:
            self.add(new_text)
            # Patch the value_mob in-place by replacing the reference in the dict
            if is_reg:
                resolved = self._row_aliases.get(row.name, row.name)
                old_row = self._reg_rows[resolved]
                self._reg_rows[resolved] = _HWRow(
                    name=old_row.name,
                    value=new_text.text,
                    color=old_row.color,
                    name_mob=old_row.name_mob,
                    value_mob=new_text,
                    bg_rect=old_row.bg_rect,
                )
            else:
                old_row = self._mem_rows[row.name]
                self._mem_rows[row.name] = _HWRow(
                    name=old_row.name,
                    value=new_text.text,
                    color=old_row.color,
                    name_mob=old_row.name_mob,
                    value_mob=new_text,
                    bg_rect=old_row.bg_rect,
                )
