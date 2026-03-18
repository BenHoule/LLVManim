"""JSON export helpers for CFG/scene graph data."""

from __future__ import annotations

import json
from pathlib import Path

from llvmanim.transform.models import SceneGraph


def _scene_graph_to_dict(graph: SceneGraph) -> dict:
    return {
        "nodes": [
            {
                "id": node.id,
                "label": node.label,
                "role": node.role,
                "animation_hint": node.animation_hint,
                "block": {
                    "id": node.block.id,
                    "name": node.block.name,
                    "function_name": node.block.function_name,
                    "terminator_opcode": node.block.terminator_opcode,
                    "indegree": node.block.indegree,
                    "outdegree": node.block.outdegree,
                    "memory_ops": [
                        {
                            "function_name": event.function_name,
                            "block_name": event.block_name,
                            "opcode": event.opcode,
                            "text": event.text,
                            "kind": event.kind,
                            "index_in_function": event.index_in_function,
                            "debug_line": event.debug_line,
                            "operands": event.operands,
                        }
                        for event in node.block.memory_ops
                    ],
                    "events": [
                        {
                            "function_name": event.function_name,
                            "block_name": event.block_name,
                            "opcode": event.opcode,
                            "text": event.text,
                            "kind": event.kind,
                            "index_in_function": event.index_in_function,
                            "debug_line": event.debug_line,
                            "operands": event.operands,
                        }
                        for event in node.block.events
                    ],
                },
            }
            for node in graph.nodes
        ],
        "edges": [
            {
                "source": edge.source,
                "target": edge.target,
                "kind": edge.kind,
            }
            for edge in graph.edges
        ],
    }


def export_scene_graph_json(graph: SceneGraph, output_path: str | Path) -> None:
    path = Path(output_path)
    payload = _scene_graph_to_dict(graph)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
