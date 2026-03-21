"""Ingestion of LLVM IR text into a structured ProgramEventStream via llvmlite."""

from pathlib import Path

import llvmlite.binding as llvm

from llvmanim.ingest.display_lines import build_display_lines
from llvmanim.transform.models import CFGEdge, EventKind, IREvent, ProgramEventStream

_BASIC_BLOCK_VALUE_KIND = 1  # llvmlite ValueKind.basic_block

_TERMINATOR_OPCODES: frozenset[str] = frozenset(
    {"br", "switch", "invoke", "indirectbr", "callbr"}
)

_OPCODE_KINDS: dict[str, EventKind] = {
    "alloca": "alloca",
    "load": "load",
    "store": "store",
    "call": "call",
    "ret": "ret",
    "br": "br",
}

_BINARY_OPCODES: frozenset[str] = frozenset(
    {
        "add",
        "sub",
        "mul",
        "udiv",
        "sdiv",
        "urem",
        "srem",
        "shl",
        "lshr",
        "ashr",
        "and",
        "or",
        "xor",
        "fadd",
        "fsub",
        "fmul",
        "fdiv",
        "frem",
    }
)

_COMPARE_OPCODES: frozenset[str] = frozenset({"icmp", "fcmp"})


def _kind_from_opcode(opcode: str | None) -> EventKind:
    """Classify an LLVM opcode into an event kind."""
    if opcode is None:
        return "other"
    if opcode in _BINARY_OPCODES:
        return "binop"
    if opcode in _COMPARE_OPCODES:
        return "compare"
    return _OPCODE_KINDS.get(opcode, "other")


def parse_ir_to_events(llvm_ir: str, source_path: str = "<in-memory>") -> ProgramEventStream:
    """Parse LLVM IR text into a deterministic event stream.

    Extracts function, block, and instruction structure from LLVM IR.
    Only supports a well-defined subset of instructions; others are
    classified as "other" and can be skipped during rendering."""
    module = llvm.parse_assembly(llvm_ir)
    module.verify()  # Ensures module is well-formed

    stream = ProgramEventStream(source_path=source_path)
    stream.display_lines = build_display_lines(llvm_ir)
    per_func_index: dict[str, int] = {}
    edge_seen: set[tuple[str, str]] = set()

    for func in module.functions:
        func_name = func.name or "<anon_fn>"
        per_func_index.setdefault(func_name, 0)

        for block in func.blocks:
            block_name = block.name
            instructions = list(block.instructions)

            for instr in instructions:
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

            # Extract typed CFG edges from the terminator instruction.
            if instructions:
                term = instructions[-1]
                if term.opcode in _TERMINATOR_OPCODES:
                    source_id = f"{func_name}::{block_name}"
                    bb_targets = [
                        op for op in term.operands
                        if op.value_kind == _BASIC_BLOCK_VALUE_KIND
                    ]
                    # Conditional br: llvmlite operand order is [false, true].
                    is_cond_br = term.opcode == "br" and len(bb_targets) == 2
                    for idx, op in enumerate(bb_targets):
                        target_id = f"{func_name}::{op.name}"
                        key = (source_id, target_id)
                        if key not in edge_seen:
                            edge_seen.add(key)
                            label = ""
                            if is_cond_br:
                                label = "F" if idx == 0 else "T"
                            stream.cfg_edges.append(
                                CFGEdge(
                                    source=source_id,
                                    target=target_id,
                                    label=label,
                                )
                            )

    return stream


def parse_module_to_events(source_path: str) -> ProgramEventStream:
    """Parse an LLVM .ll file into a deterministic event stream.

    Extracts function, block, and instruction structure from LLVM IR.
    Only supports a well-defined subset of instructions; others are
    classified as "other" and can be skipped during rendering.

    This is a wrapper around parse_ir_to_events that reads the IR from a file path."""
    path = Path(source_path)
    return parse_ir_to_events(path.read_text(encoding="utf-8"), path.as_posix())
