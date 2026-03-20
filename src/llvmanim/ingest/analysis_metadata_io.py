"""JSON import/export for dominator-tree and loop-structure metadata."""

from __future__ import annotations

import json
from pathlib import Path

from llvmanim.transform.models import BlockMetadata

_CURRENT_VERSION = 1


class AnalysisMetadataIOError(ValueError):
    """Raised when an analysis metadata JSON file is invalid."""


def load_analysis_metadata(path: str | Path) -> dict[str, BlockMetadata]:
    """Load per-block analysis metadata from a JSON file.

    Returns a mapping of block id (``"func::block"``) to metadata.

    Schema::

        {
          "version": 1,
          "source": "<path>",
          "functions": [
            {
              "name": "main",
              "blocks": [
                {
                  "id": "main::entry",
                  "idom": null,
                  "dom_depth": 0,
                  "is_loop_header": false,
                  "loop_depth": 0,
                  "loop_id": null,
                  "is_backedge_target": false
                }
              ]
            }
          ]
        }

    All per-block fields except ``id`` are optional; missing fields use defaults.
    The ``functions`` list may contain domtree-only or loop-only entries.
    """
    text = Path(path).read_text(encoding="utf-8")
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise AnalysisMetadataIOError(f"Invalid JSON in analysis metadata file: {exc}") from exc

    if not isinstance(data, dict):
        raise AnalysisMetadataIOError("Analysis metadata root must be a JSON object")

    version = data.get("version")
    if version != _CURRENT_VERSION:
        raise AnalysisMetadataIOError(
            f"Unsupported analysis metadata version {version!r} (expected {_CURRENT_VERSION})"
        )

    functions = data.get("functions")
    if not isinstance(functions, list):
        raise AnalysisMetadataIOError("'functions' must be a list")

    result: dict[str, BlockMetadata] = {}

    for func in functions:
        if not isinstance(func, dict) or "name" not in func:
            raise AnalysisMetadataIOError("Each function entry must have a 'name' field")

        blocks = func.get("blocks")
        if not isinstance(blocks, list):
            raise AnalysisMetadataIOError(f"Function {func['name']!r}: 'blocks' must be a list")

        for block in blocks:
            if not isinstance(block, dict) or "id" not in block:
                raise AnalysisMetadataIOError("Each block entry must have an 'id' field")

            block_id = block["id"]
            result[block_id] = BlockMetadata(
                idom=block.get("idom"),
                dom_depth=block.get("dom_depth", 0),
                is_loop_header=block.get("is_loop_header", False),
                loop_depth=block.get("loop_depth", 0),
                loop_id=block.get("loop_id"),
                is_backedge_target=block.get("is_backedge_target", False),
            )

    return result


def save_analysis_metadata(
    metadata: dict[str, BlockMetadata],
    path: str | Path,
    *,
    source: str = "",
) -> None:
    """Serialize per-block analysis metadata to JSON format."""
    func_blocks: dict[str, list[dict[str, object]]] = {}

    for block_id, meta in metadata.items():
        func_name, _, block_name = block_id.partition("::")
        entry: dict[str, object] = {"id": block_id, "name": block_name}
        if meta.idom is not None:
            entry["idom"] = meta.idom
        if meta.dom_depth != 0:
            entry["dom_depth"] = meta.dom_depth
        if meta.is_loop_header:
            entry["is_loop_header"] = True
        if meta.loop_depth != 0:
            entry["loop_depth"] = meta.loop_depth
        if meta.loop_id is not None:
            entry["loop_id"] = meta.loop_id
        if meta.is_backedge_target:
            entry["is_backedge_target"] = True
        func_blocks.setdefault(func_name, []).append(entry)

    payload = {
        "version": _CURRENT_VERSION,
        "source": source,
        "functions": [{"name": fn, "blocks": blocks} for fn, blocks in func_blocks.items()],
    }

    Path(path).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
