"""Unit tests for SSA value formatting (present.ssa_formatting)."""

from __future__ import annotations

from llvmanim.render.ssa_formatting import (
    _clean_operand,
    extract_opcode,
    extract_ssa_name,
    format_binop,
    format_compare,
    format_display_value,
    format_load,
)

# -- extract_ssa_name -----------------------------------------------------------


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


# -- extract_opcode -------------------------------------------------------------


class TestExtractOpcode:
    def test_mul(self) -> None:
        assert extract_opcode("%mul = mul nsw i32 2, %2") == "mul"

    def test_icmp(self) -> None:
        assert extract_opcode("%cmp = icmp slt i32 %2, 100") == "icmp"

    def test_load(self) -> None:
        assert extract_opcode("%2 = load i32, ptr %tmp") == "load"

    def test_no_match(self) -> None:
        assert extract_opcode("store i32 1, ptr %0") == ""


# -- format_binop ---------------------------------------------------------------


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


# -- format_compare -------------------------------------------------------------


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


# -- format_load ----------------------------------------------------------------


class TestFormatLoad:
    def test_with_operand(self) -> None:
        assert format_load(["%p.addr"]) == "load %p.addr"

    def test_empty_operands(self) -> None:
        assert format_load([]) == "load ?"


# -- format_display_value (dispatch) --------------------------------------------


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


# ── _clean_operand ─────────────────────────────────────────────────────────────


class TestCleanOperand:
    def test_defining_instruction_extracts_name(self) -> None:
        raw = "  %2 = load i32, ptr %tmp, align 4"
        assert _clean_operand(raw) == "%2"

    def test_defining_instruction_with_dbg(self) -> None:
        raw = "  %mul = mul nsw i32 2, %2, !dbg !32"
        assert _clean_operand(raw) == "%mul"

    def test_typed_integer_constant(self) -> None:
        assert _clean_operand("i32 2") == "2"

    def test_typed_pointer_operand(self) -> None:
        assert _clean_operand("ptr %p.addr") == "%p.addr"

    def test_bare_name_unchanged(self) -> None:
        assert _clean_operand("%x") == "%x"

    def test_bare_integer_unchanged(self) -> None:
        assert _clean_operand("100") == "100"


# ── llvmlite raw operand forms through formatters ─────────────────────────────


class TestFormattersWithRawLlvmliteOperands:
    """Formatters must produce clean output when given the raw str(ValueRef)
    strings that llvmlite emits (full defining instruction for locals, typed
    literal for constants)."""

    def test_binop_with_llvmlite_operands(self) -> None:
        # As emitted by llvmlite for `%mul = mul nsw i32 2, %2`
        ops = ["i32 2", "  %2 = load i32, ptr %tmp, align 4"]
        result = format_binop("%mul = mul nsw i32 2, %2", ops)
        assert result == "2 × %2"

    def test_compare_with_llvmlite_operands(self) -> None:
        # As emitted by llvmlite for `%cmp = icmp slt i32 %2, 100`
        ops = ["  %2 = load i32, ptr %1, align 4", "i32 100"]
        result = format_compare("%cmp = icmp slt i32 %2, 100", ops)
        assert result == "%2 < 100"

    def test_load_with_llvmlite_operand(self) -> None:
        # As emitted by llvmlite for `%1 = load i32, ptr %0`
        ops = ["  %0 = load ptr, ptr %p.addr, align 8"]
        result = format_load(ops)
        assert result == "load %0"

    def test_no_align_or_dbg_in_output(self) -> None:
        ops = ["i32 2", "  %2 = load i32, ptr %tmp, align 4, !dbg !32"]
        result = format_binop("%mul = mul nsw i32 2, %2", ops)
        assert "align" not in result
        assert "!dbg" not in result
