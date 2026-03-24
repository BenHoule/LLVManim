"""CFG-trace derivation: builds a static traversal path from a scene graph."""

from __future__ import annotations

from llvmanim.transform.models import SceneGraph, TraceOverlay


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
