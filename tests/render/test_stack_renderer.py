"""Unit tests for stack_renderer.py: mobject factories, layout helpers, and early-return paths."""

from __future__ import annotations

from manim import BLUE_D, GREEN_C, Rectangle, Text, VGroup

from llvmanim.render.stack_renderer import (
    _3COL_IR_PANEL_X,
    _HEADER_H,
    _PALETTE,
    _SLOT_H,
    _SLOT_W,
    StackRenderer,
    _build_ir_panel,
    _frame_header,
    _slot_cell,
)
from llvmanim.transform.models import AnimationCommand, SceneGraph

# -- _frame_header ------------------------------------------------------------


class TestFrameHeader:
    def test_returns_vgroup_with_rect_and_label(self) -> None:
        mob = _frame_header("main", BLUE_D)
        assert isinstance(mob, VGroup)
        assert len(mob) == 2

    def test_rect_has_expected_dimensions(self) -> None:
        mob = _frame_header("foo", GREEN_C)
        rect = mob[0]
        assert isinstance(rect, Rectangle)
        assert abs(rect.width - _SLOT_W) < 0.01
        assert abs(rect.height - _HEADER_H) < 0.01

    def test_label_contains_at_prefix(self) -> None:
        mob = _frame_header("my_func", BLUE_D)
        label = mob[1]
        assert isinstance(label, Text)
        assert "@my_func" in label.text

    def test_custom_width(self) -> None:
        mob = _frame_header("f", BLUE_D, width=6.0)
        rect = mob[0]
        assert abs(rect.width - 6.0) < 0.01


# -- _slot_cell ---------------------------------------------------------------


class TestSlotCell:
    def test_returns_vgroup_with_rect_and_label(self) -> None:
        mob = _slot_cell("%x = alloca i32", GREEN_C)
        assert isinstance(mob, VGroup)
        assert len(mob) == 2

    def test_rect_has_expected_dimensions(self) -> None:
        mob = _slot_cell("slot", BLUE_D)
        rect = mob[0]
        assert isinstance(rect, Rectangle)
        assert abs(rect.width - _SLOT_W) < 0.01
        assert abs(rect.height - _SLOT_H) < 0.01

    def test_label_text_matches_input(self) -> None:
        mob = _slot_cell("%ptr = alloca i32*", BLUE_D)
        label = mob[1]
        assert isinstance(label, Text)
        # Manim Text.text strips whitespace; just check key tokens
        assert "%ptr" in label.text
        assert "alloca" in label.text

    def test_custom_width(self) -> None:
        mob = _slot_cell("s", GREEN_C, width=3.0)
        rect = mob[0]
        assert abs(rect.width - 3.0) < 0.01


# -- _build_ir_panel ----------------------------------------------------------


class TestBuildIrPanel:
    def test_builds_panel_from_registry(self) -> None:
        registry = {"main": ["define i32 @main()", "%x = alloca i32", "ret i32 0"]}
        panel = _build_ir_panel("main", registry)
        assert isinstance(panel, VGroup)
        assert len(panel) == 3

    def test_fallback_when_function_missing(self) -> None:
        panel = _build_ir_panel("unknown", {})
        assert len(panel) == 1
        # Manim Text.text collapses whitespace
        assert "noIRavailable" in str(panel[0].text)

    def test_line_positions_descend(self) -> None:
        registry = {"f": ["line1", "line2", "line3"]}
        panel = _build_ir_panel("f", registry)
        y0 = panel[0].get_center()[1]
        y1 = panel[1].get_center()[1]
        y2 = panel[2].get_center()[1]
        assert y0 > y1 > y2


# -- _reposition_ir_panel -----------------------------------------------------


class TestRepositionIrPanel:
    def test_shifts_panel_to_3col_position(self) -> None:
        registry = {"f": ["line1", "line2"]}
        panel = _build_ir_panel("f", registry)
        graph = SceneGraph()
        renderer = StackRenderer(graph, ir_mode="rich-ssa")
        renderer._reposition_ir_panel(panel)
        x0 = panel[0].get_center()[0]
        assert abs(x0 - _3COL_IR_PANEL_X) < 2.5  # near 3-col x (after left-align)


# -- StackRenderer._color ----------------------------------------------------


class TestRendererColor:
    def test_color_cycles_through_palette(self) -> None:
        graph = SceneGraph()
        renderer = StackRenderer(graph, ir_mode="basic")
        for i in range(len(_PALETTE) + 1):
            renderer._depth = i
            assert renderer._color() == _PALETTE[i % len(_PALETTE)]


# -- IR cursor early returns (basic mode) -------------------------------------


class TestIrCursorBasicModeNoop:
    """In basic mode the _ir_on_* methods return immediately."""

    def test_ir_on_push_noop(self) -> None:
        graph = SceneGraph()
        renderer = StackRenderer(graph, ir_mode="basic")
        renderer._ir_on_push("main")  # should not raise

    def test_ir_on_alloca_noop(self) -> None:
        graph = SceneGraph()
        renderer = StackRenderer(graph, ir_mode="basic")
        renderer._ir_on_alloca("%x = alloca i32")

    def test_ir_on_pop_noop(self) -> None:
        graph = SceneGraph()
        renderer = StackRenderer(graph, ir_mode="basic")
        renderer._ir_on_pop("ret i32 0")

    def test_ir_on_ssa_noop(self) -> None:
        graph = SceneGraph()
        renderer = StackRenderer(graph, ir_mode="basic")
        renderer._ir_on_ssa("%1 = add i32 %a, %b")


# -- _ssa_after_pop early returns ---------------------------------------------


class TestSsaAfterPopNoop:
    def test_noop_in_basic_mode(self) -> None:
        graph = SceneGraph()
        renderer = StackRenderer(graph, ir_mode="basic")
        renderer._ssa_after_pop()  # should not raise

    def test_noop_in_rich_mode(self) -> None:
        graph = SceneGraph()
        renderer = StackRenderer(graph, ir_mode="rich")
        renderer._ssa_after_pop()

    def test_noop_in_rich_ssa_with_no_entries(self) -> None:
        graph = SceneGraph()
        renderer = StackRenderer(graph, ir_mode="rich-ssa")
        renderer._ssa_entries = []
        renderer._ssa_after_pop()


# -- _handle_branch (no-op) --------------------------------------------------


def test_handle_branch_is_noop() -> None:
    graph = SceneGraph()
    renderer = StackRenderer(graph, ir_mode="basic")
    cmd = AnimationCommand(action="highlight_branch", target="f::entry")
    renderer._handle_branch(cmd)  # should not raise
