"""Execution-trace builder: simulates a call tree from a flat IR event stream."""

from __future__ import annotations

import re
from collections import defaultdict
from typing import NamedTuple

from llvmanim.transform.models import ProgramEventStream, SceneGraph, TraceOverlay

_CALLEE_RE = re.compile(r"call\b[^@]*@(\w+)\s*\(")

# A trace element: ("push" | "alloca" | "pop", func_name, ir_text)
TraceStep = tuple[str, str, str]


class RichTraceStep(NamedTuple):
    """Extended trace step that also carries operand information.

    Used by the SSA bridge panel to format symbolic expressions for
    binop, compare, and load operations.
    """

    action: str  # "push" | "alloca" | "pop" | "binop" | "compare" | "load"
    func_name: str
    ir_text: str
    operands: list[str]


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
    *,
    include_ssa: bool = False,
) -> list[TraceStep] | list[RichTraceStep]:
    """Build an execution-ordered trace by simulating a call tree from *entry*.

    The IR event stream is grouped per function.  Starting from *entry*, each
    function's events are walked in order; call events recursively descend into
    the callee.  External functions (declared but not defined) are silently
    skipped.  Only one iteration of any loop is modelled (IR instructions
    appear once regardless of runtime loop count).

    When *include_ssa* is ``False`` (default), returns a list of
    ``(action, func_name, ir_text)`` triples (backward-compatible).
    When ``True``, returns :class:`RichTraceStep` named tuples that also
    carry ``operands`` for binop, compare, and load formatting.
    """
    func_events: dict[str, list] = defaultdict(list)
    for event in stream.events:
        func_events[event.function_name].append(event)

    defined: frozenset[str] = frozenset(func_events)

    if include_ssa:
        rich_trace: list[RichTraceStep] = []

        def walk_rich(func_name: str, depth: int) -> None:
            if depth > max_depth or func_name not in defined:
                return
            rich_trace.append(RichTraceStep("push", func_name, "", []))
            for event in func_events[func_name]:
                if event.kind == "alloca":
                    rich_trace.append(RichTraceStep("alloca", func_name, event.text, []))
                elif event.kind == "call":
                    callee = _extract_callee(event.text)
                    if callee and callee in defined and not callee.startswith("llvm"):
                        walk_rich(callee, depth + 1)
                elif event.kind in ("binop", "compare", "load"):
                    rich_trace.append(
                        RichTraceStep(event.kind, func_name, event.text, list(event.operands))
                    )
                elif event.kind == "ret":
                    rich_trace.append(RichTraceStep("pop", func_name, event.text, []))
                    return

        walk_rich(entry, 0)
        return rich_trace

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


def derive_cfg_trace(
    graph: SceneGraph,
    function: str = "main",
    *,
    max_loop_iterations: int = 7,
) -> TraceOverlay:
    """Derive a static CFG trace by walking edges from the entry block.

    Branches with a "T" (true) label are taken first; the walk terminates at
    a block with no outgoing edges or when a loop back-edge has been followed
    *max_loop_iterations* times.

    Returns a fully populated :class:`TraceOverlay`.
    """

    adj: dict[str, list[tuple[str, str]]] = {}
    for edge in graph.edges:
        adj.setdefault(edge.source, []).append((edge.target, edge.label))

    # Sort successors so T-labeled edges come before F-labeled, giving a
    # predictable branch-taken-first walk.
    for succs in adj.values():
        succs.sort(key=lambda pair: (pair[1] != "T", pair[1]))

    entry_id = f"{function}::entry"
    if entry_id not in {n.id for n in graph.nodes}:
        return TraceOverlay()

    entry_order: list[str] = []
    edge_counts: dict[tuple[str, str], int] = {}
    current = entry_id

    while True:
        entry_order.append(current)
        successors = adj.get(current, [])
        if not successors:
            break
        moved = False
        for target, _label in successors:
            key = (current, target)
            count = edge_counts.get(key, 0)
            if count >= max_loop_iterations:
                continue
            edge_counts[key] = count + 1
            current = target
            moved = True
            break
        if not moved:
            break

    visited = list(dict.fromkeys(entry_order))
    traversed: list[tuple[str, str]] = []
    for i in range(len(entry_order) - 1):
        edge = (entry_order[i], entry_order[i + 1])
        if edge not in traversed:
            traversed.append(edge)

    termination = "ret" if not adj.get(entry_order[-1]) else "loop_limit"

    return TraceOverlay(
        visited_nodes=visited,
        traversed_edges=traversed,
        entry_order=entry_order,
        termination_reason=termination,
    )
