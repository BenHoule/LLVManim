"""Scene graph construction from IR event streams."""

from __future__ import annotations

import re
from collections import defaultdict
from typing import Literal

from llvmanim.transform.models import (
    ActionKind,
    AnimationCommand,
    BlockMetadata,
    CFGBlock,
    ProgramEventStream,
    SceneEdge,
    SceneGraph,
    SceneNode,
)

_CALLEE_RE = re.compile(r"call\b[^@]*@(\w+)\s*\(")


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


def _assign_roles(blocks: dict[tuple[str, str], CFGBlock], edges: list[SceneEdge]) -> None:
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


def _cfg_block_properties(block: CFGBlock) -> dict[str, object]:
    """Extract a serialisable property dictionary from a CFGBlock."""
    return {
        "block_name": block.name,
        "function_name": block.function_name,
        "role": block.role,
        "terminator_opcode": block.terminator_opcode,
        "indegree": block.indegree,
        "outdegree": block.outdegree,
        "events": block.events,
        "memory_ops": block.memory_ops,
        "idom": block.idom,
        "dom_depth": block.dom_depth,
        "is_loop_header": block.is_loop_header,
        "loop_depth": block.loop_depth,
        "loop_id": block.loop_id,
        "is_backedge_target": block.is_backedge_target,
    }


def _build_overlay_commands(graph: SceneGraph) -> list[AnimationCommand]:
    """Generate animation commands from a TraceOverlay if present."""
    overlay = graph.overlay
    if overlay is None or not overlay.entry_order:
        return []

    commands: list[AnimationCommand] = []
    prev: str | None = None
    for block_id in overlay.entry_order:
        if prev is not None:
            commands.append(AnimationCommand(
                action="traverse_edge",
                target=f"{prev}->{block_id}",
                params={"source": prev, "target": block_id},
            ))
            commands.append(AnimationCommand(
                action="exit_block",
                target=prev,
            ))
        commands.append(AnimationCommand(
            action="enter_block",
            target=block_id,
        ))
        prev = block_id

    if prev is not None:
        commands.append(AnimationCommand(
            action="exit_block",
            target=prev,
        ))

    return commands


def build_scene_graph(
    event_stream: ProgramEventStream,
    *,
    mode: Literal["cfg", "stack"] = "cfg",
    analysis_metadata: dict[str, BlockMetadata] | None = None,
    entry: str = "main",
    max_depth: int = 20,
    include_ssa: bool = False,
) -> SceneGraph:
    """Construct a scene graph from a stream of IREvents.

    Pass ``mode="stack"`` to build a stack-frame visualization instead of a
    CFG graph.  The *entry*, *max_depth*, and *include_ssa* keyword arguments
    are forwarded to the stack builder and ignored when ``mode="cfg"``.

    Edges are taken from *event_stream.cfg_edges*, which the ingest layer
    populates for all terminator types via llvmlite.

    When a *TraceOverlay* is later attached (via ``graph.overlay = ...``),
    callers can run ``_build_overlay_commands(graph)`` to populate the
    ``commands`` list; ``build_scene_graph`` itself leaves ``commands``
    empty because the overlay is typically loaded separately.
    """
    if mode == "stack":
        return _build_stack_scene_graph(
            event_stream, entry=entry, max_depth=max_depth, include_ssa=include_ssa
        )
    blocks = _group_blocks(event_stream)
    scene_edges = [
        SceneEdge(
            source=e.source,
            target=e.target,
            label=e.label,
            kind=e.kind,
        )
        for e in event_stream.cfg_edges
    ]
    _assign_roles(blocks, scene_edges)

    if analysis_metadata:
        _apply_analysis_metadata(blocks, analysis_metadata)

    graph = SceneGraph()

    for block in blocks.values():
        graph.nodes.append(
            SceneNode(
                id=block.id,
                label=block.name,
                kind="cfg_block",
                properties=_cfg_block_properties(block),
                animation_hint=_animation_hint_for_block(block),
            )
        )

    graph.edges.extend(scene_edges)
    return graph


def _slot_name_from_alloca(text: str) -> str:
    """Extract the LHS name from an alloca instruction like '%x = alloca i32'."""
    return text.split("=")[0].strip()


def _build_stack_scene_graph(
    stream: ProgramEventStream,
    entry: str = "main",
    max_depth: int = 20,
    *,
    include_ssa: bool = False,
) -> SceneGraph:
    """Build a SceneGraph representing a stack-frame visualization.

    Walks the call tree starting from *entry* (like
    ``build_execution_trace``) and produces:

    * One ``SceneNode(kind="stack_frame")`` per function call
    * One ``SceneNode(kind="stack_slot")`` per alloca encountered
    * ``SceneEdge(kind="call")`` edges for caller → callee relationships
    * An ordered ``AnimationCommand`` list driving the stack animation

    When *include_ssa* is ``True``, binop/compare/load events also generate
    animation commands with operand information in ``params``.
    """
    func_events: dict[str, list] = defaultdict(list)
    for event in stream.events:
        func_events[event.function_name].append(event)

    defined: frozenset[str] = frozenset(func_events)

    nodes: list[SceneNode] = []
    edges: list[SceneEdge] = []
    commands: list[AnimationCommand] = []

    # Track IDs to avoid duplicates when a function is called multiple times.
    frame_counter: dict[str, int] = defaultdict(int)

    def _walk(func_name: str, depth: int, caller_frame_id: str | None) -> None:
        if depth > max_depth or func_name not in defined:
            return

        # Unique frame ID for this invocation.
        frame_counter[func_name] += 1
        call_idx = frame_counter[func_name]
        frame_id = f"frame::{func_name}#{call_idx}"

        nodes.append(SceneNode(
            id=frame_id,
            label=func_name,
            kind="stack_frame",
            properties={"function_name": func_name, "call_index": call_idx},
        ))

        if caller_frame_id is not None:
            edges.append(SceneEdge(
                source=caller_frame_id,
                target=frame_id,
                kind="call",
            ))

        commands.append(AnimationCommand(
            action="push_stack_frame",
            target=frame_id,
            params={"function_name": func_name},
        ))

        for event in func_events[func_name]:
            if event.kind == "alloca":
                slot_name = _slot_name_from_alloca(event.text)
                slot_id = f"{frame_id}::{slot_name}"
                nodes.append(SceneNode(
                    id=slot_id,
                    label=slot_name,
                    kind="stack_slot",
                    properties={
                        "function_name": func_name,
                        "frame_id": frame_id,
                    },
                ))
                commands.append(AnimationCommand(
                    action="create_stack_slot",
                    target=slot_id,
                    event=event,
                    params={"slot_name": slot_name, "frame_id": frame_id},
                ))

            elif event.kind == "call":
                callee = _CALLEE_RE.search(event.text)
                callee_name = callee.group(1) if callee else ""
                if callee_name and callee_name in defined and not callee_name.startswith("llvm"):
                    _walk(callee_name, depth + 1, frame_id)

            elif include_ssa and event.kind in ("binop", "compare", "load"):
                action_map: dict[str, ActionKind] = {
                    "binop": "animate_binop",
                    "compare": "animate_compare",
                    "load": "animate_memory_read",
                }
                commands.append(AnimationCommand(
                    action=action_map[event.kind],
                    target=frame_id,
                    event=event,
                    params={"operands": list(event.operands)},
                ))

            elif event.kind == "br":
                commands.append(AnimationCommand(
                    action="highlight_branch",
                    target=frame_id,
                    event=event,
                ))

            elif event.kind == "ret":
                commands.append(AnimationCommand(
                    action="pop_stack_frame",
                    target=frame_id,
                    event=event,
                    params={"function_name": func_name},
                ))
                return

    _walk(entry, 0, None)

    return SceneGraph(nodes=nodes, edges=edges, commands=commands)
