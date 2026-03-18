"""Graphviz export helpers for CFG visualization."""

from __future__ import annotations

import re
from pathlib import Path

from llvmanim.transform.models import SceneGraph


def _gv_id(node_id: str) -> str:
    """
    Convert internal node IDs like:
        main::while.cond
    into Graphviz-safe IDs like:
        main__while_cond
    """
    return re.sub(r"[^A-Za-z0-9_]", "_", node_id)


def export_cfg_dot(graph: SceneGraph, output_path: str | Path) -> None:
    """Write a Graphviz DOT file representing the CFG of *graph*.

    Each node shows its block ID, role, terminator opcode, and any memory ops.
    Edges represent control-flow branches extracted by the transform layer.
    """
    path = Path(output_path)

    lines: list[str] = []
    lines.append("digraph {")
    lines.append("    rankdir=TB")

    for node in graph.nodes:
        mem_summary = ", ".join(event.opcode for event in node.block.memory_ops)

        label_lines = [
            node.id,
            f"role: {node.role}",
            f"term: {node.block.terminator_opcode}",
        ]
        if mem_summary:
            label_lines.append(f"mem: {mem_summary}")

        label = "\\n".join(label_lines)
        lines.append(f'    "{node.id}" [label="{label}"]')

    for edge in graph.edges:
        lines.append(f'    "{edge.source}" -> "{edge.target}"')

    lines.append("}")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def export_cfg_png(graph: SceneGraph, output_prefix: str | Path) -> bool:
    """Render the CFG as a PNG via the *graphviz* Python package.

    Returns True on success and False if the graphviz package is not installed
    or the Graphviz binaries are unavailable.  The caller should print a
    diagnostic in the False case.
    """
    try:
        from graphviz import Digraph
        from graphviz.backend import CalledProcessError, ExecutableNotFound
    except ImportError:
        return False

    prefix = Path(output_prefix)
    dot = Digraph(comment="LLVManim CFG")
    dot.attr(rankdir="TB")

    for node in graph.nodes:
        mem_summary = ", ".join(event.opcode for event in node.block.memory_ops)

        label_lines = [
            node.id,  # visible label stays human-readable
            f"role: {node.role}",
            f"term: {node.block.terminator_opcode}",
        ]
        if mem_summary:
            label_lines.append(f"mem: {mem_summary}")

        dot.node(_gv_id(node.id), "\n".join(label_lines))

    for edge in graph.edges:
        dot.edge(_gv_id(edge.source), _gv_id(edge.target))

    try:
        dot.render(str(prefix), format="png", cleanup=False)
    except (ExecutableNotFound, CalledProcessError):
        return False

    return True
