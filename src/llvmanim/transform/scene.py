"""Scene graph construction from IR event streams."""

import re
from collections import defaultdict

from llvmanim.transform.models import (
    BlockMetadata,
    CFGBlock,
    CFGEdge,
    ProgramEventStream,
    SceneGraph,
    SceneNode,
)


def _make_block_id(function_name: str, block_name: str) -> str:
    """Create a unique internal block ID."""
    return f"{function_name}::{block_name}"


def _animation_hint_for_block(block: CFGBlock) -> str:
    """Return a string animation hint for the given block based on its role."""
    if block.is_loop_header:
        return "pulse_loop_header"
    if block.role == "entry":
        return "fade_in_and_focus"
    if block.role == "branch":
        return "pulse_and_split"
    if block.role == "merge":
        return "converge"
    if block.role == "exit":
        return "fade_out"
    if block.memory_ops:
        return "show_memory_activity"
    return "highlight_block"


def _group_blocks(event_stream: ProgramEventStream) -> dict[tuple[str, str], CFGBlock]:
    """Group events by (function_name, block_name) into CFGBlock objects."""
    grouped: dict[tuple[str, str], CFGBlock] = {}

    for event in event_stream.events:
        block_name = event.block_name or "<unnamed>"
        key = (event.function_name, block_name)

        if key not in grouped:
            grouped[key] = CFGBlock(
                id=_make_block_id(event.function_name, block_name),
                name=block_name,
                function_name=event.function_name,
            )

        grouped[key].events.append(event)

    for block in grouped.values():
        if block.events:
            block.terminator_opcode = block.events[-1].opcode
            block.memory_ops = [e for e in block.events if e.kind in {"alloca", "load", "store"}]

    return grouped


def _extract_branch_targets_from_text(instr_text: str) -> list[str]:
    """
    Examples:
      br i1 %cond, label %yes, label %no
      br label %while.cond
    """
    return re.findall(r"label\s+%([\w.\-]+)", instr_text)


def _extract_edges(blocks: dict[tuple[str, str], CFGBlock]) -> list[CFGEdge]:
    """Derive control-flow edges from branch terminators within each function."""
    edges: list[CFGEdge] = []
    seen: set[tuple[str, str]] = set()

    per_function: dict[str, list[CFGBlock]] = defaultdict(list)
    for block in blocks.values():
        per_function[block.function_name].append(block)

    for _function_name, function_blocks in per_function.items():
        name_to_id = {b.name: b.id for b in function_blocks}

        for block in function_blocks:
            if not block.events:
                continue

            terminator = block.events[-1]
            if terminator.opcode != "br":
                continue

            targets = _extract_branch_targets_from_text(terminator.text)
            for target_name in targets:
                if target_name in name_to_id:
                    edge_key = (block.id, name_to_id[target_name])
                    if edge_key in seen:
                        continue
                    seen.add(edge_key)
                    edges.append(CFGEdge(source=edge_key[0], target=edge_key[1]))

    return edges


def _assign_roles(blocks: dict[tuple[str, str], CFGBlock], edges: list[CFGEdge]) -> None:
    """Set each block's role (entry/branch/merge/exit/linear) from edge topology."""
    indegree: dict[str, int] = defaultdict(int)
    outdegree: dict[str, int] = defaultdict(int)

    for edge in edges:
        outdegree[edge.source] += 1
        indegree[edge.target] += 1

    for block in blocks.values():
        block.indegree = indegree[block.id]
        block.outdegree = outdegree[block.id]

        if block.outdegree > 1:
            block.role = "branch"
        elif block.indegree == 0:
            block.role = "entry"
        elif block.terminator_opcode == "ret":
            block.role = "exit"
        elif block.indegree > 1:
            block.role = "merge"
        else:
            block.role = "linear"


def _apply_analysis_metadata(
    blocks: dict[tuple[str, str], CFGBlock],
    metadata: dict[str, BlockMetadata],
) -> None:
    """Copy analysis metadata onto matching blocks."""
    for block in blocks.values():
        meta = metadata.get(block.id)
        if meta is None:
            continue
        block.idom = meta.idom
        block.dom_depth = meta.dom_depth
        block.is_loop_header = meta.is_loop_header
        block.loop_depth = meta.loop_depth
        block.loop_id = meta.loop_id
        block.is_backedge_target = meta.is_backedge_target


def build_scene_graph(
    event_stream: ProgramEventStream,
    *,
    analysis_metadata: dict[str, BlockMetadata] | None = None,
) -> SceneGraph:
    """Construct a scene graph from a stream of IREvents."""
    blocks = _group_blocks(event_stream)
    edges = event_stream.cfg_edges if event_stream.cfg_edges else _extract_edges(blocks)
    _assign_roles(blocks, edges)

    if analysis_metadata:
        _apply_analysis_metadata(blocks, analysis_metadata)

    graph = SceneGraph()

    for block in blocks.values():
        graph.nodes.append(
            SceneNode(
                id=block.id,
                label=block.name,
                role=block.role,
                block=block,
                animation_hint=_animation_hint_for_block(block),
            )
        )

    graph.edges.extend(edges)
    return graph
