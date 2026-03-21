"""SSA value formatting for the bridge panel.

Functions here produce human-readable display strings for SSA computation
results (binop, compare, load).  The key function is
:func:`format_display_value` — it is the **single swap-point** for future
numeric runtime values.  Today it returns symbolic expressions like
``2 × %2``; when a runtime trace provides concrete values, only this
function needs to change.

TODO: When numeric runtime values become available (e.g. extended
      SanitizerCoverage trace), swap format_display_value() to return
      ``str(concrete_value)`` and nothing else in the rendering pipeline
      needs to change.
"""

from __future__ import annotations

import re

from manim import BLUE_D, GOLD_D, GREEN_C, ManimColor

# ── Opcode → symbol mappings ───────────────────────────────────────────────────

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

# ── Extraction helpers ─────────────────────────────────────────────────────────

_SSA_NAME_RE = re.compile(r"(%[\w.]+)\s*=")
_OPCODE_RE = re.compile(r"%[\w.]+\s*=\s*(\w+)")
_CMP_PRED_RE = re.compile(r"(?:icmp|fcmp)\s+(\w+)")


def extract_ssa_name(ir_text: str) -> str:
    """Extract the LHS SSA name from an instruction like ``%mul = mul ...``."""
    m = _SSA_NAME_RE.match(ir_text.strip())
    return m.group(1) if m else ""


def extract_opcode(ir_text: str) -> str:
    """Extract the opcode from after the ``=`` sign."""
    m = _OPCODE_RE.match(ir_text.strip())
    return m.group(1) if m else ""


# ── Symbolic formatters ────────────────────────────────────────────────────────


def format_binop(ir_text: str, operands: list[str]) -> str:
    """Format a binary operation as ``operand0 symbol operand1``."""
    opcode = extract_opcode(ir_text)
    sym = BINOP_SYMBOLS.get(opcode, opcode)
    if len(operands) >= 2:
        return f"{operands[0]} {sym} {operands[1]}"
    return ir_text.split("=", 1)[-1].strip()


def format_compare(ir_text: str, operands: list[str]) -> str:
    """Format a comparison as ``operand0 predicate_symbol operand1``."""
    m = _CMP_PRED_RE.search(ir_text)
    pred = m.group(1) if m else ""
    sym = CMP_PREDICATES.get(pred, pred)
    if len(operands) >= 2:
        return f"{operands[0]} {sym} {operands[1]}"
    return ir_text.split("=", 1)[-1].strip()


def format_load(operands: list[str]) -> str:
    """Format a load as ``load source_operand``."""
    if operands:
        return f"load {operands[0]}"
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
