"""Tests for LLVM IR ingestion event extraction."""

from llvmanim.ingest.llvm_events import parse_ir_to_events, parse_module_to_events

# Minimal IR exercising every supported EventKind plus one "other" (icmp).
_ALL_KINDS_IR = """
define void @f(ptr %p) {
entry:
  %x = alloca i32
  store i32 99, ptr %x
  %v = load i32, ptr %x
  %cond = icmp eq i32 %v, 0
  br i1 %cond, label %yes, label %no
yes:
  call void @g()
  ret void
no:
  ret void
}

declare void @g()
"""


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
        assert event.kind in ["alloca", "load", "store", "call", "ret", "br", "other"]


def test_parse_ir_captures_all_supported_kinds() -> None:
    """Parser produces at least one event of every EventKind, including 'other'."""
    stream = parse_ir_to_events(_ALL_KINDS_IR)

    kinds = {event.kind for event in stream.events}
    assert "alloca" in kinds
    assert "load" in kinds
    assert "store" in kinds
    assert "call" in kinds
    assert "ret" in kinds
    assert "br" in kinds
    assert "other" in kinds  # icmp is not a supported kind and must fall through


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
