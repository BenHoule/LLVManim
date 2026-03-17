"""Core data models shared by ingestion and transformation layers."""

from dataclasses import dataclass, field
from typing import Literal

EventKind = Literal["alloca", "load", "store", "call", "ret", "br", "other"]


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
