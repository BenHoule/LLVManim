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


def test_main_animate_flag_calls_scene_render(tmp_path) -> None:
    """--animate flag instantiates RichStackSceneBadge (default) and calls render()."""
    from unittest.mock import patch

    ll_file = tmp_path / "test.ll"
    ll_file.write_text("""
        define i32 @f() {
        entry:
            %x = alloca i32
            ret i32 0
        }
    """)
    with patch("llvmanim.cli.main.RichStackSceneBadge") as MockScene:
        code = main(argv=[str(ll_file), "--animate"])
    assert code == 0
    MockScene.assert_called_once()
    MockScene.return_value.render.assert_called_once()


def test_main_animate_flag_passes_stream_to_scene(tmp_path) -> None:
    """--animate flag passes a ProgramEventStream to the scene constructor."""
    from unittest.mock import patch

    from llvmanim.transform.models import ProgramEventStream

    ll_file = tmp_path / "test.ll"
    ll_file.write_text("""
        define i32 @f() {
        entry:
            ret i32 0
        }
    """)
    with patch("llvmanim.cli.main.RichStackSceneBadge") as MockScene:
        main(argv=[str(ll_file), "--animate"])
    stream_arg = MockScene.call_args[0][0]
    assert isinstance(stream_arg, ProgramEventStream)


def test_main_preview_flag_calls_render_with_preview(tmp_path) -> None:
    """--preview flag calls render(preview=True)."""
    from unittest.mock import patch

    ll_file = tmp_path / "test.ll"
    ll_file.write_text("""
        define i32 @f() {
        entry:
            ret i32 0
        }
    """)
    with patch("llvmanim.cli.main.RichStackSceneBadge") as MockScene:
        code = main(argv=[str(ll_file), "--preview"])
    assert code == 0
    MockScene.return_value.render.assert_called_once_with(preview=True)


def test_main_animate_flag_calls_render_without_preview(tmp_path) -> None:
    """--animate without --preview calls render(preview=False)."""
    from unittest.mock import patch

    ll_file = tmp_path / "test.ll"
    ll_file.write_text("""
        define i32 @f() {
        entry:
            ret i32 0
        }
    """)
    with patch("llvmanim.cli.main.RichStackSceneBadge") as MockScene:
        code = main(argv=[str(ll_file), "--animate"])
    assert code == 0
    MockScene.return_value.render.assert_called_once_with(preview=False)


def test_main_animate_sets_manim_media_dir(tmp_path) -> None:
    """--animate sets Manim's media_dir to --outdir before rendering."""
    from unittest.mock import patch

    ll_file = tmp_path / "test.ll"
    ll_file.write_text("""
        define i32 @f() {
        entry:
            ret i32 0
        }
    """)
    outdir = tmp_path / "out"
    with patch("llvmanim.cli.main.RichStackSceneBadge"), \
         patch("llvmanim.cli.main.manim_config") as mock_cfg:
        main(argv=[str(ll_file), "--animate", "--outdir", str(outdir)])
    assert mock_cfg.media_dir == str(outdir)


def test_main_ir_mode_rich_uses_spotlight_scene(tmp_path) -> None:
    """--ir-mode rich instantiates RichStackSceneSpotlight instead of RichStackSceneBadge."""
    from unittest.mock import patch

    ll_file = tmp_path / "test.ll"
    ll_file.write_text("""
        define i32 @f() {
        entry:
            ret i32 0
        }
    """)
    with patch("llvmanim.cli.main.RichStackSceneSpotlight") as MockSpotlight, \
         patch("llvmanim.cli.main.RichStackSceneBadge") as MockBadge:
        code = main(argv=[str(ll_file), "--animate", "--ir-mode", "rich"])
    assert code == 0
    MockSpotlight.assert_called_once()
    MockBadge.assert_not_called()
    MockSpotlight.return_value.render.assert_called_once_with(preview=False)


def test_main_ir_mode_basic_uses_badge_scene(tmp_path) -> None:
    """--ir-mode basic (default) instantiates RichStackSceneBadge."""
    from unittest.mock import patch

    ll_file = tmp_path / "test.ll"
    ll_file.write_text("""
        define i32 @f() {
        entry:
            ret i32 0
        }
    """)
    with patch("llvmanim.cli.main.RichStackSceneBadge") as MockBadge, \
         patch("llvmanim.cli.main.RichStackSceneSpotlight") as MockSpotlight:
        code = main(argv=[str(ll_file), "--animate", "--ir-mode", "basic"])
    assert code == 0
    MockBadge.assert_called_once()
    MockSpotlight.assert_not_called()


def test_main_speed_flag_passes_multiplier_to_scene(tmp_path) -> None:
    """--speed passes the float multiplier to the scene constructor."""
    from unittest.mock import patch

    ll_file = tmp_path / "test.ll"
    ll_file.write_text("""
        define i32 @f() {
        entry:
            ret i32 0
        }
    """)
    with patch("llvmanim.cli.main.RichStackSceneBadge") as MockScene:
        main(argv=[str(ll_file), "--animate", "--speed", "2.5"])
    _, kwargs = MockScene.call_args
    assert kwargs.get("speed") == 2.5


def test_main_speed_default_is_1(tmp_path) -> None:
    """--speed defaults to 1.0 when not provided."""
    from unittest.mock import patch

    ll_file = tmp_path / "test.ll"
    ll_file.write_text("""
        define i32 @f() {
        entry:
            ret i32 0
        }
    """)
    with patch("llvmanim.cli.main.RichStackSceneBadge") as MockScene:
        main(argv=[str(ll_file), "--animate"])
    _, kwargs = MockScene.call_args
    assert kwargs.get("speed") == 1.0
