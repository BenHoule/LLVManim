"""CLI smoke tests."""

import json
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
    assert (outdir / "test_scene_graph.json").exists()


def test_main_draw_flag_writes_dot_file(tmp_path) -> None:
    """--draw flag writes a cfg_<name>.dot file to the output directory."""
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
    assert (outdir / "cfg_test.dot").exists()


def test_name_flag_overrides_output_basenames(tmp_path) -> None:
    """--name flag overrides the base name used for output artifacts."""
    ll_file = tmp_path / "test.ll"
    ll_file.write_text("""
        define i32 @f() {
        entry:
            ret i32 0
        }
    """)
    outdir = tmp_path / "out"
    code = main(
        argv=[str(ll_file), "--json", "--draw", "--outdir", str(outdir), "--name", "myproject"]
    )
    assert code == 0
    assert (outdir / "myproject_scene_graph.json").exists()
    assert (outdir / "cfg_myproject.dot").exists()


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
    """--animate flag instantiates StackRenderer (default) and calls render()."""
    from unittest.mock import patch

    ll_file = tmp_path / "test.ll"
    ll_file.write_text("""
        define i32 @f() {
        entry:
            %x = alloca i32
            ret i32 0
        }
    """)
    with patch("llvmanim.cli.main.StackRenderer") as MockScene:
        code = main(argv=[str(ll_file), "--animate"])
    assert code == 0
    MockScene.assert_called_once()
    MockScene.return_value.render.assert_called_once()


def test_main_animate_flag_passes_graph_to_scene(tmp_path) -> None:
    """--animate flag passes a SceneGraph to the StackRenderer constructor."""
    from unittest.mock import patch

    from llvmanim.transform.models import SceneGraph

    ll_file = tmp_path / "test.ll"
    ll_file.write_text("""
        define i32 @f() {
        entry:
            ret i32 0
        }
    """)
    with patch("llvmanim.cli.main.StackRenderer") as MockScene:
        main(argv=[str(ll_file), "--animate"])
    graph_arg = MockScene.call_args[0][0]
    assert isinstance(graph_arg, SceneGraph)


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
    with patch("llvmanim.cli.main.StackRenderer") as MockScene:
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
    with patch("llvmanim.cli.main.StackRenderer") as MockScene:
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
    with (
        patch("llvmanim.cli.main.StackRenderer"),
        patch("llvmanim.cli.main.manim_config") as mock_cfg,
    ):
        main(argv=[str(ll_file), "--animate", "--outdir", str(outdir)])
    assert mock_cfg.media_dir == str(outdir)


def test_main_ir_mode_rich_uses_stack_renderer_with_ir_mode(tmp_path) -> None:
    """--ir-mode rich instantiates StackRenderer with ir_mode='rich'."""
    from unittest.mock import patch

    ll_file = tmp_path / "test.ll"
    ll_file.write_text("""
        define i32 @f() {
        entry:
            ret i32 0
        }
    """)
    with patch("llvmanim.cli.main.StackRenderer") as MockStack:
        code = main(argv=[str(ll_file), "--animate", "--ir-mode", "rich"])
    assert code == 0
    MockStack.assert_called_once()
    _, kwargs = MockStack.call_args
    assert kwargs.get("ir_mode") == "rich"
    assert "display_lines" in kwargs
    MockStack.return_value.render.assert_called_once_with(preview=False)


def test_main_ir_mode_rich_ssa_uses_stack_renderer_with_ir_mode(tmp_path) -> None:
    """--ir-mode rich-ssa instantiates StackRenderer with ir_mode='rich-ssa'."""
    from unittest.mock import patch

    ll_file = tmp_path / "test.ll"
    ll_file.write_text("""
        define i32 @f() {
        entry:
            ret i32 0
        }
    """)
    with patch("llvmanim.cli.main.StackRenderer") as MockStack:
        code = main(argv=[str(ll_file), "--animate", "--ir-mode", "rich-ssa"])
    assert code == 0
    MockStack.assert_called_once()
    _, kwargs = MockStack.call_args
    assert kwargs.get("ir_mode") == "rich-ssa"
    assert "display_lines" in kwargs
    MockStack.return_value.render.assert_called_once_with(preview=False)


def test_main_ir_mode_basic_uses_stack_renderer(tmp_path) -> None:
    """--ir-mode basic (default) instantiates StackRenderer with ir_mode='basic'."""
    from unittest.mock import patch

    ll_file = tmp_path / "test.ll"
    ll_file.write_text("""
        define i32 @f() {
        entry:
            ret i32 0
        }
    """)
    with patch("llvmanim.cli.main.StackRenderer") as MockStack:
        code = main(argv=[str(ll_file), "--animate", "--ir-mode", "basic"])
    assert code == 0
    MockStack.assert_called_once()
    _, kwargs = MockStack.call_args
    assert kwargs.get("ir_mode") == "basic"


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
    with patch("llvmanim.cli.main.StackRenderer") as MockScene:
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
    with patch("llvmanim.cli.main.StackRenderer") as MockScene:
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
    with (
        patch("llvmanim.cli.main.StackRenderer"),
        patch("llvmanim.cli.main.manim_config") as mock_cfg,
        patch("llvmanim.cli.main._find_latest_file", return_value=None),
    ):
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

    with (
        patch("llvmanim.cli.main.StackRenderer"),
        patch("llvmanim.cli.main._find_latest_file", return_value=fake_mp4),
        patch("llvmanim.cli.main._convert_mp4_to_gif", return_value=True) as mock_convert,
    ):
        code = main(
            argv=[
                str(ll_file),
                "--animate",
                "--format",
                "gif",
                "--gif-fps",
                "10",
                "--gif-width",
                "720",
            ]
        )

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


# -- CFG edge I/O CLI tests ---------------------------------------


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
    import os

    from llvmanim.cli.main import _find_latest_file

    older = tmp_path / "a.mp4"
    newer = tmp_path / "b.mp4"
    older.write_text("old")
    newer.write_text("new")

    # Set explicit distinct mtimes to avoid filesystem resolution flakiness.
    os.utime(older, (1000, 1000))
    os.utime(newer, (2000, 2000))

    assert _find_latest_file(tmp_path, "*.mp4") == newer


def test_convert_mp4_to_gif_returns_false_without_ffmpeg(tmp_path, capsys) -> None:
    """_convert_mp4_to_gif returns False and warns when ffmpeg is unavailable."""
    from unittest.mock import patch

    from llvmanim.cli.main import _convert_mp4_to_gif

    with patch("llvmanim.util.tools.ffmpeg", return_value=None):
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

    with (
        patch("llvmanim.util.tools.ffmpeg", return_value="/usr/bin/ffmpeg"),
        patch(
            "llvmanim.cli.main.subprocess.run",
            side_effect=subprocess.CalledProcessError(2, ["ffmpeg"]),
        ),
    ):
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

    with (
        patch("llvmanim.util.tools.ffmpeg", return_value="/usr/bin/ffmpeg"),
        patch("llvmanim.cli.main.subprocess.run") as mock_run,
    ):
        ok = _convert_mp4_to_gif(
            tmp_path / "in.mp4",
            tmp_path / "out.gif",
            fps=10,
            width=720,
        )

    assert ok is True
    assert mock_run.call_count == 2


# -- Analysis metadata CLI flags -----------------------------------


def test_import_analysis_metadata_bad_path_returns_one(tmp_path, capsys) -> None:
    """--import-analysis-metadata with missing file returns 1."""
    ll_file = tmp_path / "test.ll"
    ll_file.write_text("""
        define i32 @f() { entry: ret i32 0 }
    """)
    code = main(argv=[str(ll_file), "--import-analysis-metadata", str(tmp_path / "nope.json")])
    assert code == 1
    assert "not found" in capsys.readouterr().out


def test_import_analysis_metadata_malformed_returns_one(tmp_path, capsys) -> None:
    """--import-analysis-metadata with invalid JSON returns 1."""
    ll_file = tmp_path / "test.ll"
    ll_file.write_text("""
        define i32 @f() { entry: ret i32 0 }
    """)
    bad = tmp_path / "bad.json"
    bad.write_text("not json")
    code = main(argv=[str(ll_file), "--import-analysis-metadata", str(bad)])
    assert code == 1
    assert "invalid analysis metadata" in capsys.readouterr().out.lower()


def test_import_analysis_metadata_applies_to_graph(tmp_path, capsys) -> None:
    """--import-analysis-metadata applies metadata to the scene graph."""
    import json

    ll_file = tmp_path / "test.ll"
    ll_file.write_text("""
        define void @f() {
        entry:
          br label %loop
        loop:
          %c = icmp eq i32 0, 0
          br i1 %c, label %loop, label %exit
        exit:
          ret void
        }
    """)
    meta = {
        "version": 1,
        "source": "",
        "functions": [
            {
                "name": "f",
                "blocks": [
                    {"id": "f::loop", "is_loop_header": True, "loop_depth": 1},
                ],
            }
        ],
    }
    meta_path = tmp_path / "meta.json"
    meta_path.write_text(json.dumps(meta))

    code = main(
        argv=[
            str(ll_file),
            "--json",
            "--outdir",
            str(tmp_path),
            "--import-analysis-metadata",
            str(meta_path),
        ]
    )
    assert code == 0

    scene = json.loads((tmp_path / "test_scene_graph.json").read_text())
    loop_nodes = [n for n in scene["nodes"] if n["label"] == "loop"]
    assert len(loop_nodes) == 1
    assert loop_nodes[0]["animation_hint"] == "pulse_loop_header"


def test_export_analysis_metadata_writes_file(tmp_path, capsys) -> None:
    """--export-analysis-metadata writes a valid JSON metadata file."""
    import json

    ll_file = tmp_path / "test.ll"
    ll_file.write_text("""
        define i32 @f() { entry: ret i32 0 }
    """)
    meta_out = tmp_path / "meta_out.json"
    code = main(argv=[str(ll_file), "--export-analysis-metadata", str(meta_out)])
    assert code == 0
    assert meta_out.exists()

    data = json.loads(meta_out.read_text())
    assert data["version"] == 1
    assert "Wrote analysis metadata" in capsys.readouterr().out


# -- Trace overlay CLI flags --------------------------------------

_LOOP_IR = """\
define i32 @main() {
entry:
    br label %loop
loop:
    %c = icmp eq i32 0, 0
    br i1 %c, label %loop, label %exit
exit:
    ret i32 0
}
"""


def _write_trace_json(path: Path) -> None:
    """Write a minimal valid trace JSON file."""
    data = {
        "version": 1,
        "source": "",
        "entry_order": ["main::entry", "main::loop", "main::exit"],
        "visited_nodes": ["main::entry", "main::loop", "main::exit"],
        "traversed_edges": [
            ["main::entry", "main::loop"],
            ["main::loop", "main::exit"],
        ],
        "termination_reason": "ret",
    }
    path.write_text(json.dumps(data))


def test_import_trace_bad_path_returns_one(tmp_path, capsys) -> None:
    """--import-trace with a nonexistent path returns 1."""
    ll_file = tmp_path / "test.ll"
    ll_file.write_text(_LOOP_IR)
    code = main(argv=[str(ll_file), "--import-trace", str(tmp_path / "nope.json")])
    assert code == 1
    assert "not found" in capsys.readouterr().out


def test_import_trace_malformed_returns_one(tmp_path, capsys) -> None:
    """--import-trace with invalid JSON returns 1 with actionable message."""
    ll_file = tmp_path / "test.ll"
    ll_file.write_text(_LOOP_IR)
    bad = tmp_path / "bad.json"
    bad.write_text("{oops}")
    code = main(argv=[str(ll_file), "--import-trace", str(bad)])
    assert code == 1
    assert "invalid trace file" in capsys.readouterr().out.lower()


def test_import_trace_populates_overlay(tmp_path, capsys) -> None:
    """--import-trace loads a trace and applies it to the scene graph."""
    ll_file = tmp_path / "test.ll"
    ll_file.write_text(_LOOP_IR)
    trace_file = tmp_path / "trace.json"
    _write_trace_json(trace_file)

    outdir = tmp_path / "out"
    code = main(
        argv=[str(ll_file), "--import-trace", str(trace_file), "--draw", "--outdir", str(outdir)]
    )
    assert code == 0

    # DOT output should contain overlay styling
    dot_text = (outdir / "cfg_test.dot").read_text()
    assert "#d4edda" in dot_text  # visited node fill


def test_export_trace_writes_file(tmp_path, capsys) -> None:
    """--import-trace + --export-trace round-trips the trace to a new file."""
    ll_file = tmp_path / "test.ll"
    ll_file.write_text(_LOOP_IR)
    trace_in = tmp_path / "trace_in.json"
    _write_trace_json(trace_in)
    trace_out = tmp_path / "trace_out.json"

    code = main(
        argv=[
            str(ll_file),
            "--import-trace",
            str(trace_in),
            "--export-trace",
            str(trace_out),
        ]
    )
    assert code == 0
    assert trace_out.exists()

    data = json.loads(trace_out.read_text())
    assert data["version"] == 1
    assert "Wrote trace" in capsys.readouterr().out


def test_export_trace_without_import_warns(tmp_path, capsys) -> None:
    """--export-trace without --import-trace prints a warning."""
    ll_file = tmp_path / "test.ll"
    ll_file.write_text(_LOOP_IR)
    trace_out = tmp_path / "trace_out.json"

    code = main(argv=[str(ll_file), "--export-trace", str(trace_out)])
    assert code == 0
    assert "no trace overlay to export" in capsys.readouterr().out.lower()
    assert not trace_out.exists()


def test_no_trace_flag_produces_no_overlay(tmp_path) -> None:
    """Without --import-trace, DOT output has no overlay styling."""
    ll_file = tmp_path / "test.ll"
    ll_file.write_text(_LOOP_IR)
    outdir = tmp_path / "out"

    code = main(argv=[str(ll_file), "--draw", "--outdir", str(outdir)])
    assert code == 0

    dot_text = (outdir / "cfg_test.dot").read_text()
    assert "fillcolor" not in dot_text
    assert "penwidth" not in dot_text


# -- CFG animate CLI flags ----------------------------------------


def test_cfg_animate_requires_dot_cfg(tmp_path, capsys) -> None:
    """--cfg-animate without --dot-cfg returns error."""
    ll_file = tmp_path / "test.ll"
    ll_file.write_text(_LOOP_IR)
    trace_file = tmp_path / "trace.json"
    _write_trace_json(trace_file)
    code = main(argv=[str(ll_file), "--cfg-animate", "--import-trace", str(trace_file)])
    assert code == 1
    assert "--dot-cfg" in capsys.readouterr().out


def test_cfg_animate_auto_derives_trace(tmp_path, capsys) -> None:
    """--cfg-animate without --import-trace auto-derives a trace with --yes."""
    ll_file = tmp_path / "test.ll"
    ll_file.write_text(_LOOP_IR)
    dot_file = tmp_path / ".main.dot"
    dot_file.write_text("digraph { a -> b }")
    # --yes skips the prompt; the DOT will fail at layout parse, but the
    # auto-derive message should appear in stdout first.
    main(
        argv=[
            str(ll_file),
            "--cfg-animate",
            "--dot-cfg",
            str(dot_file),
            "--yes",
        ]
    )
    out = capsys.readouterr().out
    assert "Deriving a static trace for @main" in out


def test_cfg_animate_dot_file_not_found(tmp_path, capsys) -> None:
    """--cfg-animate with nonexistent DOT file returns error."""
    ll_file = tmp_path / "test.ll"
    ll_file.write_text(_LOOP_IR)
    trace_file = tmp_path / "trace.json"
    _write_trace_json(trace_file)
    code = main(
        argv=[
            str(ll_file),
            "--cfg-animate",
            "--dot-cfg",
            str(tmp_path / "nope.dot"),
            "--import-trace",
            str(trace_file),
        ]
    )
    assert code == 1
    assert "not found" in capsys.readouterr().out.lower()


def test_cfg_animate_dot_layout_error(tmp_path, capsys) -> None:
    """--cfg-animate with invalid DOT file returns error."""
    from unittest.mock import patch

    from llvmanim.ingest.dot_layout import DotLayoutError

    ll_file = tmp_path / "test.ll"
    ll_file.write_text(_LOOP_IR)
    dot_file = tmp_path / "cfg.dot"
    dot_file.write_text("bad dot")
    trace_file = tmp_path / "trace.json"
    _write_trace_json(trace_file)

    with patch("llvmanim.cli.main.compute_dot_layout", side_effect=DotLayoutError("test error")):
        code = main(
            argv=[
                str(ll_file),
                "--cfg-animate",
                "--dot-cfg",
                str(dot_file),
                "--import-trace",
                str(trace_file),
            ]
        )
    assert code == 1
    assert "test error" in capsys.readouterr().out


def test_cfg_animate_renders_scene(tmp_path, capsys) -> None:
    """--cfg-animate with valid inputs invokes CFGRenderer.render."""
    from unittest.mock import patch

    from llvmanim.ingest.dot_layout import DotLayout, DotNodeLayout

    ll_file = tmp_path / "test.ll"
    ll_file.write_text(_LOOP_IR)
    dot_file = tmp_path / "cfg.dot"
    dot_file.write_text("digraph { entry -> loop -> exit }")
    trace_file = tmp_path / "trace.json"
    _write_trace_json(trace_file)

    mock_layout = DotLayout(
        nodes={
            "entry": DotNodeLayout("entry", 100, 200, 100, 50),
            "loop": DotNodeLayout("loop", 100, 150, 100, 50),
            "exit": DotNodeLayout("exit", 100, 100, 100, 50),
        },
        edges=[],
        bounding_box=(0, 0, 200, 300),
    )

    with (
        patch("llvmanim.cli.main.compute_dot_layout", return_value=mock_layout),
        patch("llvmanim.cli.main.CFGRenderer") as mock_scene_cls,
    ):
        mock_instance = mock_scene_cls.return_value
        code = main(
            argv=[
                str(ll_file),
                "--cfg-animate",
                "--dot-cfg",
                str(dot_file),
                "--import-trace",
                str(trace_file),
                "--outdir",
                str(tmp_path / "out"),
            ]
        )
    assert code == 0
    mock_scene_cls.assert_called_once()
    mock_instance.render.assert_called_once()
