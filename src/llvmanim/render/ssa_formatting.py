"""SSA value formatting for the bridge panel.

Functions here produce human-readable display strings for SSA computation
results (binop, compare, load). The key function is
:func:`format_display_value` -- it is the **single swap-point** for future
numeric runtime values.  Today it returns symbolic expressions like
``2 x %2``; when a runtime trace provides concrete values, only this
function needs to change.

TODO: When numeric runtime values become available (e.g. extended
      SanitizerCoverage trace), swap format_display_value() to return
      ``str(concrete_value)`` and nothing else in the rendering pipeline
      needs to change.
"""

from __future__ import annotations

import re

from manim import BLUE_D, GOLD_D, GREEN_C, ManimColor

# -- Opcode → symbol mappings ---------------------------------------------------

BINOP_SYMBOLS: dict[str, str] = {
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

CMP_PREDICATES: dict[str, str] = {
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

OP_COLORS: dict[str, ManimColor] = {
    "binop": GREEN_C,
    "compare": GOLD_D,
    "load": BLUE_D,
}

# -- Extraction helpers ---------------------------------------------------------

_SSA_NAME_RE = re.compile(r"(%[\w.]+)\s*=")
_OPCODE_RE = re.compile(r"%[\w.]+\s*=\s*(\w+)")
_CMP_PRED_RE = re.compile(r"(?:icmp|fcmp)\s+(\w+)")
_TYPE_PREFIX_RE = re.compile(r"^\S+\s+")


def extract_ssa_name(ir_text: str) -> str:
    """Extract the LHS SSA name from an instruction like ``%mul = mul ...``."""
    m = _SSA_NAME_RE.match(ir_text.strip())
    return m.group(1) if m else ""


def _clean_operand(raw: str) -> str:
    """Reduce a raw llvmlite operand string to a concise display token.

    ``str(ValueRef)`` for a local variable in llvmlite returns the full
    defining instruction (e.g. ``'  %2 = load i32, ptr %tmp, align 4'``)
    rather than just the name.  For typed constants it returns the type
    and value together (e.g. ``'i32 2'``).

    Returns:
      * The LHS SSA name (``%2``) when the string contains ``=``.
      * The bare value without type prefix (``2``) for typed literals.
      * The input unchanged for anything else.
    """
    s = raw.strip()
    if "=" in s:
        name = extract_ssa_name(s)
        return name if name else s
    # Strip leading LLVM type token ("i32 2" → "2", "ptr %x" → "%x").
    m = _TYPE_PREFIX_RE.match(s)
    return s[m.end():] if m else s


def extract_opcode(ir_text: str) -> str:
    """Extract the opcode from after the ``=`` sign."""
    m = _OPCODE_RE.match(ir_text.strip())
    return m.group(1) if m else ""


# -- Symbolic formatters --------------------------------------------------------


def format_binop(ir_text: str, operands: list[str]) -> str:
    """Format a binary operation as ``operand0 symbol operand1``."""
    opcode = extract_opcode(ir_text)
    sym = BINOP_SYMBOLS.get(opcode, opcode)
    cleaned = [_clean_operand(o) for o in operands]
    if len(cleaned) >= 2:
        return f"{cleaned[0]} {sym} {cleaned[1]}"
    return ir_text.split("=", 1)[-1].strip()


def format_compare(ir_text: str, operands: list[str]) -> str:
    """Format a comparison as ``operand0 predicate_symbol operand1``."""
    m = _CMP_PRED_RE.search(ir_text)
    pred = m.group(1) if m else ""
    sym = CMP_PREDICATES.get(pred, pred)
    cleaned = [_clean_operand(o) for o in operands]
    if len(cleaned) >= 2:
        return f"{cleaned[0]} {sym} {cleaned[1]}"
    return ir_text.split("=", 1)[-1].strip()


def format_load(operands: list[str]) -> str:
    """Format a load as ``load source_operand``."""
    if operands:
        return f"load {_clean_operand(operands[0])}"
    return "load ?"


def format_display_value(action: str, ir_text: str, operands: list[str]) -> str:
    """Produce the human-readable display string for an SSA value.

    **This is the single function to swap when numeric runtime values arrive.**
    Today it returns symbolic expressions; in the future, return
    ``str(concrete_value)`` here and nothing else changes.
    """
    if action == "binop":
        return format_binop(ir_text, operands)
    if action == "compare":
        return format_compare(ir_text, operands)
    if action == "load":
        return format_load(operands)
    return ir_text
