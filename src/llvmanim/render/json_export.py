"""JSON export helpers for CFG/scene graph data."""

from __future__ import annotations

import json
from pathlib import Path

from llvmanim.transform.models import IREvent, SceneGraph


def _scene_graph_to_dict(graph: SceneGraph) -> dict:
    def _event_to_dict(event: IREvent) -> dict:
        return {
            "function_name": event.function_name,
            "block_name": event.block_name,
            "opcode": event.opcode,
            "text": event.text,
            "kind": event.kind,
            "index_in_function": event.index_in_function,
            "debug_line": event.debug_line,
            "operands": event.operands,
        }

    nodes = []
    for node in graph.nodes:
        props = node.properties
        node_dict: dict = {
            "id": node.id,
            "label": node.label,
            "kind": node.kind,
            "animation_hint": node.animation_hint,
        }
        if node.kind == "cfg_block":
            node_dict["block"] = {
                "id": node.id,
                "name": props.get("block_name", ""),
                "function_name": props.get("function_name", ""),
                "terminator_opcode": props.get("terminator_opcode"),
                "indegree": props.get("indegree", 0),
                "outdegree": props.get("outdegree", 0),
                "memory_ops": [_event_to_dict(e) for e in props.get("memory_ops", [])],
                "events": [_event_to_dict(e) for e in props.get("events", [])],
            }
        else:
            node_dict["properties"] = {
                k: v for k, v in props.items()
                if not callable(v) and not hasattr(v, "__dataclass_fields__")
            }
        nodes.append(node_dict)

    return {
        "nodes": nodes,
        "edges": [
            {
                "source": edge.source,
                "target": edge.target,
                "kind": edge.kind,
                "label": edge.label,
            }
            for edge in graph.edges
        ],
        "commands": [
            {
                "action": cmd.action,
                "target": cmd.target,
            }
            for cmd in graph.commands
        ],
    }


def export_scene_graph_json(graph: SceneGraph, output_path: str | Path) -> None:
    path = Path(output_path)
    payload = _scene_graph_to_dict(graph)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
