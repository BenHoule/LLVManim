"""Unit tests for pure helper functions in rich_stack_scene.py."""

from __future__ import annotations

from llvmanim.present.rich_stack_scene import (
    _call_site_idx,
    _clean_ir_line,
    _find_line_idx,
    build_ir_registry,
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

