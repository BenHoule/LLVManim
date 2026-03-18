"""Core data models shared by ingestion and transformation layers."""

from dataclasses import dataclass, field
from typing import Literal

EventKind = Literal["alloca", "load", "store", "call", "ret", "br", "other"]
BlockRole = Literal["entry", "linear", "branch", "merge", "exit"]


@dataclass(slots=True)
class IREvent:
    """Normalize LLVM IR instructions into a common event format for transformation."""

    function_name: str
    block_name: str
    opcode: str
    text: str
    kind: EventKind
    index_in_function: int
    debug_line: int | None
    operands: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ProgramEventStream:
    """Ordered event stream for one LLVM module."""

    source_path: str
    events: list[IREvent] = field(default_factory=list)


@dataclass(slots=True)
class CFGBlock:
    """A basic block grouped from IR events."""

    id: str
    name: str
    function_name: str
    events: list[IREvent] = field(default_factory=list)
    terminator_opcode: str | None = None
    role: BlockRole = "linear"
    indegree: int = 0
    outdegree: int = 0
    memory_ops: list[IREvent] = field(default_factory=list)


@dataclass(slots=True)
class CFGEdge:
    """A control-flow edge between two blocks."""

    source: str
    target: str
    kind: str = "control_flow"


@dataclass(slots=True)
class SceneNode:
    """A node in the scene graph representing one CFG block."""

    id: str
    label: str
    role: BlockRole
    block: CFGBlock
    animation_hint: str


@dataclass(slots=True)
class SceneGraph:
    """Scene graph for LLVM IR visualization."""

    nodes: list[SceneNode] = field(default_factory=list)
    edges: list[CFGEdge] = field(default_factory=list)
