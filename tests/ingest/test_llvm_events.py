"""Tests for LLVM IR ingestion event extraction."""

import pytest

from llvmanim.ingest.llvm_events import (
    _kind_from_opcode,
    parse_ir_to_events,
    parse_module_to_events,
)


def test_parse_module_extracts_events_and_path() -> None:
    """parse_module_to_events reads the file and records source_path correctly."""
    stream = parse_module_to_events("tests/ingest/testdata/double.ll")

    assert stream.source_path == "tests/ingest/testdata/double.ll"
    assert len(stream.events) > 0


def test_events_have_function_block_opcode_and_kind() -> None:
    """Every event carries the function name, block name, opcode, and kind set by the IR."""
    stream = parse_ir_to_events("""
        define i32 @compute() {
        entry:
          %x = alloca i32
          store i32 7, ptr %x
          %v = load i32, ptr %x
          ret i32 %v
        }
    """)

    for event in stream.events:
        assert event.function_name == "compute"
        assert event.block_name == "entry"
        assert event.opcode != ""
        assert event.kind in [
            "alloca",
            "load",
            "store",
            "binop",
            "compare",
            "call",
            "ret",
            "br",
            "other",
        ]


def test_parse_ir_captures_all_supported_kinds(all_kinds_ir: str) -> None:
    """Parser produces at least one event of every EventKind, including 'other'."""
    stream = parse_ir_to_events(all_kinds_ir)

    kinds = {event.kind for event in stream.events}
    assert "alloca" in kinds
    assert "load" in kinds
    assert "store" in kinds
    assert "binop" in kinds
    assert "compare" in kinds
    assert "call" in kinds
    assert "ret" in kinds
    assert "br" in kinds
    assert "other" in kinds  # zext is not a supported kind and must fall through


def test_kind_from_opcode_add_returns_binop() -> None:
    """Classifier should map arithmetic opcodes like add to binop."""
    assert _kind_from_opcode("add") == "binop"


def test_kind_from_opcode_icmp_returns_compare() -> None:
    """Classifier should map compare opcodes like icmp to compare."""
    assert _kind_from_opcode("icmp") == "compare"


def test_events_have_sequential_indices() -> None:
    """Parser assigns 0-based monotonic indices per function."""
    stream = parse_ir_to_events("""
        define void @f() {
        entry:
          %x = alloca i32
          store i32 1, ptr %x
          %v = load i32, ptr %x
          ret void
        }
    """)

    indices = [e.index_in_function for e in stream.events if e.function_name == "f"]
    assert indices == list(range(len(indices)))


def test_kind_from_opcode_none_returns_other() -> None:
    """Classifier should map None opcode to the fallback 'other' kind."""
    assert _kind_from_opcode(None) == "other"


def test_parse_module_missing_file_raises_file_not_found() -> None:
    """parse_module_to_events should raise FileNotFoundError for missing source files."""
    with pytest.raises(FileNotFoundError):
        parse_module_to_events("tests/ingest/testdata/does_not_exist.ll")


def test_parse_ir_invalid_input_raises() -> None:
    """parse_ir_to_events should surface llvmlite parse failures on invalid IR text."""
    with pytest.raises(RuntimeError):
        parse_ir_to_events("this is not valid llvm ir")


# ── Typed CFG edge extraction ───────────────────────────────────────────────────


def test_cfg_edges_conditional_branch() -> None:
    """A conditional br produces two typed CFGEdge entries."""
    stream = parse_ir_to_events("""
        define void @f() {
        entry:
          %cond = icmp eq i32 0, 0
          br i1 %cond, label %yes, label %no
        yes:
          ret void
        no:
          ret void
        }
    """)
    edge_pairs = {(e.source, e.target) for e in stream.cfg_edges}
    assert ("f::entry", "f::no") in edge_pairs
    assert ("f::entry", "f::yes") in edge_pairs
    assert len(stream.cfg_edges) == 2


def test_cfg_edges_unconditional_branch() -> None:
    """An unconditional br produces one typed CFGEdge."""
    stream = parse_ir_to_events("""
        define void @f() {
        entry:
          br label %next
        next:
          ret void
        }
    """)
    assert len(stream.cfg_edges) == 1
    assert stream.cfg_edges[0].source == "f::entry"
    assert stream.cfg_edges[0].target == "f::next"


def test_cfg_edges_dedup_same_target() -> None:
    """A branch that names the same target twice produces only one edge."""
    stream = parse_ir_to_events("""
        define void @f() {
        entry:
          %cond = icmp eq i32 0, 0
          br i1 %cond, label %done, label %done
        done:
          ret void
        }
    """)
    assert len(stream.cfg_edges) == 1
    assert stream.cfg_edges[0].target == "f::done"


def test_cfg_edges_switch() -> None:
    """A switch instruction produces edges to the default and each case target."""
    stream = parse_ir_to_events("""
        define i32 @test(i32 %x) {
        entry:
          switch i32 %x, label %default [
            i32 0, label %case0
            i32 1, label %case1
          ]
        case0:
          ret i32 10
        case1:
          ret i32 20
        default:
          ret i32 -1
        }
    """)
    edge_targets = {e.target for e in stream.cfg_edges}
    assert edge_targets == {"test::default", "test::case0", "test::case1"}
    assert all(e.source == "test::entry" for e in stream.cfg_edges)


def test_cfg_edges_ret_produces_none() -> None:
    """A ret terminator produces no CFG edges."""
    stream = parse_ir_to_events("""
        define void @f() {
        entry:
          ret void
        }
    """)
    assert stream.cfg_edges == []


def test_cfg_edges_multi_function() -> None:
    """Edges are scoped per function and use function::block id format."""
    stream = parse_ir_to_events("""
        define void @a() {
        entry:
          br label %next
        next:
          ret void
        }
        define void @b() {
        entry:
          br label %next
        next:
          ret void
        }
    """)
    assert len(stream.cfg_edges) == 2
    sources = {e.source for e in stream.cfg_edges}
    assert sources == {"a::entry", "b::entry"}
