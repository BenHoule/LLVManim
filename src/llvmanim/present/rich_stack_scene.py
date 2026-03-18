"""Rich call-stack Manim CE scenes for LLVManim.

Two display modes are provided, selected via the ``--ir-mode`` CLI flag:

  basic (--ir-mode basic)  — Stack-only layout.  Each arriving frame header or
                             slot row is labelled in yellow then fades to white,
                             keeping the viewer's focus without a competing panel.

  rich  (--ir-mode rich)   — Two-column layout.  Full IR source for the currently
                             executing function sits on the left; the live stack
                             animates on the right.  A yellow SurroundingRectangle
                             cursor advances to the current instruction and
                             FadeTransforms to the callee's IR on each call/ret.

Public API
----------
build_ir_registry        — parse a .ll file → per-function display-line lists
RichStackSceneBadge      — ``--ir-mode basic`` scene; accepts a ProgramEventStream
RichStackSceneSpotlight  — ``--ir-mode rich``  scene; accepts a ProgramEventStream
"""

from __future__ import annotations

import re
from collections import defaultdict

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

from llvmanim.transform.models import ProgramEventStream

# ── IR registry ────────────────────────────────────────────────────────────────
# TODO: build_ir_registry re-parses the .ll file from scratch because IREvent
# only carries flat instruction strings — no define signature, block labels,
# blank lines, or closing brace.  Long-term fix: extend IREvent (or add a
# parallel DisplayLine model) so that the ingestion layer emits display-ready
# text and this second parse can be removed.

_DBG_META_RE = re.compile(r",?\s*![a-zA-Z0-9_.]+\s+!\d+|,?\s*!\d+\b")
_DEFINE_RE = re.compile(r"^define\b.*?@(\w+)\s*\(")


def _clean_ir_line(raw: str) -> str:
    """Strip comments, debug metadata, attribute refs, and verbose type qualifiers.

    Returns the display-friendly version of a raw .ll source line.
    """
    # Strip ; comments (block-label preds notes live here too)
    line = raw.split(";")[0].rstrip()
    # Strip debug metadata tokens: , !dbg !17, , !llvm.loop !32, etc.
    line = _DBG_META_RE.sub("", line)
    # Strip function attribute group references: #0, #1, etc.
    line = re.sub(r"\s+#\d+\b", "", line)
    # Strip verbose type qualifiers that add length without adding insight
    line = re.sub(r"\bnoalias\s+", "", line)
    line = re.sub(r"\bnoundef\s+", "", line)
    line = re.sub(r"\bdso_local\s+", "", line)
    line = re.sub(r",\s*align\s+\d+", "", line)
    return line.rstrip(", ")


def build_ir_registry(source_path: str) -> dict[str, list[str]]:
    """Parse a .ll file and return per-function display-line lists.

    Keys are bare function names (no @).  Display lines are:
      - Cleaned with _clean_ir_line (debug metadata, attribute refs removed).
      - @llvm intrinsic call lines omitted (they add noise, not insight).
      - Blank lines between basic blocks preserved for readability.
    """
    registry: dict[str, list[str]] = {}
    current_func: str | None = None
    current_lines: list[str] = []

    with open(source_path) as fh:
        for raw in fh:
            line = raw.rstrip()
            m = _DEFINE_RE.match(line)
            if m:
                current_func = m.group(1)
                current_lines = [_clean_ir_line(line)]
                continue
            if current_func is None:
                continue
            stripped = line.strip()
            if stripped == "}":
                current_lines.append("}")
                registry[current_func] = list(current_lines)
                current_func = None
                current_lines = []
                continue
            # Skip llvm intrinsic call lines entirely
            if "@llvm." in stripped:
                continue
            clean = _clean_ir_line(line)
            if clean.strip():  # skip lines that are blank after cleaning
                current_lines.append(clean)

    return registry


# ── Execution trace ─────────────────────────────────────────────────────────────
# TODO: build_execution_trace re-implements a recursive call-tree walk because
# the transform pipeline produces a flat, function-appearance-ordered event
# stream and a CFG graph — neither of which expresses call-tree order (push
# caller → recurse into callee → pop).  Long-term fix: add a call-trace
# builder to the transform layer so the presentation layer can consume a
# typed TraceStep list from the pipeline instead of computing it here.

_CALLEE_RE = re.compile(r"call\b[^@]*@(\w+)\s*\(")

# A trace element: ("push" | "alloca" | "pop", func_name, ir_text)
TraceStep = tuple[str, str, str]


def _extract_callee(call_text: str) -> str:
    """Extract bare callee name from a call instruction string.

    E.g. 'call void @init(ptr %0)' → 'init'.
    Returns '' if no callee can be identified.
    """
    m = _CALLEE_RE.search(call_text)
    return m.group(1) if m else ""


def build_execution_trace(
    stream: ProgramEventStream,
    entry: str = "main",
    max_depth: int = 20,
) -> list[TraceStep]:
    """Build an execution-ordered trace by simulating a call tree from *entry*.

    The IR event stream is grouped per function.  Starting from *entry*, each
    function's events are walked in order; call events recursively descend into
    the callee.  External functions (declared but not defined) are silently
    skipped.  Only one iteration of any loop is modelled (IR instructions
    appear once regardless of runtime loop count).

    Returns a list of (action, func_name, ir_text) triples where action is one
    of "push", "alloca", or "pop".
    """
    func_events: dict[str, list] = defaultdict(list)
    for event in stream.events:
        func_events[event.function_name].append(event)

    defined: frozenset[str] = frozenset(func_events)
    trace: list[TraceStep] = []

    def walk(func_name: str, depth: int) -> None:
        if depth > max_depth or func_name not in defined:
            return
        trace.append(("push", func_name, ""))
        for event in func_events[func_name]:
            if event.kind == "alloca":
                trace.append(("alloca", func_name, event.text))
            elif event.kind == "call":
                callee = _extract_callee(event.text)
                # Skip llvm intrinsics and undefined (external) functions
                if callee and callee in defined and not callee.startswith("llvm"):
                    walk(callee, depth + 1)
            elif event.kind == "ret":
                trace.append(("pop", func_name, event.text))
                return

    walk(entry, 0)
    return trace


# ── Layout constants ────────────────────────────────────────────────────────────

_SLOT_W = 4.0  # width of every stack cell
_HEADER_H = 0.55  # height of a frame header bar
_SLOT_H = 0.62  # height of one alloca slot row
_GAP = 0.04  # gap between adjacent cells
_STACK_TOP_Y = 2.6  # y of the top edge of the topmost cell

# Colour palette — one colour per call depth; wraps if deeper than palette
_PALETTE: list[ManimColor] = [BLUE_D, GREEN_C, TEAL_D, GOLD_D, MAROON_D, PURPLE_D]

_IR_PANEL_X = -3.5  # horizontal centre of the IR text column (Option A)
_IR_LINE_SPACING = 0.40
_IR_FONT_SIZE = 13
_IR_PANEL_TOP_Y = 2.2  # y of the topmost panel line (unscrolled origin)
_IR_VIEWPORT_BOT = -3.5  # lowest y still within the visible IR area


# ── Mobject factories ───────────────────────────────────────────────────────────


def _frame_header(func_name: str, color: ManimColor) -> VGroup:
    """Opaque coloured header bar labelled @func_name.

    Returns VGroup(rect, label) — label is always index 1.
    """
    rect = Rectangle(
        width=_SLOT_W,
        height=_HEADER_H,
        fill_color=color,
        fill_opacity=0.85,
        stroke_color=color,
        stroke_width=2,
    )
    label = Text(f"@{func_name}", font="Monospace", font_size=22, color=WHITE, weight=BOLD)
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


# ── Shared base ─────────────────────────────────────────────────────────────────


class _StackBase(Scene):
    """Common stack mechanics shared by both rich-scene variants.

    Subclasses customise appearance by overriding the hook methods below.
    Data is supplied via the constructor's *trace* argument so that the scene
    can be instantiated programmatically (i.e. via .render(), not manim CLI).
    """

    _STACK_X: float = 0.5  # horizontal centre of the stack panel; override per subclass

    def __init__(self, trace: list[TraceStep], speed: float = 1.0, **kwargs: object) -> None:
        self._trace = trace
        self._speed = max(speed, 0.01)  # guard against zero/negative
        super().__init__(**kwargs)  # type: ignore[arg-type]

    def _rt(self, base: float) -> float:
        """Return a run_time scaled by the inverse of the speed multiplier."""
        return base / self._speed

    def construct(self) -> None:
        self._cursor_y: float = _STACK_TOP_Y
        self._depth: int = 0
        # One entry per live frame: (header_mob, [slot_mobs])
        self._frame_stack: list[tuple[VGroup, list[VGroup]]] = []
        # Parallel list of bare function names for the live frames
        self._frame_names: list[str] = []
        self._setup_chrome()
        self._run_trace()
        self.wait(1.0)

    # ── Hooks (default no-ops; override in subclasses) ──────────────────────

    def _setup_chrome(self) -> None:
        """Add title bar and dividing rule.  Call super() from subclasses."""
        title = Text("Call Stack  /  LLVManim", font_size=30, weight=BOLD)
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
        """Called immediately after FadeIn completes.  Play badge animations here."""

    def _on_step_begin(
        self,
        action: str,
        ir_text: str,
        func_name: str,
        caller_name: str = "",
    ) -> None:
        """Called at the start of each trace step before stack animation.

        action      — "push", "alloca", or "pop"
        ir_text     — IR instruction text
        func_name   — callee (push), current frame (alloca), popped frame (pop)
        caller_name — caller name; set for push and pop
        """

    # ── Stack mechanics ─────────────────────────────────────────────────────

    def _color(self) -> ManimColor:
        return _PALETTE[self._depth % len(_PALETTE)]

    def _push(self, func_name: str, ir_text: str = "") -> None:
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
        self.play(FadeIn(mob, shift=DOWN * 0.25), run_time=self._rt(0.5))
        self._on_cell_arrive(mob)

    def _alloca(self, slot_text: str, func_name: str = "") -> None:
        """Slide a new alloca-slot row below the current frame header."""
        if not self._frame_stack:
            return
        fn = func_name or (self._frame_names[-1] if self._frame_names else "")
        self._on_step_begin("alloca", slot_text, fn)
        color = _PALETTE[(self._depth - 1) % len(_PALETTE)]
        # Strip alignment annotations so the label fits the cell width
        display_text = _clean_ir_line(slot_text)
        mob = _slot_cell(display_text, color)
        mob.move_to(RIGHT * self._STACK_X + UP * (self._cursor_y - _SLOT_H / 2))
        self._cursor_y -= _SLOT_H + _GAP
        self._frame_stack[-1][1].append(mob)
        self._before_cell_arrive(mob)
        self.play(FadeIn(mob, shift=DOWN * 0.15), run_time=self._rt(0.4))
        self._on_cell_arrive(mob)

    def _pop(self, func_name: str = "", ir_text: str = "") -> None:
        """Fade out the top frame (slots bottom-to-top, then header)."""
        if not self._frame_stack:
            return
        callee_name = self._frame_names[-1] if self._frame_names else ""
        caller_name = self._frame_names[-2] if len(self._frame_names) >= 2 else ""
        self._on_step_begin("pop", ir_text, callee_name, caller_name)
        if self._frame_names:
            self._frame_names.pop()
        header, slots = self._frame_stack.pop()
        self._depth -= 1
        self._cursor_y += _HEADER_H + _GAP + len(slots) * (_SLOT_H + _GAP)
        mobs_out = slots[::-1] + [header]
        self.play(*[FadeOut(m, shift=UP * 0.2) for m in mobs_out], run_time=self._rt(0.55))

    def _run_trace(self) -> None:
        """Drive the stack animations from the pre-built execution trace."""
        for action, func_name, ir_text in self._trace:
            if action == "push":
                self._push(func_name, ir_text)
            elif action == "alloca":
                self._alloca(ir_text, func_name)
            elif action == "pop":
                self._pop(func_name, ir_text)


# ── Option B: Badge flash ────────────────────────────────────────────────────────


class RichStackSceneBadge(_StackBase):
    """Option B — Stack-only layout with yellow-flash badge on arriving cells.

    No separate IR text panel.  Each arriving cell's label starts yellow and
    settles to white, drawing the viewer's attention to the new instruction
    without a competing panel.
    """

    _STACK_X = 0.5

    def __init__(
        self,
        stream: ProgramEventStream,
        entry: str = "main",
        speed: float = 1.0,
        **kwargs: object,
    ) -> None:
        trace = build_execution_trace(stream, entry)
        super().__init__(trace, speed=speed, **kwargs)

    def _setup_chrome(self) -> None:
        super()._setup_chrome()
        col_label = Text("Stack  (grows ↓)", font_size=21, color=GREY_B)
        col_label.move_to(RIGHT * self._STACK_X + UP * 2.85)
        self.add(col_label)

    def _before_cell_arrive(self, mob: VGroup) -> None:
        mob[1].set_color(YELLOW)

    def _on_cell_arrive(self, mob: VGroup) -> None:
        self.play(mob[1].animate.set_color(WHITE), run_time=self._rt(0.35))


# ── IR panel helpers (Option A) ──────────────────────────────────────────────────


def _build_ir_panel(func_name: str, ir_registry: dict[str, list[str]]) -> VGroup:
    """Build a monospaced VGroup of Text lines for func_name's IR source.

    Each submobject is a single line's Text so that
    panel[line_index].get_center() gives the correct cursor target.
    """
    lines = ir_registry.get(func_name, [f"(no IR available for @{func_name})"])
    group = VGroup()
    for i, line in enumerate(lines):
        txt = Text(line, font="Monospace", font_size=_IR_FONT_SIZE)
        txt.move_to((_IR_PANEL_X, 2.2 - i * _IR_LINE_SPACING, 0))
        txt.align_to((_IR_PANEL_X - 2.6, 0, 0), direction=LEFT)
        group.add(txt)
    return group


def _find_line_idx(ir_lines: list[str], text: str) -> int:
    """Return the index of the first display line that contains *text*.

    Both sides are cleaned with _clean_ir_line so that debug metadata
    differences between the event text and the file text don't cause misses.
    Returns 0 if not found.
    """
    clean_text = _clean_ir_line(" " + text).strip()
    for i, line in enumerate(ir_lines):
        if clean_text and clean_text in line:
            return i
    return 0


def _call_site_idx(ir_lines: list[str], callee: str) -> int:
    """Return the line index of the call to @callee in ir_lines, or 0."""
    for i, line in enumerate(ir_lines):
        if "call" in line and f"@{callee}" in line:
            return i
    return 0


# ── Option A: Spotlight cursor ───────────────────────────────────────────────────


class RichStackSceneSpotlight(_StackBase):
    """Option A — Two-column layout with a moving IR source cursor.

    Left panel  — full IR source for the currently executing function,
                  rendered from the .ll file via build_ir_registry.
    Right panel — live animated stack (inherited from _StackBase).

    A yellow SurroundingRectangle cursor advances to the current instruction
    on every step.  On call the panel FadeTransforms to the callee's IR and
    the cursor jumps to the callee's define line.  On ret the reverse happens
    and the cursor is restored to the call instruction in the caller.
    """

    _STACK_X = 3.0

    def __init__(
        self,
        stream: ProgramEventStream,
        entry: str = "main",
        speed: float = 1.0,
        **kwargs: object,
    ) -> None:
        trace = build_execution_trace(stream, entry)
        self._ir_registry = build_ir_registry(stream.source_path)
        super().__init__(trace, speed=speed, **kwargs)

    def _setup_chrome(self) -> None:
        super()._setup_chrome()

        vdiv = Line(UP * 3.5, DOWN * 4.0, color=GREY_D, stroke_width=1)
        self.add(vdiv)

        ir_lbl = Text("IR Source", font_size=21, color=GREY_B)
        ir_lbl.move_to((_IR_PANEL_X, 2.85, 0))
        self.add(ir_lbl)

        stack_lbl = Text("Stack  (grows ↓)", font_size=21, color=GREY_B)
        stack_lbl.move_to(RIGHT * self._STACK_X + UP * 2.85)
        self.add(stack_lbl)

        # Initialise the IR panel to the first pushed function.
        first_func = next(
            (fn for act, fn, _ in self._trace if act == "push"),
            "main",
        )
        self._ir_panel: VGroup = _build_ir_panel(first_func, self._ir_registry)
        self.add(self._ir_panel)
        self._ir_cursor = SurroundingRectangle(
            self._ir_panel[0], color=YELLOW, buff=0.06, stroke_width=2
        )
        self.add(self._ir_cursor)

        # Track which function's IR is currently on screen.
        self._current_func: str = first_func
        # Stack of (caller_func, call_site_line_idx) for cursor restoration on ret.
        self._call_site_stack: list[tuple[str, int]] = []
        # Current vertical scroll offset: how far UP the panel has shifted.
        self._panel_scroll: float = 0.0

    def _on_step_begin(
        self,
        action: str,
        ir_text: str,
        func_name: str,
        caller_name: str = "",
    ) -> None:
        """Advance the IR cursor and manage panel swaps on call/ret.

        push  — move cursor to the call instruction in the caller, save the
                call-site for restoration, then swap panel to callee (line 0).
        alloca — move cursor to the alloca line (no panel swap).
        pop   — move cursor to the ret instruction in the callee, then swap
                back to the caller and restore the cursor to the call site.
        """
        if action == "push":
            caller_lines = self._ir_registry.get(self._current_func, [])
            call_line = _call_site_idx(caller_lines, func_name)
            self._advance_cursor(call_line)
            self._call_site_stack.append((self._current_func, call_line))
            self._swap_panel(func_name, target_line=0)

        elif action == "alloca":
            ir_lines = self._ir_registry.get(self._current_func, [])
            idx = _find_line_idx(ir_lines, ir_text)
            self._advance_cursor(idx)

        elif action == "pop":
            ir_lines = self._ir_registry.get(self._current_func, [])
            idx = _find_line_idx(ir_lines, ir_text)
            self._advance_cursor(idx)
            if self._call_site_stack:
                restore_func, restore_line = self._call_site_stack.pop()
                self._swap_panel(restore_func, target_line=restore_line)

    def _scroll_to_line(self, idx: int) -> None:
        """Shift the panel (and cursor) so that line *idx* is within the viewport.

        If the target line is already visible, this is a no-op.  Otherwise the
        panel and cursor are animated together so the line lands near the
        vertical centre of the visible area.
        """
        # y coordinate for this line on screen (accounting for current scroll)
        line_y = _IR_PANEL_TOP_Y - idx * _IR_LINE_SPACING + self._panel_scroll
        if _IR_VIEWPORT_BOT <= line_y <= _IR_PANEL_TOP_Y + _IR_LINE_SPACING:
            return  # already visible
        target_y = (_IR_PANEL_TOP_Y + _IR_VIEWPORT_BOT) / 2
        delta = target_y - line_y
        self.play(
            self._ir_panel.animate.shift(UP * delta),
            self._ir_cursor.animate.shift(UP * delta),
            run_time=self._rt(0.25),
        )
        self._panel_scroll += delta

    def _swap_panel(self, new_func: str, target_line: int = 0) -> None:
        """FadeTransform the current IR panel to *new_func*'s panel.

        *target_line* — line index for the cursor in the new panel.
        The new panel starts unscrolled; scroll is applied afterward if needed.
        """
        new_panel = _build_ir_panel(new_func, self._ir_registry)
        self.play(FadeTransform(self._ir_panel, new_panel), run_time=self._rt(0.4))
        self._ir_panel = new_panel
        self._current_func = new_func
        self._panel_scroll = 0.0  # new panel starts at its natural origin
        safe_idx = min(target_line, len(self._ir_panel) - 1)
        new_cursor = SurroundingRectangle(
            self._ir_panel[safe_idx], color=YELLOW, buff=0.06, stroke_width=2
        )
        self.play(FadeTransform(self._ir_cursor, new_cursor), run_time=self._rt(0.25))
        self._ir_cursor = new_cursor
        # Scroll into view if target_line falls below the visible area
        self._scroll_to_line(safe_idx)

    def _advance_cursor(self, line_index: int) -> None:
        """Scroll the panel if needed, then animate the cursor to *line_index*."""
        safe_idx = min(line_index, len(self._ir_panel) - 1)
        self._scroll_to_line(safe_idx)
        new_cursor = SurroundingRectangle(
            self._ir_panel[safe_idx], color=YELLOW, buff=0.06, stroke_width=2
        )
        self.play(self._ir_cursor.animate.become(new_cursor), run_time=self._rt(0.3))
