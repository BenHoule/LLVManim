"""
Rich call-stack visualization sandbox — Manim Community Edition.

Two scene classes are provided, selectable with the -s flag:

  StackDemoBadge     — Option B (IMPLEMENTED)
      Stack-only layout, no separate IR text panel.  When a frame header or
      slot row arrives it slides in with its label highlighted yellow, then
      settles to white.  The slot labels carry the full instruction text, so
      the stack IS the story — no competing panel required.

  StackDemoIRCursor  — Option A (STUBBED — see class docstring for TODOs)
      Two-column layout: full IR source with a moving SurroundingRectangle
      cursor on the left; animated stack on the right.  Requires per-function
      IR text to flow through the data pipeline (not yet implemented).

Run (low quality, fast):
    uv run manim -ql sandbox/manim_CE/stack_demo.py StackDemoBadge
    uv run manim -ql sandbox/manim_CE/stack_demo.py StackDemoIRCursor

Run (high quality):
    uv run manim -qh sandbox/manim_CE/stack_demo.py StackDemoBadge
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
    Scene,
    SurroundingRectangle,
    Text,
    VGroup,
)

# ── IR source registry (hardcoded double.ll, relevant alloca/call/ret lines) ──
#
# Each entry maps a function name to:
#   lines      — display strings for the IR panel (stripped, readable)
#   event_map  — maps (ir_text_fragment) → line index for cursor placement
#
# When porting to production, replace this dict with data extracted live from
# llvmanim.ingest.llvm_events and stored on LLVManimScene (see class TODOs).
_IR_REGISTRY: dict[str, dict] = {
    "main": {
        # Line indices (0-based) used by event_map and call_sites below:
        #  0  define i32 @main() {
        #  1  entry:
        #  2    %retval = alloca i32
        #  3    %r = alloca i32
        #  4    %p = alloca ptr
        #  5    call void @init(ptr %p)          ← call_site for 'init'
        #  6    br label %while.cond
        #  7  while.cond:
        #  8    br i1 %cmp, %while.body, %while.end
        #  9  while.body:
        # 10    %call1 = call i32 @double_1(ptr %p)  ← call_site for 'double_1'
        # 11    br label %while.cond
        # 12  while.end:
        # 13    ret i32 %r
        # 14  }
        "lines": [
            "define i32 @main() {",
            "entry:",
            "  %retval = alloca i32",
            "  %r = alloca i32",
            "  %p = alloca ptr",
            "  call void @init(ptr %p)",
            "  br label %while.cond",
            "while.cond:",
            "  br i1 %cmp, %while.body, %while.end",
            "while.body:",
            "  %call1 = call i32 @double_1(ptr %p)",
            "  br label %while.cond",
            "while.end:",
            "  ret i32 %r",
            "}",
        ],
        # Keys are substrings of the ir_text passed to _on_step_begin.
        # Put longer / more specific keys first to prevent "ret" matching
        # "%retval" before the alloca keys do.
        "event_map": {
            "push_stack_frame": 0,
            "%retval = alloca i32": 2,
            "%r = alloca i32": 3,
            "%p = alloca ptr": 4,
            "ret": 13,
        },
        # Maps bare callee name → line index of the call instruction in this function.
        "call_sites": {
            "init": 5,
            "double_1": 10,
        },
    },
    "init": {
        # 0  define void @init(ptr %p) {
        # 1  entry:
        # 2    %p.addr = alloca ptr
        # 3    store ptr %p, ptr %p.addr
        # 4    store i32 1, ptr %p
        # 5    ret void
        # 6  }
        "lines": [
            "define void @init(ptr %p) {",
            "entry:",
            "  %p.addr = alloca ptr",
            "  store ptr %p, ptr %p.addr",
            "  store i32 1, ptr %p",
            "  ret void",
            "}",
        ],
        "event_map": {
            "push_stack_frame": 0,
            "%p.addr = alloca ptr": 2,
            "ret": 5,
        },
        "call_sites": {},
    },
    "double_1": {
        # 0  define i32 @double_1(ptr %p) {
        # 1  entry:
        # 2    %p.addr = alloca ptr
        # 3    %tmp = alloca i32
        # 4    store ptr %p, ptr %p.addr
        # 5    %mul = mul nsw i32 2, %tmp
        # 6    ret i32 %mul
        # 7  }
        "lines": [
            "define i32 @double_1(ptr %p) {",
            "entry:",
            "  %p.addr = alloca ptr",
            "  %tmp = alloca i32",
            "  store ptr %p, ptr %p.addr",
            "  %mul = mul nsw i32 2, %tmp",
            "  ret i32 %mul",
            "}",
        ],
        "event_map": {
            "push_stack_frame": 0,
            "%p.addr = alloca ptr": 2,
            "%tmp = alloca i32": 3,
            "ret": 6,
        },
        "call_sites": {},
    },
}

# ── Layout constants ───────────────────────────────────────────────────────────
_SLOT_W = 4.0          # width of every stack cell
_HEADER_H = 0.55       # height of a frame's header bar
_SLOT_H = 0.62         # height of one alloca slot
_GAP = 0.04            # gap between adjacent cells
_STACK_TOP_Y = 2.6     # y of the top edge of the first cell; subclasses may shift

# One colour per call depth; wraps if depth exceeds palette length
_PALETTE = [BLUE_D, GREEN_C, TEAL_D, GOLD_D, MAROON_D, PURPLE_D]


# ── Mobject factories ──────────────────────────────────────────────────────────

def _frame_header(func_name: str, color: ManimColor) -> VGroup:
    """Bold, opaque header bar labelled with the function name.

    Returns VGroup(rect, label) — label is always index 1.  Callers may
    recolour label before or after FadeIn (e.g. for the yellow-flash effect).
    """
    rect = Rectangle(
        width=_SLOT_W,
        height=_HEADER_H,
        fill_color=color,
        fill_opacity=0.85,
        stroke_color=color,
        stroke_width=2,
    )
    label = Text(func_name, font="Monospace", font_size=22, color=WHITE, weight=BOLD)
    label.move_to(rect)
    return VGroup(rect, label)


def _slot_cell(slot_text: str, color: ManimColor) -> VGroup:
    """Single alloca-slot row tinted with the owning frame's colour.

    Returns VGroup(rect, label) — label is always index 1.
    """
    rect = Rectangle(
        width=_SLOT_W,
        height=_SLOT_H,
        fill_color=color,
        fill_opacity=0.18,
        stroke_color=color,
        stroke_width=1.5,
    )
    label = Text(slot_text, font="Monospace", font_size=19)
    label.move_to(rect)
    return VGroup(rect, label)


# ── Shared base ────────────────────────────────────────────────────────────────

class _StackBase(Scene):
    """Shared stack mechanics.  Do not instantiate directly — use a subclass.

    Subclasses customise behaviour by overriding:
      _setup_chrome()        — add title, panels, column labels, etc.
      _before_cell_arrive()  — called just before FadeIn (e.g. set label → YELLOW)
      _on_cell_arrive()      — called just after FadeIn (e.g. animate label → WHITE)
      _on_step_begin()       — called at the start of push / alloca / pop
    """

    _STACK_X: float = 0.5  # horizontal centre of the stack panel; override per subclass

    def construct(self) -> None:
        self._cursor_y: float = _STACK_TOP_Y
        self._depth: int = 0
        # Parallel lists: one entry per live frame.
        self._frame_stack: list[tuple[VGroup, list[VGroup]]] = []
        self._frame_names: list[str] = []
        self._setup_chrome()
        self._run_sequence()
        self.wait(1.0)

    # ── Hook overrides (default: no-op) ───────────────────────────────────────

    def _setup_chrome(self) -> None:
        """Add title bar and horizontal rule.  Call super() from subclasses."""
        title = Text("Call Stack  /  double.ll", font_size=30, weight=BOLD)
        title.to_edge(UP, buff=0.28)
        self.add(title)
        rule = Line(
            title.get_bottom() + DOWN * 0.12 + LEFT * 7.1,
            title.get_bottom() + DOWN * 0.12 + RIGHT * 7.1,
            color=GREY_D,
            stroke_width=1,
        )
        self.add(rule)

    def _before_cell_arrive(self, mob: VGroup) -> None:
        """Called after Mobject creation but before FadeIn (synchronous)."""

    def _on_cell_arrive(self, mob: VGroup) -> None:
        """Called after FadeIn completes.  Play badge animations here."""

    def _on_step_begin(self, action: str, ir_text: str, func_name: str, caller_name: str = "") -> None:
        """Called at the start of each stack step.  Advance IR cursor here.

        action      — "push", "alloca", or "pop"
        ir_text     — raw instruction text (alloca) or IR event label (ret)
        func_name   — callee for push; current frame for alloca; popped frame for pop
        caller_name — caller frame name (only meaningful for push and pop)
        """

    # ── Stack mechanics ───────────────────────────────────────────────────────

    def _color(self) -> ManimColor:
        return _PALETTE[self._depth % len(_PALETTE)]

    def _push(self, func_name: str, ir_text: str = "call") -> None:
        """Push a new frame header onto the visual stack."""
        caller_name = self._frame_names[-1] if self._frame_names else ""
        self._on_step_begin("push", ir_text, func_name, caller_name)
        color = self._color()
        mob = _frame_header(func_name, color)
        mob.move_to(RIGHT * self._STACK_X + UP * (self._cursor_y - _HEADER_H / 2))
        self._cursor_y -= _HEADER_H + _GAP
        self._depth += 1
        self._frame_stack.append((mob, []))
        self._frame_names.append(func_name)
        self._before_cell_arrive(mob)
        self.play(FadeIn(mob, shift=DOWN * 0.25), run_time=0.5)
        self._on_cell_arrive(mob)

    def _alloca(self, slot_text: str) -> None:
        """Slide a new alloca-slot row below the current frame header."""
        if not self._frame_stack:
            return
        func_name = self._frame_names[-1] if self._frame_names else ""
        self._on_step_begin("alloca", slot_text, func_name)
        color = _PALETTE[(self._depth - 1) % len(_PALETTE)]
        mob = _slot_cell(slot_text, color)
        mob.move_to(RIGHT * self._STACK_X + UP * (self._cursor_y - _SLOT_H / 2))
        self._cursor_y -= _SLOT_H + _GAP
        self._frame_stack[-1][1].append(mob)
        self._before_cell_arrive(mob)
        self.play(FadeIn(mob, shift=DOWN * 0.15), run_time=0.4)
        self._on_cell_arrive(mob)

    def _pop(self, ir_text: str = "ret") -> None:
        """Fade out the top frame (slots bottom-to-top, then header)."""
        if not self._frame_stack:
            return
        # Peek at names before popping so both callee and caller are visible to hook.
        callee_name = self._frame_names[-1] if self._frame_names else ""
        caller_name = self._frame_names[-2] if len(self._frame_names) >= 2 else ""
        self._on_step_begin("pop", ir_text, callee_name, caller_name)
        if self._frame_names:
            self._frame_names.pop()
        header, slots = self._frame_stack.pop()
        self._depth -= 1
        self._cursor_y += _HEADER_H + _GAP + len(slots) * (_SLOT_H + _GAP)
        mobs_out = slots[::-1] + [header]
        self.play(*[FadeOut(m, shift=UP * 0.2) for m in mobs_out], run_time=0.55)

    def _run_sequence(self) -> None:
        """Demo sequence mirroring double.ll runtime call order.

        Actual order: @main entry allocates locals → calls @init → @init
        allocates %p.addr → returns → @main while.body calls @double_1 →
        @double_1 allocates locals → returns → @main while.end returns.
        """
        self._push("@main",     "push_stack_frame main")
        self._alloca("%retval = alloca i32")
        self._alloca("%r = alloca i32")
        self._alloca("%p = alloca ptr")
        self._push("@init",     "push_stack_frame init")
        self._alloca("%p.addr = alloca ptr")
        self._pop("ret  ← @init")
        self._push("@double_1", "push_stack_frame double_1")
        self._alloca("%p.addr = alloca ptr")
        self._alloca("%tmp = alloca i32")
        self._pop("ret  ← @double_1")
        self._pop("ret  ← @main")


# ── Option B: Badge flash (IMPLEMENTED) ───────────────────────────────────────

class StackDemoBadge(_StackBase):
    """Option B (IMPLEMENTED): Stack-only layout with yellow-flash badge.

    No separate IR text panel — the slot labels carry the instruction text.
    Each arriving cell's label starts yellow and settles to white, drawing
    the viewer's attention without a competing panel.
    """

    _STACK_X = 0.5

    def _setup_chrome(self) -> None:
        super()._setup_chrome()
        col_label = Text("Stack  (grows ↓)", font_size=21, color=GREY_B)
        col_label.move_to(RIGHT * self._STACK_X + UP * 2.85)
        self.add(col_label)

    def _before_cell_arrive(self, mob: VGroup) -> None:
        """Colour the label yellow so it arrives highlighted."""
        mob[1].set_color(YELLOW)

    def _on_cell_arrive(self, mob: VGroup) -> None:
        """Animate the label back to its resting colour (white)."""
        self.play(mob[1].animate.set_color(WHITE), run_time=0.35)


# ── IR panel factory (shared, used by Option A) ──────────────────────────────

_IR_PANEL_X = -3.5    # horizontal centre of the IR text column
_IR_LINE_SPACING = 0.40
_IR_FONT_SIZE = 16


def _build_ir_panel(func_name: str) -> VGroup:
    """Build a monospaced Text VGroup for func_name using _IR_REGISTRY.

    Returns a VGroup where each submobject is one line's Text Mobject so that
    cursor positioning via mob[line_index].get_center() works directly.

    When porting to production:
      - Replace _IR_REGISTRY with data from LLVManimScene (e.g. a
        dict[str, list[str]] populated by build_scene from the ingest layer).
      - Consider swapping Text for manim's Code mobject for syntax highlighting.
    """
    entry = _IR_REGISTRY.get(func_name, {})
    lines: list[str] = entry.get("lines", [f"(no IR available for {func_name})"])
    group = VGroup()
    for i, line in enumerate(lines):
        txt = Text(line, font="Monospace", font_size=_IR_FONT_SIZE)
        txt.move_to([_IR_PANEL_X, 2.2 - i * _IR_LINE_SPACING, 0])
        txt.align_to([_IR_PANEL_X - 2.6, 0, 0], direction=LEFT)
        group.add(txt)
    return group


def _cursor_line_index(func_name: str, ir_text: str, action: str) -> int:
    """Resolve an (action, ir_text) pair to a line index in the IR registry.

    Scans the event_map for the first key that is a substring of ir_text.
    Keys should be ordered from most-specific to least-specific in _IR_REGISTRY
    to avoid short fragments (like 'ret') matching long strings ('%retval ...').

    When porting to production replace this with an exact lookup using
    IREvent.index_in_function once that index is threaded through RenderStep.
    """
    entry = _IR_REGISTRY.get(func_name, {})
    event_map: dict[str, int] = entry.get("event_map", {})
    for fragment, idx in event_map.items():
        if fragment and fragment in ir_text:
            return idx
    return 0


def _call_site_line(caller_func: str, callee_func: str) -> int:
    """Return the line index of the call to callee_func inside caller_func's IR.

    Uses the 'call_sites' sub-dict of _IR_REGISTRY.  Returns 0 if not found.
    When porting to production, replace with index_in_function from IREvent.
    """
    entry = _IR_REGISTRY.get(caller_func, {})
    return entry.get("call_sites", {}).get(callee_func, 0)


# ── Option A: IR cursor (IMPLEMENTED) ─────────────────────────────────────────

class StackDemoIRCursor(_StackBase):
    """Option A (IMPLEMENTED): Two-column layout with a moving IR source cursor.

    Left panel  — full IR source for the currently executing function,
                  rendered as monospaced text from _IR_REGISTRY.
    Right panel — live animated stack (inherited from _StackBase).

    A yellow SurroundingRectangle cursor advances to the current instruction
    on every stack step.  On call the panel FadeTransforms to the callee's IR
    and the cursor jumps to the callee's first line.  On ret the reverse happens.

    ── Production TODOs ────────────────────────────────────────────────────────

    TODO [pipeline]: _IR_REGISTRY is hardcoded for double.ll.  In production,
        per-function IR lines should be extracted by the ingest layer and stored
        on LLVManimScene (e.g. as ir_source: dict[str, list[str]]) so that any
        module can be visualised without editing this file.

    TODO [line resolution]: _cursor_line_index() uses substring matching as a
        heuristic.  Replace with exact lookup via IREvent.index_in_function once
        that index is threaded through RenderStep.

    TODO [scrolling]: For long functions, implement smooth scroll-into-view so
        the highlighted line stays visible (e.g. shift the panel VGroup so the
        cursor line is always within the visible frame area).
    """

    _STACK_X = 3.0

    def _setup_chrome(self) -> None:
        super()._setup_chrome()

        vdiv = Line(UP * 3.5, DOWN * 4.0, color=GREY_D, stroke_width=1)
        self.add(vdiv)

        ir_col_label = Text("IR Source", font_size=21, color=GREY_B)
        ir_col_label.move_to([_IR_PANEL_X, 2.85, 0])
        self.add(ir_col_label)

        stack_col_label = Text("Stack  (grows ↓)", font_size=21, color=GREY_B)
        stack_col_label.move_to(RIGHT * self._STACK_X + UP * 2.85)
        self.add(stack_col_label)

        # IR panel starts with @main — first function in the demo sequence.
        self._ir_panel: VGroup = _build_ir_panel("main")
        self.add(self._ir_panel)

        # Cursor — starts on the define line (index 0).
        self._ir_cursor = SurroundingRectangle(
            self._ir_panel[0],
            color=YELLOW,
            buff=0.06,
            stroke_width=2,
        )
        self.add(self._ir_cursor)

        # Track current function (bare name, no @) so we know when to swap panels.
        self._current_func: str = "main"
        # Call-site restoration stack: (caller_func, call_line_idx) per active call.
        self._call_site_stack: list[tuple[str, int]] = []

    def _on_step_begin(self, action: str, ir_text: str, func_name: str, caller_name: str = "") -> None:
        """Advance the IR cursor and manage panel swaps on call/ret.

        push  — advance cursor to the call instruction in the caller, record
                the call-site for later restoration, then swap to the callee.
        alloca — advance cursor to the alloca line (no panel swap).
        pop   — advance cursor to the ret line in the callee, then swap back
                to the caller and restore the cursor to the call-site.
        """
        callee = func_name.lstrip("@")

        if action == "push":
            # Point to the call instruction in the current (caller) function.
            call_line = _call_site_line(self._current_func, callee)
            self._advance_cursor(call_line)
            # Remember where to return the cursor when this frame is popped.
            self._call_site_stack.append((self._current_func, call_line))
            # Swap the panel to the callee (cursor resets to the define line).
            self._swap_panel(callee, target_line=0)

        elif action == "alloca":
            idx = _cursor_line_index(callee, ir_text, "alloca")
            self._advance_cursor(idx)

        elif action == "pop":
            # Advance to the ret instruction in the callee's panel.
            idx = _cursor_line_index(callee, ir_text, "ret")
            self._advance_cursor(idx)
            # Swap back to the caller and restore the cursor to the call site.
            if self._call_site_stack:
                restore_func, restore_line = self._call_site_stack.pop()
                self._swap_panel(restore_func, target_line=restore_line)

    def _swap_panel(self, new_func: str, target_line: int = 0) -> None:
        """FadeTransform the current IR panel to the new function's panel.

        target_line — line index the cursor should land on in the new panel.
                      Pass the call-site index when returning to a caller.
        """
        new_panel = _build_ir_panel(new_func)
        self.play(FadeTransform(self._ir_panel, new_panel), run_time=0.4)
        self._ir_panel = new_panel
        self._current_func = new_func
        safe_idx = min(target_line, len(self._ir_panel) - 1)
        new_cursor = SurroundingRectangle(
            self._ir_panel[safe_idx], color=YELLOW, buff=0.06, stroke_width=2
        )
        self.play(FadeTransform(self._ir_cursor, new_cursor), run_time=0.25)
        self._ir_cursor = new_cursor

    def _advance_cursor(self, line_index: int) -> None:
        """Animate the SurroundingRectangle to surround the target line."""
        safe_idx = min(line_index, len(self._ir_panel) - 1)
        new_cursor = SurroundingRectangle(
            self._ir_panel[safe_idx], color=YELLOW, buff=0.06, stroke_width=2
        )
        self.play(self._ir_cursor.animate.become(new_cursor), run_time=0.3)
