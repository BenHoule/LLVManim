"""Build per-function display lines from raw LLVM IR text.

Provides ``build_display_lines`` which parses a raw ``.ll`` string into a
``dict[str, list[str]]`` mapping bare function names to cleaned,
display-ready IR source lines.  The cleaning removes debug metadata,
attribute references, verbose type qualifiers, and intrinsic calls that
add noise without insight.

The result is stored in ``ProgramEventStream.display_lines`` so the
presentation layer can render IR source panels without re-reading the
``.ll`` file.
"""

from __future__ import annotations

import re

_DBG_META_RE = re.compile(r",?\s*![a-zA-Z0-9_.]+\s+!\d+|,?\s*!\d+\b")
_DEFINE_RE = re.compile(r"^\s*define\b.*?@(\w+)\s*\(")


def clean_ir_line(raw: str) -> str:
    """Strip comments, debug metadata, attribute refs, and verbose type qualifiers.

    Returns the display-friendly version of a raw ``.ll`` source line.
    """
    line = raw.split(";")[0].rstrip()
    line = _DBG_META_RE.sub("", line)
    line = re.sub(r"\s+#\d+\b", "", line)
    line = re.sub(r"\bnoalias\s+", "", line)
    line = re.sub(r"\bnoundef\s+", "", line)
    line = re.sub(r"\bdso_local\s+", "", line)
    line = re.sub(r",\s*align\s+\d+", "", line)
    return line.rstrip(", ")


def build_display_lines(llvm_ir: str) -> dict[str, list[str]]:
    """Parse raw LLVM IR text into per-function display-line lists.

    Keys are bare function names (no ``@``).  Display lines are:

    - Cleaned with :func:`clean_ir_line` (debug metadata, attribute refs removed).
    - ``@llvm`` intrinsic call lines omitted (they add noise, not insight).
    - Blank lines between basic blocks preserved for readability.
    """
    registry: dict[str, list[str]] = {}
    current_func: str | None = None
    current_lines: list[str] = []

    for raw in llvm_ir.splitlines():
        line = raw.rstrip()
        m = _DEFINE_RE.match(line)
        if m:
            current_func = m.group(1)
            current_lines = [clean_ir_line(line)]
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
        if "@llvm." in stripped:
            continue
        clean = clean_ir_line(line)
        if clean.strip():
            current_lines.append(clean)

    return registry
