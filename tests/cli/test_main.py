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


def test_main_nonexistent_file_returns_one(tmp_path) -> None:
    """CLI main returns 1 and prints an error when the input file does not exist."""
    code = main(argv=[str(tmp_path / "nonexistent.ll")])
    assert code == 1


def test_main_json_flag_writes_scene_graph_json(tmp_path) -> None:
    """--json flag writes a scene_graph.json file to the output directory."""
    ll_file = tmp_path / "test.ll"
    ll_file.write_text("""
        define i32 @f() {
        entry:
            ret i32 0
        }
    """)
    outdir = tmp_path / "out"
    code = main(argv=[str(ll_file), "--json", "--outdir", str(outdir)])
    assert code == 0
    assert (outdir / "scene_graph.json").exists()


def test_main_draw_flag_writes_dot_file(tmp_path) -> None:
    """--draw flag writes a cfg_main.dot file to the output directory."""
    ll_file = tmp_path / "test.ll"
    ll_file.write_text("""
        define i32 @f() {
        entry:
            ret i32 0
        }
    """)
    outdir = tmp_path / "out"
    code = main(argv=[str(ll_file), "--draw", "--outdir", str(outdir)])
    assert code == 0
    assert (outdir / "cfg_main.dot").exists()


def test_main_draw_flag_prints_skipped_when_png_unavailable(tmp_path, capsys) -> None:
    """--draw flag prints a 'skipped PNG' message when export_cfg_png returns False."""
    from unittest.mock import patch

    ll_file = tmp_path / "test.ll"
    ll_file.write_text("""
        define i32 @f() {
        entry:
            ret i32 0
        }
    """)
    outdir = tmp_path / "out"
    with patch("llvmanim.cli.main.export_cfg_png", return_value=False):
        code = main(argv=[str(ll_file), "--draw", "--outdir", str(outdir)])
    assert code == 0
    assert "skipped PNG export" in capsys.readouterr().out
