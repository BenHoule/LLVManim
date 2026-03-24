"""Unit tests for SSA value formatting (present.ssa_formatting)."""

from __future__ import annotations

from llvmanim.render.ssa_formatting import (
    extract_opcode,
    extract_ssa_name,
    format_binop,
    format_compare,
    format_display_value,
    format_load,
)

# ── extract_ssa_name ───────────────────────────────────────────────────────────


class TestExtractSSAName:
    def test_simple(self) -> None:
        assert extract_ssa_name("%mul = mul nsw i32 2, %2") == "%mul"

    def test_numbered(self) -> None:
        assert extract_ssa_name("%0 = load ptr, ptr %p.addr") == "%0"

    def test_dotted(self) -> None:
        assert extract_ssa_name("%p.addr = alloca ptr") == "%p.addr"

    def test_no_match(self) -> None:
        assert extract_ssa_name("store i32 1, ptr %0") == ""

    def test_leading_whitespace(self) -> None:
        assert extract_ssa_name("  %cmp = icmp slt i32 %2, 100") == "%cmp"


# ── extract_opcode ─────────────────────────────────────────────────────────────


class TestExtractOpcode:
    def test_mul(self) -> None:
        assert extract_opcode("%mul = mul nsw i32 2, %2") == "mul"

    def test_icmp(self) -> None:
        assert extract_opcode("%cmp = icmp slt i32 %2, 100") == "icmp"

    def test_load(self) -> None:
        assert extract_opcode("%2 = load i32, ptr %tmp") == "load"

    def test_no_match(self) -> None:
        assert extract_opcode("store i32 1, ptr %0") == ""


# ── format_binop ───────────────────────────────────────────────────────────────


class TestFormatBinop:
    def test_mul(self) -> None:
        assert format_binop("%mul = mul nsw i32 2, %2", ["2", "%2"]) == "2 × %2"

    def test_add(self) -> None:
        assert format_binop("%r = add i32 %a, %b", ["%a", "%b"]) == "%a + %b"

    def test_sub(self) -> None:
        assert format_binop("%r = sub i32 %a, 1", ["%a", "1"]) == "%a − 1"

    def test_sdiv(self) -> None:
        assert format_binop("%r = sdiv i32 %a, %b", ["%a", "%b"]) == "%a ÷ %b"

    def test_and(self) -> None:
        assert format_binop("%r = and i32 %a, %b", ["%a", "%b"]) == "%a & %b"

    def test_shl(self) -> None:
        assert format_binop("%r = shl i32 %a, 2", ["%a", "2"]) == "%a << 2"

    def test_float_add(self) -> None:
        assert format_binop("%r = fadd float %a, %b", ["%a", "%b"]) == "%a + %b"

    def test_unknown_opcode_passthrough(self) -> None:
        result = format_binop("%r = myop i32 %a, %b", ["%a", "%b"])
        assert result == "%a myop %b"

    def test_insufficient_operands_fallback(self) -> None:
        result = format_binop("%r = add i32 %a", ["%a"])
        assert "add" in result


# ── format_compare ─────────────────────────────────────────────────────────────


class TestFormatCompare:
    def test_slt(self) -> None:
        assert format_compare("%cmp = icmp slt i32 %2, 100", ["%2", "100"]) == "%2 < 100"

    def test_eq(self) -> None:
        assert format_compare("%cmp = icmp eq i32 %a, %b", ["%a", "%b"]) == "%a == %b"

    def test_ne(self) -> None:
        assert format_compare("%cmp = icmp ne i32 %a, 0", ["%a", "0"]) == "%a != 0"

    def test_sge(self) -> None:
        assert format_compare("%cmp = icmp sge i32 %a, %b", ["%a", "%b"]) == "%a >= %b"

    def test_float_olt(self) -> None:
        assert format_compare("%cmp = fcmp olt float %a, %b", ["%a", "%b"]) == "%a < %b"

    def test_insufficient_operands_fallback(self) -> None:
        result = format_compare("%cmp = icmp slt i32 %a", ["%a"])
        assert "icmp" in result


# ── format_load ────────────────────────────────────────────────────────────────


class TestFormatLoad:
    def test_with_operand(self) -> None:
        assert format_load(["%p.addr"]) == "load %p.addr"

    def test_empty_operands(self) -> None:
        assert format_load([]) == "load ?"


# ── format_display_value (dispatch) ────────────────────────────────────────────


class TestFormatDisplayValue:
    def test_binop_dispatch(self) -> None:
        result = format_display_value("binop", "%mul = mul nsw i32 2, %2", ["2", "%2"])
        assert result == "2 × %2"

    def test_compare_dispatch(self) -> None:
        result = format_display_value("compare", "%cmp = icmp slt i32 %2, 100", ["%2", "100"])
        assert result == "%2 < 100"

    def test_load_dispatch(self) -> None:
        result = format_display_value("load", "%0 = load ptr, ptr %p.addr", ["%p.addr"])
        assert result == "load %p.addr"

    def test_unknown_action_returns_ir_text(self) -> None:
        result = format_display_value("store", "store i32 1, ptr %0", [])
        assert result == "store i32 1, ptr %0"
