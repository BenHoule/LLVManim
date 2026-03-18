"""Unit tests for the execution-trace builder (transform.trace)."""

from __future__ import annotations

from llvmanim.transform.models import IREvent, ProgramEventStream
from llvmanim.transform.trace import _extract_callee, build_execution_trace


def _event(fn: str, kind: str, text: str, idx: int, opcode: str | None = None) -> IREvent:
    return IREvent(
        function_name=fn,
        block_name="entry",
        opcode=opcode or kind,
        text=text,
        kind=kind,  # type: ignore[arg-type]
        index_in_function=idx,
        debug_line=None,
    )


def test_extract_callee_handles_match_and_miss() -> None:
    assert _extract_callee("call void @foo(i32 1)") == "foo"
    assert _extract_callee("ret void") == ""


def test_build_execution_trace_descends_into_defined_callees_only() -> None:
    stream = ProgramEventStream(
        source_path="<test>",
        events=[
            _event("main", "call", "call void @ext()", 0, opcode="call"),
            _event("main", "call", "call void @llvm.memcpy.p0.p0.i64(ptr %a, ptr %b, i64 8, i1 false)", 1, opcode="call"),
            _event("main", "call", "call void @foo()", 2, opcode="call"),
            _event("main", "ret", "ret i32 0", 3, opcode="ret"),
            _event("foo", "alloca", "%x = alloca i32", 0, opcode="alloca"),
            _event("foo", "ret", "ret void", 1, opcode="ret"),
        ],
    )

    trace = build_execution_trace(stream, entry="main")

    assert trace == [
        ("push", "main", ""),
        ("push", "foo", ""),
        ("alloca", "foo", "%x = alloca i32"),
        ("pop", "foo", "ret void"),
        ("pop", "main", "ret i32 0"),
    ]


def test_build_execution_trace_honors_max_depth() -> None:
    stream = ProgramEventStream(
        source_path="<test>",
        events=[
            _event("main", "call", "call void @foo()", 0, opcode="call"),
            _event("main", "ret", "ret i32 0", 1, opcode="ret"),
            _event("foo", "ret", "ret void", 0, opcode="ret"),
        ],
    )

    # depth 0 includes only the entry frame; recursion to callees is blocked.
    trace = build_execution_trace(stream, entry="main", max_depth=0)
    assert trace == [
        ("push", "main", ""),
        ("pop", "main", "ret i32 0"),
    ]
