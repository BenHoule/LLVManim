"""Ingestion of LLVM IR text into a structured ProgramEventStream via llvmlite."""

from pathlib import Path

import llvmlite.binding as llvm

from llvmanim.transform.models import EventKind, IREvent, ProgramEventStream

_OPCODE_KINDS: dict[str, EventKind] = {
    "alloca": "alloca",
    "load": "load",
    "store": "store",
    "call": "call",
    "ret": "ret",
    "br": "br",
}


def _kind_from_opcode(opcode: str | None) -> EventKind:
    """Classify an LLVM opcode into an event kind."""
    if opcode is None:
        return "other"
    return _OPCODE_KINDS.get(opcode, "other")


def parse_ir_to_events(llvm_ir: str, source_path: str = "<in-memory>") -> ProgramEventStream:
    """Parse LLVM IR text into a deterministic event stream.

    Extracts function, block, and instruction structure from LLVM IR.
    Only supports a well-defined subset of instructions; others are
    classified as "other" and can be skipped during rendering."""
    module = llvm.parse_assembly(llvm_ir)
    module.verify()  # Ensures module is well-formed

    stream = ProgramEventStream(source_path=source_path)
    per_func_index: dict[str, int] = {}

    for func in module.functions:
        func_name = func.name or "<anon_fn>"
        per_func_index.setdefault(func_name, 0)

        for block in func.blocks:
            block_name = block.name

            for instr in block.instructions:
                opcode = instr.opcode

                event = IREvent(
                    function_name=func_name,
                    block_name=block_name,
                    opcode=opcode or "unknown",
                    text=str(instr).strip(),
                    kind=_kind_from_opcode(opcode),
                    index_in_function=per_func_index[func_name],
                    debug_line=None,
                    operands=[str(op) for op in instr.operands],
                )
                stream.events.append(event)
                per_func_index[func_name] += 1

    return stream


def parse_module_to_events(source_path: str) -> ProgramEventStream:
    """Parse an LLVM .ll file into a deterministic event stream.

    Extracts function, block, and instruction structure from LLVM IR.
    Only supports a well-defined subset of instructions; others are
    classified as "other" and can be skipped during rendering.

    This is a wrapper around parse_ir_to_events that reads the IR from a file path."""
    path = Path(source_path)
    return parse_ir_to_events(path.read_text(encoding="utf-8"), path.as_posix())
