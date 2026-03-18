"""Unit tests for pure helper functions in rich_stack_scene.py."""

from __future__ import annotations

from llvmanim.present.rich_stack_scene import (
    _call_site_idx,
    _clean_ir_line,
    _extract_callee,
    _find_line_idx,
    build_execution_trace,
    build_ir_registry,
)
from llvmanim.transform.models import IREvent, ProgramEventStream


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


def test_clean_ir_line_removes_noise_tokens() -> None:
    raw = "  call noalias noundef dso_local ptr @f(ptr %x), align 8, !dbg !12 #3 ; trailing comment"
    cleaned = _clean_ir_line(raw)

    assert "noalias" not in cleaned
    assert "noundef" not in cleaned
    assert "dso_local" not in cleaned
    assert "!dbg" not in cleaned
    assert "#3" not in cleaned
    assert "align 8" not in cleaned
    assert ";" not in cleaned
    assert "@f" in cleaned


def test_build_ir_registry_collects_functions_and_skips_intrinsics(tmp_path) -> None:
    ir_file = tmp_path / "demo.ll"
    ir_file.write_text(
        """
define i32 @main() #0 {
entry:
  call void @llvm.dbg.value(metadata i32 0, metadata !12, metadata !DIExpression()), !dbg !17
  %x = alloca i32, align 4
  ret i32 0
}

define void @helper() {
entry:
  ret void
}
""".strip()
    )

    registry = build_ir_registry(ir_file.as_posix())

    assert set(registry) == {"main", "helper"}
    assert any(line.startswith("define i32 @main") for line in registry["main"])
    assert all("@llvm." not in line for line in registry["main"])
    assert registry["main"][-1] == "}"
    assert registry["helper"][-1] == "}"


def test_extract_callee_handles_match_and_miss() -> None:
    assert _extract_callee("call void @foo(i32 1)") == "foo"
    assert _extract_callee("ret void") == ""


def test_find_line_idx_and_call_site_idx() -> None:
    lines = [
        "define i32 @main()",
        "%x = alloca i32",
        "call i32 @foo(i32 1)",
        "ret i32 0",
    ]

    assert _find_line_idx(lines, "  %x = alloca i32, align 4") == 1
    assert _find_line_idx(lines, "call i32 @foo(i32 1)") == 2
    assert _find_line_idx(lines, "does not exist") == 0
    assert _call_site_idx(lines, "foo") == 2
    assert _call_site_idx(lines, "bar") == 0


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
