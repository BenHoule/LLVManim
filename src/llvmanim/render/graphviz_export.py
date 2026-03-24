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

    When *graph.overlay* is set, visited nodes and traversed edges are
    highlighted while unvisited elements are dimmed.
    """
    path = Path(output_path)
    overlay = graph.overlay
    visited: set[str] = set(overlay.visited_nodes) if overlay else set()
    traversed: set[tuple[str, str]] = set(overlay.traversed_edges) if overlay else set()

    lines: list[str] = []
    lines.append("digraph {")
    lines.append("    rankdir=TB")

    for node in graph.nodes:
        props = node.properties
        memory_ops = props.get("memory_ops", [])
        mem_summary = ", ".join(event.opcode for event in memory_ops)

        label_lines = [
            node.id,
            f"role: {props.get('role', '')}",
            f"term: {props.get('terminator_opcode', '')}",
        ]
        if mem_summary:
            label_lines.append(f"mem: {mem_summary}")

        label = "\\n".join(label_lines)

        attrs = f'label="{label}"'
        if overlay:
            if node.id in visited:
                attrs += ', style=filled, fillcolor="#d4edda"'
            else:
                attrs += ', style=filled, fillcolor="#e0e0e0", fontcolor="#888888"'
        lines.append(f'    "{node.id}" [{attrs}]')

    for edge in graph.edges:
        edge_attrs = ""
        if overlay:
            if (edge.source, edge.target) in traversed:
                edge_attrs = ' [color="#0056b3", penwidth=2.0'
            else:
                edge_attrs = ' [color="#cccccc", style=dashed'
            if edge.label:
                edge_attrs += f', label="{edge.label}"'
            edge_attrs += "]"
        elif edge.label:
            edge_attrs = f' [label="{edge.label}"]'
        lines.append(f'    "{edge.source}" -> "{edge.target}"{edge_attrs}')

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

    overlay = graph.overlay
    visited: set[str] = set(overlay.visited_nodes) if overlay else set()
    traversed: set[tuple[str, str]] = set(overlay.traversed_edges) if overlay else set()

    for node in graph.nodes:
        props = node.properties
        memory_ops = props.get("memory_ops", [])
        mem_summary = ", ".join(event.opcode for event in memory_ops)

        label_lines = [
            node.id,  # visible label stays human-readable
            f"role: {props.get('role', '')}",
            f"term: {props.get('terminator_opcode', '')}",
        ]
        if mem_summary:
            label_lines.append(f"mem: {mem_summary}")

        node_attrs: dict[str, str] = {}
        if overlay:
            if node.id in visited:
                node_attrs = {"style": "filled", "fillcolor": "#d4edda"}
            else:
                node_attrs = {"style": "filled", "fillcolor": "#e0e0e0", "fontcolor": "#888888"}
        dot.node(_gv_id(node.id), "\n".join(label_lines), **node_attrs)

    for edge in graph.edges:
        edge_attrs: dict[str, str] = {}
        if overlay:
            if (edge.source, edge.target) in traversed:
                edge_attrs = {"color": "#0056b3", "penwidth": "2.0"}
            else:
                edge_attrs = {"color": "#cccccc", "style": "dashed"}
        if edge.label:
            edge_attrs["label"] = edge.label
        dot.edge(_gv_id(edge.source), _gv_id(edge.target), **edge_attrs)

    try:
        dot.render(str(prefix), format="png", cleanup=False)
    except (ExecutableNotFound, CalledProcessError):
        return False

    return True
