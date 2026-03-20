"""CLI entrypoint for LLVManim."""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path

from llvmanim.ingest import parse_module_to_events
from llvmanim.ingest.analysis_metadata_io import (
    AnalysisMetadataIOError,
    load_analysis_metadata,
    save_analysis_metadata,
)
from llvmanim.ingest.cfg_edge_io import CFGEdgeIOError, load_cfg_edges, save_cfg_edges
from llvmanim.ingest.trace_io import TraceIOError, load_trace, save_trace
from llvmanim.present import export_cfg_dot, export_cfg_png, export_scene_graph_json
from llvmanim.present.rich_stack_scene import RichStackSceneBadge, RichStackSceneSpotlight
from llvmanim.transform.models import BlockMetadata, SceneGraph
from llvmanim.transform.scene import build_scene_graph

try:
    from manim import config as manim_config
except ImportError:
    manim_config = None  # type: ignore[assignment]


def _find_latest_file(root: Path, pattern: str) -> Path | None:
    """Return the most recently modified file matching pattern below root."""
    candidates = [path for path in root.rglob(pattern) if path.is_file()]
    if not candidates:
        return None
    return max(candidates, key=lambda path: path.stat().st_mtime)


def _convert_mp4_to_gif(mp4_path: Path, gif_path: Path, fps: int, width: int) -> bool:
    """Convert mp4_path to gif_path with ffmpeg using a low-memory palette workflow.

    This is here because trying to use the Manim GIF renderer directly can lead to very
    high memory usage when combining frames into a GIF, (enough to crash my WSL process).
    By rendering to MP4 first and then converting to GIF with ffmpeg using a palette, we
    keep memory usage much lower."""
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        print("Warning: ffmpeg not found; skipping GIF conversion.")
        return False

    palette_path = gif_path.with_suffix(".palette.png")
    scale_filter = f"fps={fps},scale={width}:-1:flags=lanczos"
    try:
        subprocess.run(
            [
                ffmpeg,
                "-y",
                "-i",
                str(mp4_path),
                "-vf",
                f"{scale_filter},palettegen=stats_mode=diff",
                str(palette_path),
            ],
            check=True,
        )

        subprocess.run(
            [
                ffmpeg,
                "-y",
                "-i",
                str(mp4_path),
                "-i",
                str(palette_path),
                "-lavfi",
                f"{scale_filter}[x];[x][1:v]paletteuse=dither=sierra2_4a",
                str(gif_path),
            ],
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        print(f"Warning: ffmpeg GIF conversion failed (exit {exc.returncode}).")
        return False
    finally:
        palette_path.unlink(missing_ok=True)

    return True


def _collect_analysis_metadata(graph: SceneGraph) -> dict[str, BlockMetadata]:
    """Extract per-block analysis metadata from a built scene graph."""
    result: dict[str, BlockMetadata] = {}
    for node in graph.nodes:
        blk = node.block
        result[blk.id] = BlockMetadata(
            idom=blk.idom,
            dom_depth=blk.dom_depth,
            is_loop_header=blk.is_loop_header,
            loop_depth=blk.loop_depth,
            loop_id=blk.loop_id,
            is_backedge_target=blk.is_backedge_target,
        )
    return result


def main(argv: list[str] | None = None) -> int:
    """Main function for the CLI."""
    parser = argparse.ArgumentParser(description="LLVManim LLVM IR visualization tool")

    parser.add_argument(
        "input",
        nargs="?",
        default="tests/ingest/testdata/double.ll",
        help="Path to LLVM IR file (.ll)",
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Export scene graph JSON",
    )

    parser.add_argument(
        "--draw",
        action="store_true",
        help="Export Graphviz DOT and PNG",
    )

    parser.add_argument(
        "--animate",
        action="store_true",
        help="Render stack animation video via Manim",
    )

    parser.add_argument(
        "--preview",
        action="store_true",
        help="Render and open the stack animation in a video viewer (implies --animate)",
    )

    parser.add_argument(
        "--ir-mode",
        choices=["rich", "basic"],
        default="basic",
        metavar="MODE",
        help="IR display mode: rich = full IR source with spotlight cursor, basic = stack-only with badge flash (default: basic)",
    )

    parser.add_argument(
        "--speed",
        type=float,
        default=1.0,
        metavar="MULTIPLIER",
        help="Animation speed multiplier (e.g. 2.0 = twice as fast, 0.5 = half speed; default: 1.0)",
    )

    parser.add_argument(
        "--outdir",
        default=".",
        help="Output directory",
    )

    parser.add_argument(
        "--format",
        choices=["mp4", "gif"],
        default="mp4",
        help="Animation output format (default: mp4)",
    )

    parser.add_argument(
        "--gif-fps",
        type=int,
        default=12,
        metavar="FPS",
        help="GIF conversion frame rate when --format gif (default: 12)",
    )

    parser.add_argument(
        "--gif-width",
        type=int,
        default=960,
        metavar="PX",
        help="GIF conversion width in pixels when --format gif (default: 960)",
    )

    parser.add_argument(
        "--import-cfg-edges",
        metavar="PATH",
        help="Import CFG edges from a JSON file instead of extracting from IR",
    )

    parser.add_argument(
        "--export-cfg-edges",
        metavar="PATH",
        help="Export extracted CFG edges to a JSON file",
    )

    parser.add_argument(
        "--import-analysis-metadata",
        metavar="PATH",
        help="Import domtree/loop analysis metadata from a JSON file",
    )

    parser.add_argument(
        "--export-analysis-metadata",
        metavar="PATH",
        help="Export analysis metadata to a JSON file",
    )

    parser.add_argument(
        "--import-trace",
        metavar="PATH",
        help="Import a runtime path trace from a JSON file for overlay visualization",
    )

    parser.add_argument(
        "--export-trace",
        metavar="PATH",
        help="Export the trace overlay to a JSON file",
    )

    args = parser.parse_args(argv)

    input_path = Path(args.input)
    outdir = Path(args.outdir)

    if not input_path.exists():
        print(f"Error: input file not found: {input_path}")
        return 1

    outdir.mkdir(parents=True, exist_ok=True)

    stream = parse_module_to_events(input_path.as_posix())

    if args.import_cfg_edges:
        edge_path = Path(args.import_cfg_edges)
        if not edge_path.exists():
            print(f"Error: CFG edge file not found: {edge_path}")
            return 1
        try:
            stream.cfg_edges = load_cfg_edges(edge_path)
        except CFGEdgeIOError as exc:
            print(f"Error: invalid CFG edge file: {exc}")
            return 1

    analysis_metadata = None
    if args.import_analysis_metadata:
        meta_path = Path(args.import_analysis_metadata)
        if not meta_path.exists():
            print(f"Error: analysis metadata file not found: {meta_path}")
            return 1
        try:
            analysis_metadata = load_analysis_metadata(meta_path)
        except AnalysisMetadataIOError as exc:
            print(f"Error: invalid analysis metadata file: {exc}")
            return 1

    graph = build_scene_graph(stream, analysis_metadata=analysis_metadata)

    if args.import_trace:
        trace_path = Path(args.import_trace)
        if not trace_path.exists():
            print(f"Error: trace file not found: {trace_path}")
            return 1
        try:
            graph.overlay = load_trace(trace_path)
        except TraceIOError as exc:
            print(f"Error: invalid trace file: {exc}")
            return 1

    if args.export_trace:
        if graph.overlay is None:
            print("Warning: no trace overlay to export (use --import-trace first)")
        else:
            save_trace(graph.overlay, args.export_trace, source=stream.source_path)
            print(f"Wrote trace: {args.export_trace}")

    if args.export_analysis_metadata:
        meta = _collect_analysis_metadata(graph)
        save_analysis_metadata(meta, args.export_analysis_metadata, source=stream.source_path)
        print(f"Wrote analysis metadata: {args.export_analysis_metadata}")

    if args.export_cfg_edges:
        save_cfg_edges(stream.cfg_edges, args.export_cfg_edges, source=stream.source_path)
        print(f"Wrote CFG edges: {args.export_cfg_edges}")

    print(f"Loaded IR from: {stream.source_path}")
    print(f"Event count: {len(stream.events)}")
    print(f"Scene nodes: {len(graph.nodes)}")
    print(f"Scene edges: {len(graph.edges)}")

    if args.json:
        json_path = outdir / "scene_graph.json"
        export_scene_graph_json(graph, json_path)
        print(f"Wrote JSON: {json_path}")

    if args.draw:
        dot_path = outdir / "cfg_main.dot"
        png_prefix = outdir / "cfg_main"

        export_cfg_dot(graph, dot_path)
        print(f"Wrote DOT: {dot_path}")

        png_ok = export_cfg_png(graph, png_prefix)
        if png_ok:
            print(f"Wrote PNG: {png_prefix}.png")
        else:
            print("Graphviz Python package not installed; skipped PNG export.")

    if args.animate or args.preview:
        render_format = "mp4" if args.format == "gif" else args.format
        if manim_config is not None:
            manim_config.media_dir = str(outdir)
            manim_config.format = render_format
        if args.ir_mode == "rich":
            animation_scene = RichStackSceneSpotlight(stream, speed=args.speed)
        else:
            animation_scene = RichStackSceneBadge(stream, speed=args.speed)
        animation_scene.render(preview=args.preview)

        if args.format == "gif":
            mp4_path = _find_latest_file(outdir, "*.mp4")
            if mp4_path is None:
                print("Warning: could not find rendered mp4 to convert into GIF.")
            else:
                gif_path = mp4_path.with_suffix(".gif")
                converted = _convert_mp4_to_gif(
                    mp4_path,
                    gif_path,
                    fps=max(args.gif_fps, 1),
                    width=max(args.gif_width, 64),
                )
                if converted:
                    print(f"Wrote GIF: {gif_path}")

    return 0
