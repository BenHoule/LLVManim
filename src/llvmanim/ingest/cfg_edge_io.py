"""JSON import/export for CFG edge data."""

from __future__ import annotations

import json
from pathlib import Path

from llvmanim.transform.models import CFGEdge

_CURRENT_VERSION = 1


class CFGEdgeIOError(ValueError):
    """Raised when a CFG edge JSON file is invalid."""


def load_cfg_edges(path: str | Path) -> list[CFGEdge]:
    """Load CFG edges from a JSON file.

    Schema::

        {
          "version": 1,
          "source": "<path>",
          "functions": [
            {
              "name": "<fn>",
              "blocks": [
                { "name": "<blk>", "id": "<fn>::<blk>", "successors": ["<fn>::<tgt>", ...] }
              ]
            }
          ]
        }
    """
    text = Path(path).read_text(encoding="utf-8")
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise CFGEdgeIOError(f"Invalid JSON in CFG edge file: {exc}") from exc

    if not isinstance(data, dict):
        raise CFGEdgeIOError("CFG edge file root must be a JSON object")

    version = data.get("version")
    if version != _CURRENT_VERSION:
        raise CFGEdgeIOError(
            f"Unsupported CFG edge file version {version!r} (expected {_CURRENT_VERSION})"
        )

    functions = data.get("functions")
    if not isinstance(functions, list):
        raise CFGEdgeIOError("CFG edge file 'functions' must be a list")

    edges: list[CFGEdge] = []
    seen: set[tuple[str, str]] = set()

    for func in functions:
        if not isinstance(func, dict) or "name" not in func:
            raise CFGEdgeIOError("Each function entry must have a 'name' field")

        blocks = func.get("blocks")
        if not isinstance(blocks, list):
            raise CFGEdgeIOError(f"Function {func['name']!r}: 'blocks' must be a list")

        for block in blocks:
            if not isinstance(block, dict) or "id" not in block:
                raise CFGEdgeIOError("Each block entry must have an 'id' field")

            source_id = block["id"]
            for target_id in block.get("successors", []):
                key = (source_id, target_id)
                if key not in seen:
                    seen.add(key)
                    edges.append(CFGEdge(source=source_id, target=target_id))

    return edges


def save_cfg_edges(
    edges: list[CFGEdge],
    path: str | Path,
    *,
    source: str = "",
) -> None:
    """Serialize CFG edges to JSON format."""
    # Group edges by function.  Edge ids are "func::block".
    func_blocks: dict[str, dict[str, list[str]]] = {}
    for edge in edges:
        func_name, _, block_name = edge.source.partition("::")
        func_blocks.setdefault(func_name, {}).setdefault(block_name, [])

        _, _, tgt_block = edge.target.partition("::")
        func_blocks[func_name][block_name].append(edge.target)

        # Ensure target block entry exists (may have no outgoing edges).
        tgt_func, _, tgt_blk = edge.target.partition("::")
        func_blocks.setdefault(tgt_func, {}).setdefault(tgt_blk, [])

    # Build predecessors from the edges.
    predecessors: dict[str, list[str]] = {}
    for edge in edges:
        predecessors.setdefault(edge.target, []).append(edge.source)

    payload = {
        "version": _CURRENT_VERSION,
        "source": source,
        "functions": [
            {
                "name": fn,
                "blocks": [
                    {
                        "name": blk,
                        "id": f"{fn}::{blk}",
                        "successors": succs,
                        "predecessors": predecessors.get(f"{fn}::{blk}", []),
                    }
                    for blk, succs in blocks.items()
                ],
            }
            for fn, blocks in func_blocks.items()
        ],
    }

    Path(path).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
