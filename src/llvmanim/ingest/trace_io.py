"""JSON import/export for runtime path trace data."""

from __future__ import annotations

import json
from pathlib import Path

from llvmanim.transform.models import TraceOverlay

_CURRENT_VERSION = 1


class TraceIOError(ValueError):
    """Raised when a trace JSON file is invalid."""


def load_trace(path: str | Path) -> TraceOverlay:
    """Load a runtime path trace from a JSON file.

    Schema::

        {
          "version": 1,
          "source": "<path>",
          "entry_order": ["main::entry", "main::while.cond", ...],
          "visited_nodes": ["main::entry", "main::while.cond", ...],
          "traversed_edges": [["main::entry", "main::while.cond"], ...],
          "termination_reason": "ret"
        }

    ``entry_order`` is required (the ordered sequence of block visits).
    ``visited_nodes`` and ``traversed_edges`` are optional — when absent they
    are derived from ``entry_order``.
    """
    text = Path(path).read_text(encoding="utf-8")
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise TraceIOError(f"Invalid JSON in trace file: {exc}") from exc

    if not isinstance(data, dict):
        raise TraceIOError("Trace file root must be a JSON object")

    version = data.get("version")
    if version != _CURRENT_VERSION:
        raise TraceIOError(
            f"Unsupported trace file version {version!r} (expected {_CURRENT_VERSION})"
        )

    entry_order = data.get("entry_order")
    if not isinstance(entry_order, list):
        raise TraceIOError("'entry_order' must be a list of block IDs")

    # Derive visited_nodes from entry_order if not explicitly provided.
    visited_nodes: list[str]
    if "visited_nodes" in data:
        if not isinstance(data["visited_nodes"], list):
            raise TraceIOError("'visited_nodes' must be a list of block IDs")
        visited_nodes = data["visited_nodes"]
    else:
        visited_nodes = list(dict.fromkeys(entry_order))

    # Derive traversed_edges from consecutive entry_order pairs if not provided.
    traversed_edges: list[tuple[str, str]]
    if "traversed_edges" in data:
        raw_edges = data["traversed_edges"]
        if not isinstance(raw_edges, list):
            raise TraceIOError("'traversed_edges' must be a list of [source, target] pairs")
        traversed_edges = []
        seen: set[tuple[str, str]] = set()
        for pair in raw_edges:
            if not isinstance(pair, list) or len(pair) != 2:
                raise TraceIOError("Each traversed edge must be a [source, target] pair")
            key = (pair[0], pair[1])
            if key not in seen:
                seen.add(key)
                traversed_edges.append(key)
    else:
        seen_edges: set[tuple[str, str]] = set()
        traversed_edges = []
        for i in range(len(entry_order) - 1):
            key = (entry_order[i], entry_order[i + 1])
            if key not in seen_edges:
                seen_edges.add(key)
                traversed_edges.append(key)

    termination_reason = data.get("termination_reason", "")
    if not isinstance(termination_reason, str):
        raise TraceIOError("'termination_reason' must be a string")

    return TraceOverlay(
        visited_nodes=visited_nodes,
        traversed_edges=traversed_edges,
        entry_order=entry_order,
        termination_reason=termination_reason,
    )


def save_trace(
    overlay: TraceOverlay,
    path: str | Path,
    *,
    source: str = "",
) -> None:
    """Serialize a trace overlay to JSON format."""
    payload = {
        "version": _CURRENT_VERSION,
        "source": source,
        "entry_order": overlay.entry_order,
        "visited_nodes": overlay.visited_nodes,
        "traversed_edges": [list(edge) for edge in overlay.traversed_edges],
        "termination_reason": overlay.termination_reason,
    }

    Path(path).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
