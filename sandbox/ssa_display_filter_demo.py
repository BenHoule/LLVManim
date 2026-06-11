"""Sandbox: fix for `align`/`!dbg` appearing in the rich-SSA *SSA Values* column.

ROOT CAUSE
──────────
In llvmlite, ``str(ValueRef)`` for a local variable operand returns the
**full defining instruction** of that variable, not just its name.  For
example, the operand ``%2`` in ``%mul = mul nsw i32 2, %2`` is printed as:

    '  %2 = load i32, ptr %tmp, align 4'

So ``event.operands`` (built as ``[str(op) for op in instr.operands]``) ends
up carrying complete instruction strings with ``align``, ``!dbg``, etc.
These land verbatim in the SSA Values display via ``format_binop`` /
``format_load``, producing rows like:

    %mul = i32 2 × %2 = load i32, ptr %tmp, align 4    ← BROKEN

THE FIX
───────
``_clean_operand`` normalises each operand string:
  • If it contains ``=``, it is a defining instruction — extract the LHS
    SSA name with ``extract_ssa_name`` (gives ``%2``).
  • Otherwise strip the LLVM type prefix (``i32 2`` → ``2``).

This function belongs in ``render/ssa_formatting.py``.  The callers
``format_binop``, ``format_compare``, and ``format_load`` each clean their
operands before building the display string.

Run:
    uv run python sandbox/ssa_display_filter_demo.py
"""

from __future__ import annotations

import os
import re
import sys

# Allow running from the repo root or from sandbox/.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import llvmlite.binding as llvm

from llvmanim.render.ssa_formatting import (
    extract_ssa_name,
    format_binop,
    format_compare,
    format_load,
)

# ── Proposed fix: _clean_operand ────────────────────────────────────────────────


def _clean_operand(raw: str) -> str:
    """Reduce a raw llvmlite operand string to a concise display token.

    llvmlite's ``str(ValueRef)`` for a local variable gives the full
    defining instruction (e.g. ``'  %2 = load i32, ptr %tmp, align 4'``).
    For constants it gives the typed literal (e.g. ``'i32 2'``).

    Returns:
      • The LHS SSA name (``%2``) when the operand contains ``=``.
      • The bare value without type prefix (``2``) for typed constants.
      • The input unchanged for anything else.
    """
    s = raw.strip()
    if "=" in s:
        name = extract_ssa_name(s)
        return name if name else s
    # Strip leading type token (e.g. "i32 2" → "2", "ptr %x" → "%x")
    parts = s.split(None, 1)
    return parts[1] if len(parts) == 2 else s


def _patched_format_binop(ir_text: str, operands: list[str]) -> str:
    return format_binop(ir_text, [_clean_operand(o) for o in operands])


def _patched_format_compare(ir_text: str, operands: list[str]) -> str:
    return format_compare(ir_text, [_clean_operand(o) for o in operands])


def _patched_format_load(operands: list[str]) -> str:
    return format_load([_clean_operand(o) for o in operands])


# ── Parse double.ll with llvmlite to get real operand strings ────────────────────

_DOUBLE_LL_PATH = os.path.join(os.path.dirname(__file__), "..", "double.ll")


def _load_module() -> llvm.ModuleRef:
    with open(_DOUBLE_LL_PATH) as f:
        ir_text = f.read()
    return llvm.parse_assembly(ir_text)


# ── Build comparison table ────────────────────────────────────────────────────────

_W_DESC = 32
_W_BEFORE = 54
_SSA_PANEL_WIDTH = 35  # approximate SSA Values column width in rich-ssa mode
_WARN = " ← OVERFLOW"


def _flag(text: str) -> str:
    return _WARN if len(text.strip()) > _SSA_PANEL_WIDTH else ""


_OPCODE_TO_KIND = {
    "mul": "binop",
    "add": "binop",
    "sub": "binop",
    "udiv": "binop",
    "sdiv": "binop",
    "shl": "binop",
    "lshr": "binop",
    "ashr": "binop",
    "and": "binop",
    "or": "binop",
    "xor": "binop",
    "fadd": "binop",
    "fsub": "binop",
    "fmul": "binop",
    "fdiv": "binop",
    "icmp": "compare",
    "fcmp": "compare",
    "load": "load",
}


def main() -> None:
    mod = _load_module()

    rows: list[tuple[str, str, str, str]] = []  # (func, instr_text, before, after)

    for fn in mod.functions:
        for blk in fn.blocks:
            for instr in blk.instructions:
                opcode = instr.opcode
                kind = _OPCODE_TO_KIND.get(opcode)
                if kind is None:
                    continue

                raw_text = str(instr).strip()
                ops = [str(op) for op in instr.operands]

                # Current output (raw operands)
                if kind == "binop":
                    before_val = format_binop(raw_text, ops)
                elif kind == "compare":
                    before_val = format_compare(raw_text, ops)
                else:
                    before_val = format_load(ops)

                # Proposed output (cleaned operands)
                if kind == "binop":
                    after_val = _patched_format_binop(raw_text, ops)
                elif kind == "compare":
                    after_val = _patched_format_compare(raw_text, ops)
                else:
                    after_val = _patched_format_load(ops)

                ssa_name = extract_ssa_name(raw_text)
                desc = f"{fn.name} / {ssa_name or opcode}"
                rows.append((desc, raw_text, before_val, after_val))

    header = f"\n  {'Instruction':<{_W_DESC}}  {'BEFORE (current)':<{_W_BEFORE}}  AFTER (proposed)"
    sep = "  " + "-" * (_W_DESC + _W_BEFORE + 50)

    print(header)
    print(sep)

    overflow_before = overflow_after = 0
    for desc, raw_text, before_val, after_val in rows:
        label_before = f"{extract_ssa_name(raw_text)} = {before_val}".strip("= ")
        label_after = f"{extract_ssa_name(raw_text)} = {after_val}".strip("= ")
        if len(before_val) > _SSA_PANEL_WIDTH:
            overflow_before += 1
        if len(after_val) > _SSA_PANEL_WIDTH:
            overflow_after += 1
        changed = "" if before_val != after_val else "  (unchanged)"
        print(f"  {desc:<{_W_DESC}}  {label_before:<{_W_BEFORE}}{_flag(before_val)}")
        print(f"  {' ':<{_W_DESC}}  {label_after}{_flag(after_val)}{changed}")
        print()

    print(sep)
    print(
        f"\n  SSA value display_value strings exceeding ~{_SSA_PANEL_WIDTH} chars: "
        f"{overflow_before} → {overflow_after}  "
        f"({'no change' if overflow_before == overflow_after else 'improved'})\n"
    )
    print("  Root cause: llvmlite str(ValueRef) for a local variable returns")
    print("  the full defining instruction, not just the name.")
    print()
    print("  Fix: _clean_operand() in ssa_formatting.py, called by")
    print("  format_binop / format_compare / format_load before building")
    print("  the display string.\n")


if __name__ == "__main__":
    main()
