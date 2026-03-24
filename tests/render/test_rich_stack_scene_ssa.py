"""Integration tests for SSA panel support in StackRenderer."""

from __future__ import annotations

from manim import GREEN_C

from llvmanim.render.stack_renderer import (
    _3COL_SLOT_W,
    _3COL_STACK_X,
    StackRenderer,
    _ssa_row,
)
from llvmanim.transform.models import (
    IREvent,
    SceneGraph,
)


def _event(
    fn: str,
    kind: str,
    text: str,
    idx: int,
    opcode: str | None = None,
    operands: list[str] | None = None,
) -> IREvent:
    return IREvent(
        function_name=fn,
        block_name="entry",
        opcode=opcode or kind,
        text=text,
        kind=kind,  # type: ignore[arg-type]
        index_in_function=idx,
        debug_line=None,
        operands=operands or [],
    )


# ── _ssa_row factory ────────────────────────────────────────────────────────────


class TestSsaRow:
    def test_returns_vgroup_with_rect_and_label(self) -> None:
        mob = _ssa_row("%1", "2 × %2", GREEN_C)
        assert len(mob) == 2  # rect + label

    def test_label_text_contains_name_and_value(self) -> None:
        from manim import BLUE_D

        mob = _ssa_row("%x", "load %ptr", BLUE_D)
        label_text: str = mob[1].text  # type: ignore[union-attr]
        assert "%x" in label_text
        assert "load" in label_text
        assert "%ptr" in label_text


# ── StackRenderer SSA handler registration ──────────────────────────────────────


class TestStackRendererSsaRegistration:
    """Verify that ir_mode='rich-ssa' registers SSA handlers."""

    def test_rich_ssa_registers_ssa_handlers(self) -> None:
        graph = SceneGraph()
        renderer = StackRenderer(graph, ir_mode="rich-ssa")
        expected = {"animate_binop", "animate_compare", "animate_memory_read"}
        assert expected.issubset(set(renderer._handlers.keys()))

    def test_basic_does_not_register_ssa_handlers(self) -> None:
        graph = SceneGraph()
        renderer = StackRenderer(graph, ir_mode="basic")
        for action in ("animate_binop", "animate_compare", "animate_memory_read"):
            assert action not in renderer._handlers

    def test_rich_does_not_register_ssa_handlers(self) -> None:
        graph = SceneGraph()
        renderer = StackRenderer(graph, ir_mode="rich")
        for action in ("animate_binop", "animate_compare", "animate_memory_read"):
            assert action not in renderer._handlers


# ── StackRenderer 3-column layout ───────────────────────────────────────────────


class TestStackRendererRichSsaLayout:
    """Test that ir_mode='rich-ssa' activates 3-column mode."""

    def test_rich_ssa_sets_3col_stack_x(self) -> None:
        graph = SceneGraph()
        renderer = StackRenderer(graph, ir_mode="rich-ssa")
        assert renderer._STACK_X == _3COL_STACK_X

    def test_rich_ssa_sets_3col_slot_width(self) -> None:
        graph = SceneGraph()
        renderer = StackRenderer(graph, ir_mode="rich-ssa")
        assert renderer._SLOT_WIDTH == _3COL_SLOT_W

    def test_rich_keeps_2col_stack_x(self) -> None:
        graph = SceneGraph()
        renderer = StackRenderer(graph, ir_mode="rich")
        assert renderer._STACK_X == 3.0

    def test_basic_keeps_default_stack_x(self) -> None:
        graph = SceneGraph()
        renderer = StackRenderer(graph, ir_mode="basic")
        assert renderer._STACK_X == 0.5


# ── SSA pop cleanup ─────────────────────────────────────────────────────────────


class TestSsaCleanupOnPop:
    """Verify SSA entries are returned for fade-out when owning frame pops."""

    def test_ssa_pop_cleanup_returns_owned_entries(self) -> None:
        graph = SceneGraph()
        renderer = StackRenderer(graph, ir_mode="rich-ssa")
        # Manually set up SSA state (normally done by _setup_ir_chrome)
        renderer._ssa_entries = []
        renderer._ssa_cursor_y = 1.0

        mob1 = _ssa_row("%1", "val", GREEN_C)
        mob2 = _ssa_row("%2", "val", GREEN_C)
        renderer._ssa_entries = [(mob1, "foo"), (mob2, "bar")]

        result = renderer._ssa_pop_cleanup("foo")
        assert mob1 in result
        assert mob2 not in result
        assert len(renderer._ssa_entries) == 1
        assert renderer._ssa_entries[0][1] == "bar"

    def test_ssa_pop_cleanup_noop_in_basic_mode(self) -> None:
        graph = SceneGraph()
        renderer = StackRenderer(graph, ir_mode="basic")
        result = renderer._ssa_pop_cleanup("foo")
        assert result == []

    def test_ssa_pop_cleanup_noop_in_rich_mode(self) -> None:
        graph = SceneGraph()
        renderer = StackRenderer(graph, ir_mode="rich")
        result = renderer._ssa_pop_cleanup("foo")
        assert result == []
