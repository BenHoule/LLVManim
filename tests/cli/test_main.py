"""CLI smoke tests."""

import subprocess
from pathlib import Path

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


def test_main_gif_renders_manim_as_mp4(tmp_path) -> None:
    """--format gif renders through Manim as mp4 first to avoid high memory GIF combine."""
    from unittest.mock import patch

    ll_file = tmp_path / "test.ll"
    ll_file.write_text("""
        define i32 @f() {
        entry:
            ret i32 0
        }
    """)
    with patch("llvmanim.cli.main.RichStackSceneBadge"), \
         patch("llvmanim.cli.main.manim_config") as mock_cfg, \
         patch("llvmanim.cli.main._find_latest_file", return_value=None):
        code = main(argv=[str(ll_file), "--animate", "--format", "gif"])

    assert code == 0
    assert mock_cfg.format == "mp4"


def test_main_gif_calls_conversion_when_mp4_found(tmp_path) -> None:
    """--format gif runs conversion step when a rendered mp4 is present."""
    from unittest.mock import patch

    ll_file = tmp_path / "test.ll"
    ll_file.write_text("""
        define i32 @f() {
        entry:
            ret i32 0
        }
    """)
    fake_mp4 = tmp_path / "media" / "videos" / "scene.mp4"

    with patch("llvmanim.cli.main.RichStackSceneBadge"), \
         patch("llvmanim.cli.main._find_latest_file", return_value=fake_mp4), \
         patch("llvmanim.cli.main._convert_mp4_to_gif", return_value=True) as mock_convert:
        code = main(argv=[str(ll_file), "--animate", "--format", "gif", "--gif-fps", "10", "--gif-width", "720"])

    assert code == 0
    mock_convert.assert_called_once_with(
        fake_mp4,
        Path(str(fake_mp4.with_suffix(".gif"))),
        fps=10,
        width=720,
    )


def test_find_latest_file_returns_none_when_no_matches(tmp_path) -> None:
    """_find_latest_file returns None when no files match the pattern."""
    from llvmanim.cli.main import _find_latest_file

    assert _find_latest_file(tmp_path, "*.mp4") is None


# ── CFG edge I/O CLI tests ───────────────────────────────────────


_BRANCH_IR = """\
define i32 @f(i1 %c) {
entry:
    br i1 %c, label %yes, label %no
yes:
    ret i32 1
no:
    ret i32 0
}
"""


def test_import_cfg_edges_bad_path_returns_one(tmp_path, capsys) -> None:
    """--import-cfg-edges with a nonexistent path returns 1."""
    ll_file = tmp_path / "test.ll"
    ll_file.write_text(_BRANCH_IR)
    code = main(argv=[str(ll_file), "--import-cfg-edges", str(tmp_path / "nope.json")])
    assert code == 1
    assert "not found" in capsys.readouterr().out


def test_import_cfg_edges_malformed_returns_one(tmp_path, capsys) -> None:
    """--import-cfg-edges with invalid JSON returns 1 with actionable message."""
    ll_file = tmp_path / "test.ll"
    ll_file.write_text(_BRANCH_IR)
    bad = tmp_path / "bad.json"
    bad.write_text("{oops}")
    code = main(argv=[str(ll_file), "--import-cfg-edges", str(bad)])
    assert code == 1
    assert "invalid cfg edge file" in capsys.readouterr().out.lower()


def test_import_cfg_edges_overrides_llvmlite_edges(tmp_path, capsys) -> None:
    """--import-cfg-edges replaces llvmlite-extracted edges with file edges."""
    import json

    ll_file = tmp_path / "test.ll"
    ll_file.write_text(_BRANCH_IR)
    edge_file = tmp_path / "cfg.json"
    edge_file.write_text(
        json.dumps(
            {
                "version": 1,
                "source": "",
                "functions": [
                    {
                        "name": "f",
                        "blocks": [
                            {"name": "entry", "id": "f::entry", "successors": ["f::yes"]},
                            {"name": "yes", "id": "f::yes", "successors": []},
                        ],
                    }
                ],
            }
        )
    )
    code = main(argv=[str(ll_file), "--import-cfg-edges", str(edge_file)])
    assert code == 0


def test_export_cfg_edges_writes_file(tmp_path, capsys) -> None:
    """--export-cfg-edges writes a valid CFG edge JSON file."""
    import json

    ll_file = tmp_path / "test.ll"
    ll_file.write_text(_BRANCH_IR)
    out = tmp_path / "edges.json"
    code = main(argv=[str(ll_file), "--export-cfg-edges", str(out)])
    assert code == 0
    data = json.loads(out.read_text())
    assert data["version"] == 1
    assert "Wrote CFG edges" in capsys.readouterr().out


def test_find_latest_file_returns_most_recent_match(tmp_path) -> None:
    """_find_latest_file returns the most recently modified matching file."""
    from llvmanim.cli.main import _find_latest_file

    older = tmp_path / "a.mp4"
    newer = tmp_path / "b.mp4"
    older.write_text("old")
    newer.write_text("new")

    older.touch()
    newer.touch()

    assert _find_latest_file(tmp_path, "*.mp4") == newer


def test_convert_mp4_to_gif_returns_false_without_ffmpeg(tmp_path, capsys) -> None:
    """_convert_mp4_to_gif returns False and warns when ffmpeg is unavailable."""
    from unittest.mock import patch

    from llvmanim.cli.main import _convert_mp4_to_gif

    with patch("llvmanim.cli.main.shutil.which", return_value=None):
        ok = _convert_mp4_to_gif(
            tmp_path / "in.mp4",
            tmp_path / "out.gif",
            fps=12,
            width=960,
        )

    assert ok is False
    assert "ffmpeg not found" in capsys.readouterr().out


def test_convert_mp4_to_gif_returns_false_on_ffmpeg_error(tmp_path, capsys) -> None:
    """_convert_mp4_to_gif returns False when ffmpeg command fails."""
    from unittest.mock import patch

    from llvmanim.cli.main import _convert_mp4_to_gif

    with patch("llvmanim.cli.main.shutil.which", return_value="/usr/bin/ffmpeg"), \
         patch("llvmanim.cli.main.subprocess.run", side_effect=subprocess.CalledProcessError(2, ["ffmpeg"])):
        ok = _convert_mp4_to_gif(
            tmp_path / "in.mp4",
            tmp_path / "out.gif",
            fps=12,
            width=960,
        )

    assert ok is False
    assert "ffmpeg GIF conversion failed" in capsys.readouterr().out


def test_convert_mp4_to_gif_returns_true_when_commands_succeed(tmp_path) -> None:
    """_convert_mp4_to_gif returns True when both ffmpeg commands succeed."""
    from unittest.mock import patch

    from llvmanim.cli.main import _convert_mp4_to_gif

    with patch("llvmanim.cli.main.shutil.which", return_value="/usr/bin/ffmpeg"), \
         patch("llvmanim.cli.main.subprocess.run") as mock_run:
        ok = _convert_mp4_to_gif(
            tmp_path / "in.mp4",
            tmp_path / "out.gif",
            fps=10,
            width=720,
        )

    assert ok is True
    assert mock_run.call_count == 2
