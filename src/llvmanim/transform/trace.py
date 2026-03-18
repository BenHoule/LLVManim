"""Execution-trace builder: simulates a call tree from a flat IR event stream."""

from __future__ import annotations

import re
from collections import defaultdict

from llvmanim.transform.models import ProgramEventStream

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
