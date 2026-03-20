"""Integration tests for SSA panel support in RichStackSceneSpotlight."""

from __future__ import annotations

from unittest.mock import MagicMock

from llvmanim.present.rich_stack_scene import (
    RichStackSceneSpotlight,
    _ssa_row,
    _StackBase,
)
from llvmanim.transform.models import IREvent, ProgramEventStream
from llvmanim.transform.trace import RichTraceStep


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
        from manim import GREEN_C

        mob = _ssa_row("%1", "2 × %2", GREEN_C)
        assert len(mob) == 2  # rect + label

    def test_label_text_contains_name_and_value(self) -> None:
        from manim import BLUE_D

        mob = _ssa_row("%x", "load %ptr", BLUE_D)
        # Manim Text strips spaces internally, so check without spaces
        label_text: str = mob[1].text  # type: ignore[union-attr]
        assert "%x" in label_text
        assert "load" in label_text
        assert "%ptr" in label_text


# ── _StackBase _run_trace dispatching ───────────────────────────────────────────


class TestStackBaseRichDispatch:
    """Verify _run_trace dispatches binop/compare/load to _on_ssa_step."""

    def test_dispatches_binop_to_on_ssa_step(self) -> None:
        trace = [
            RichTraceStep("push", "main", "call @main", []),
            RichTraceStep("binop", "main", "%1 = add i32 %a, %b", ["%a", "%b"]),
        ]
        scene = _StackBase(trace)
        calls: list[tuple[str, str, list[str], str]] = []
        scene._on_ssa_step = lambda a, t, o, f: calls.append((a, t, o, f))  # type: ignore[assignment]
        scene.play = MagicMock()  # type: ignore[assignment]
        scene.add = MagicMock()  # type: ignore[assignment]
        scene.wait = MagicMock()  # type: ignore[assignment]
        scene.construct()
        assert len(calls) == 1
        assert calls[0][0] == "binop"
        assert calls[0][2] == ["%a", "%b"]

    def test_dispatches_legacy_trace_step(self) -> None:
        """Legacy 3-element TraceSteps still work."""
        trace = [("push", "main", "call @main"), ("alloca", "main", "%x = alloca")]
        scene = _StackBase(trace)
        scene.play = MagicMock()  # type: ignore[assignment]
        scene.add = MagicMock()  # type: ignore[assignment]
        scene.wait = MagicMock()  # type: ignore[assignment]
        scene.construct()
        assert scene._depth == 1


# ── RichStackSceneSpotlight enable_ssa ──────────────────────────────────────────


class TestSpotlightEnableSsa:
    """Test that enable_ssa=True activates 3-column mode."""

    def _make_stream(self, tmp_path):
        """Create a minimal ProgramEventStream for testing."""
        ir_file = tmp_path / "test.ll"
        ir_file.write_text(
            "define i32 @main() {\n"
            "entry:\n"
            "  %x = alloca i32\n"
            "  %1 = add i32 1, 2\n"
            "  ret i32 %1\n"
            "}\n"
        )
        events = [
            _event("main", "call", "call @main", 0),
            _event("main", "alloca", "%x = alloca i32", 1),
            _event("main", "binop", "%1 = add i32 1, 2", 2, operands=["%a", "%b"]),
            _event("main", "ret", "ret i32 %1", 3),
        ]
        return ProgramEventStream(source_path=ir_file.as_posix(), events=events)

    def test_enable_ssa_sets_3col_stack_x(self, tmp_path) -> None:
        stream = self._make_stream(tmp_path)
        scene = RichStackSceneSpotlight(stream, enable_ssa=True)
        from llvmanim.present.rich_stack_scene import _3COL_STACK_X

        assert scene._STACK_X == _3COL_STACK_X

    def test_enable_ssa_false_keeps_default_stack_x(self, tmp_path) -> None:
        stream = self._make_stream(tmp_path)
        scene = RichStackSceneSpotlight(stream, enable_ssa=False)
        assert scene._STACK_X == 3.0

    def test_enable_ssa_sets_slot_width(self, tmp_path) -> None:
        stream = self._make_stream(tmp_path)
        scene = RichStackSceneSpotlight(stream, enable_ssa=True)
        from llvmanim.present.rich_stack_scene import _3COL_SLOT_W

        assert scene._SLOT_WIDTH == _3COL_SLOT_W

    def test_enable_ssa_passes_include_ssa_to_trace_builder(self, tmp_path) -> None:
        stream = self._make_stream(tmp_path)
        scene = RichStackSceneSpotlight(stream, enable_ssa=True)
        # The trace should contain RichTraceStep instances (4-element tuples)
        rich_steps = [s for s in scene._trace if len(s) >= 4]
        assert len(rich_steps) > 0  # At least the binop should be there


# ── _on_pop_cleanup and _after_pop ──────────────────────────────────────────────


class TestSsaCleanupOnPop:
    """Verify SSA entries are returned for fade-out when owning frame pops."""

    def test_on_pop_cleanup_returns_owned_entries(self) -> None:
        scene = RichStackSceneSpotlight.__new__(RichStackSceneSpotlight)
        scene._enable_ssa = True
        from manim import GREEN_C

        mob1 = _ssa_row("%1", "val", GREEN_C)
        mob2 = _ssa_row("%2", "val", GREEN_C)
        scene._ssa_entries = [(mob1, "foo"), (mob2, "bar")]
        scene._ssa_cursor_y = 1.0

        result = scene._on_pop_cleanup("foo")
        assert mob1 in result
        assert mob2 not in result
        assert len(scene._ssa_entries) == 1
        assert scene._ssa_entries[0][1] == "bar"

    def test_on_pop_cleanup_noop_without_enable_ssa(self) -> None:
        scene = RichStackSceneSpotlight.__new__(RichStackSceneSpotlight)
        scene._enable_ssa = False
        result = scene._on_pop_cleanup("foo")
        assert result == []
