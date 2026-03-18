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
    path = Path(output_path)

    lines: list[str] = []
    lines.append("digraph {")
    lines.append("    rankdir=TB")

    for node in graph.nodes:
        gv_name = _gv_id(node.id)
        mem_summary = ", ".join(event.opcode for event in node.block.memory_ops)

        label_lines = [
            node.id,  # keep original ID in the visible label
            f"role: {node.role}",
            f"term: {node.block.terminator_opcode}",
        ]
        if mem_summary:
            label_lines.append(f"mem: {mem_summary}")

        label = "\\n".join(label_lines)
        lines.append(f'    "{gv_name}" [label="{label}"]')

    for edge in graph.edges:
        src = _gv_id(edge.source)
        dst = _gv_id(edge.target)
        lines.append(f'    "{src}" -> "{dst}"')

    lines.append("}")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def export_cfg_png(graph: SceneGraph, output_prefix: str | Path) -> bool:
    try:
        from graphviz import Digraph
        from graphviz.backend import CalledProcessError, ExecutableNotFound
    except ImportError:
        return False

    prefix = Path(output_prefix)
    dot = Digraph(comment="LLVManim CFG")
    dot.attr(rankdir="TB")

    for node in graph.nodes:
        gv_name = _gv_id(node.id)
        mem_summary = ", ".join(event.opcode for event in node.block.memory_ops)

        label_lines = [
            node.id,  # visible label stays human-readable
            f"role: {node.role}",
            f"term: {node.block.terminator_opcode}",
        ]
        if mem_summary:
            label_lines.append(f"mem: {mem_summary}")

        dot.node(gv_name, "\n".join(label_lines))

    for edge in graph.edges:
        dot.edge(_gv_id(edge.source), _gv_id(edge.target))

    try:
        dot.render(str(prefix), format="png", cleanup=False)
    except (ExecutableNotFound, CalledProcessError):
        return False

    return True
