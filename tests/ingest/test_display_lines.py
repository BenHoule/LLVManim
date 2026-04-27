"""Tests for the display_lines module -- IR text cleaning and display-line extraction."""

from llvmanim.ingest.display_lines import build_display_lines, clean_ir_line

# ---------------------------------------------------------------------------
# clean_ir_line
# ---------------------------------------------------------------------------


def test_clean_ir_line_removes_noise_tokens() -> None:
    raw = "  call noalias noundef dso_local ptr @f(ptr %x), align 8, !dbg !12 #3 ; trailing comment"
    cleaned = clean_ir_line(raw)

    assert "noalias" not in cleaned
    assert "noundef" not in cleaned
    assert "dso_local" not in cleaned
    assert "!dbg" not in cleaned
    assert "#3" not in cleaned
    assert "align 8" not in cleaned
    assert ";" not in cleaned
    assert "@f" in cleaned


def test_clean_ir_line_preserves_useful_content() -> None:
    raw = "  %x = alloca i32"
    assert clean_ir_line(raw).strip() == "%x = alloca i32"


def test_clean_ir_line_handles_empty_string() -> None:
    assert clean_ir_line("") == ""


# ---------------------------------------------------------------------------
# build_display_lines
# ---------------------------------------------------------------------------

_SAMPLE_IR = """\
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
"""


def test_build_display_lines_collects_functions() -> None:
    registry = build_display_lines(_SAMPLE_IR)
    assert set(registry) == {"main", "helper"}


def test_build_display_lines_skips_intrinsics() -> None:
    registry = build_display_lines(_SAMPLE_IR)
    assert all("@llvm." not in line for line in registry["main"])


def test_build_display_lines_includes_define_and_closing_brace() -> None:
    registry = build_display_lines(_SAMPLE_IR)
    assert any(line.startswith("define i32 @main") for line in registry["main"])
    assert registry["main"][-1] == "}"
    assert registry["helper"][-1] == "}"


def test_build_display_lines_cleans_metadata_and_attributes() -> None:
    registry = build_display_lines(_SAMPLE_IR)
    for line in registry["main"]:
        assert "!dbg" not in line
        assert "#0" not in line


def test_build_display_lines_empty_ir() -> None:
    assert build_display_lines("") == {}


def test_build_display_lines_declare_only_ir() -> None:
    """Declared (but not defined) functions should not produce display lines."""
    ir = "declare void @puts(ptr)\n"
    assert build_display_lines(ir) == {}


def test_build_display_lines_preserves_instruction_order() -> None:
    ir = """\
define void @f() {
entry:
  %a = alloca i32
  %b = alloca i64
  ret void
}
"""
    lines = build_display_lines(ir)["f"]
    # First line is define, last is }, middle are instructions
    alloca_lines = [line for line in lines if "alloca" in line]
    assert len(alloca_lines) == 2
    assert "i32" in alloca_lines[0]
    assert "i64" in alloca_lines[1]


def test_build_display_lines_multiple_blocks() -> None:
    ir = """\
define void @f(i1 %cond) {
entry:
  br i1 %cond, label %yes, label %no
yes:
  ret void
no:
  ret void
}
"""
    lines = build_display_lines(ir)["f"]
    assert any("br" in line for line in lines)
    ret_lines = [line for line in lines if "ret" in line]
    assert len(ret_lines) == 2
