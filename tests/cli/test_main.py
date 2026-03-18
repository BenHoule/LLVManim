"""CLI smoke tests."""

from llvmanim.cli.main import main


def test_main_returns_one() -> None:
    """CLI main returns error exit code."""
    assert main() == 1, "CLI should exit with code 1 when no arguments are provided"


def test_main_with_ir_file_prints_commands(tmp_path, capsys) -> None:
    """CLI main can process an IR file without crashing."""
    ll_file = tmp_path / "test.ll"
    ll_file.write_text("""
        define i32 @f() {
        entry:
            %x = alloca i32
            ret i32 0
        }
    """)
    code = main(args=[str(ll_file)])
    assert code == 0, "CLI should exit with code 0 on success"
    out = capsys.readouterr().out
    assert "create_stack_slot" in out
    assert "pop_stack_frame" in out
