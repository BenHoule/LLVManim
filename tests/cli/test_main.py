"""CLI smoke tests."""

from llvmanim.cli.main import main


def test_main_returns_zero() -> None:
    """CLI main returns success when called with no args (uses default .ll file)."""
    assert main(argv=[]) == 0, "CLI should exit with code 0 using the default input file"


def test_main_with_ir_file_prints_summary(tmp_path, capsys) -> None:
    """CLI main can process an IR file and prints a scene graph summary."""
    ll_file = tmp_path / "test.ll"
    ll_file.write_text("""
        define i32 @f() {
        entry:
            %x = alloca i32
            ret i32 0
        }
    """)
    code = main(argv=[str(ll_file)])
    assert code == 0, "CLI should exit with code 0 on success"
    out = capsys.readouterr().out
    assert "Loaded IR from:" in out
    assert "Scene nodes:" in out
