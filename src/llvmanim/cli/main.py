"""CLI entrypoint for LLVManim."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from llvmanim.ingest import parse_module_to_events
from llvmanim.ingest.analysis_metadata_io import (
    AnalysisMetadataIOError,
    load_analysis_metadata,
    save_analysis_metadata,
)
from llvmanim.ingest.cfg_edge_io import CFGEdgeIOError, load_cfg_edges, save_cfg_edges
from llvmanim.ingest.dot_layout import DotLayoutError, compute_dot_layout
from llvmanim.ingest.trace_io import TraceIOError, load_trace, save_trace
from llvmanim.render import export_cfg_dot, export_cfg_png, export_scene_graph_json
from llvmanim.render.cfg_renderer import CFGRenderer
from llvmanim.render.stack_renderer import StackRenderer
from llvmanim.transform.models import BlockMetadata, SceneGraph
from llvmanim.transform.scene import (
    _build_overlay_commands,
    build_scene_graph,
)
from llvmanim.util import tools

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
    ffmpeg = tools.ffmpeg()
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
        if node.kind != "cfg_block":
            continue
        props = node.properties
        result[node.id] = BlockMetadata(
            idom=props.get("idom"),
            dom_depth=props.get("dom_depth", 0),
            is_loop_header=props.get("is_loop_header", False),
            loop_depth=props.get("loop_depth", 0),
            loop_id=props.get("loop_id"),
            is_backedge_target=props.get("is_backedge_target", False),
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
        choices=["rich", "rich-ssa", "basic"],
        default="basic",
        metavar="MODE",
        help="IR display mode: rich = IR source + spotlight cursor, rich-ssa = IR + SSA values + stack (3-column), basic = stack-only with badge flash (default: basic)",
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
        "--cfg-animate",
        action="store_true",
        help="Render a CFG traversal animation (requires --dot-cfg; auto-derives trace if --import-trace is not given)",
    )

    parser.add_argument(
        "--dot-cfg",
        metavar="PATH",
        help="Path to a .dot file from 'opt -passes=dot-cfg' for CFG layout",
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

    parser.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Skip confirmation prompts (e.g. auto-derive trace)",
    )

    parser.add_argument(
        "-n",
        "--name",
        metavar="NAME",
        help="Base name for output artifacts (default: stem of input file)",
    )

    args = parser.parse_args(argv)

    input_path = Path(args.input)
    outdir = Path(args.outdir)
    base_name = args.name if args.name else input_path.stem

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
        json_path = outdir / f"{base_name}_scene_graph.json"
        export_scene_graph_json(graph, json_path)
        print(f"Wrote JSON: {json_path}")

    if args.draw:
        dot_path = outdir / f"cfg_{base_name}.dot"
        png_prefix = outdir / f"cfg_{base_name}"

        export_cfg_dot(graph, dot_path)
        print(f"Wrote DOT: {dot_path}")

        png_ok = export_cfg_png(graph, png_prefix)
        if png_ok:
            print(f"Wrote PNG: {png_prefix}.png")
        else:
            print("Graphviz Python package not installed; skipped PNG export.")

    if args.cfg_animate:
        if not args.dot_cfg:
            print("Error: --cfg-animate requires --dot-cfg <path-to-.dot-file>")
            return 1

        if graph.overlay is None or not graph.overlay.entry_order:
            # Auto-derive a trace from the CFG edges.
            from llvmanim.transform.trace import derive_cfg_trace

            # Infer function name from the DOT filename (e.g. ".main.dot" → "main").
            dot_stem = Path(args.dot_cfg).stem.lstrip(".")
            func_name = dot_stem if dot_stem else "main"

            # Confirm with the user.
            node_ids = [n.id for n in graph.nodes if n.id.startswith(f"{func_name}::")]
            edge_count = sum(1 for e in graph.edges if e.source.startswith(f"{func_name}::"))
            print(
                f"No --import-trace provided.  Deriving a static trace for "
                f"@{func_name} ({len(node_ids)} blocks, {edge_count} edges)."
            )
            if not args.yes:
                answer = input("Proceed? [Y/n] ").strip().lower()
                if answer not in ("", "y", "yes"):
                    print("Aborted.")
                    return 0

            overlay = derive_cfg_trace(graph, function=func_name)
            if not overlay.entry_order:
                print(f"Error: could not derive a trace for @{func_name} (no entry block found)")
                return 1
            graph.overlay = overlay
            print(
                f"Derived trace: {len(overlay.entry_order)} steps, "
                f"{len(overlay.visited_nodes)} blocks visited."
            )

            if args.export_trace and not Path(args.export_trace).exists():
                save_trace(overlay, args.export_trace, source=stream.source_path)
                print(f"Wrote trace: {args.export_trace}")

        dot_path = Path(args.dot_cfg)
        if not dot_path.exists():
            print(f"Error: DOT file not found: {dot_path}")
            return 1
        try:
            dot_layout = compute_dot_layout(dot_path)
        except DotLayoutError as exc:
            print(f"Error: {exc}")
            return 1

        render_format = "mp4" if args.format == "gif" else args.format
        if manim_config is not None:
            manim_config.media_dir = str(outdir)
            manim_config.format = render_format
            manim_config.output_file = f"cfg_{base_name}"

        source_name = Path(stream.source_path).name
        cfg_title = f"CFG Traversal  ·  {source_name}"

        # Populate commands from the trace overlay for the new pipeline.
        graph.commands = _build_overlay_commands(graph)

        cfg_scene = CFGRenderer(
            graph,
            dot_layout,
            speed=args.speed,
            title=cfg_title,
        )
        cfg_scene.render(preview=args.preview)
        print("Rendered CFG traversal animation.")

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

    if args.animate or args.preview:
        render_format = "mp4" if args.format == "gif" else args.format
        if manim_config is not None:
            manim_config.media_dir = str(outdir)
            manim_config.format = render_format
            manim_config.output_file = base_name
        include_ssa = args.ir_mode == "rich-ssa"
        stack_graph = build_scene_graph(stream, mode="stack", include_ssa=include_ssa)
        animation_scene = StackRenderer(
            stack_graph,
            speed=args.speed,
            ir_mode=args.ir_mode,
            display_lines=stream.display_lines,
        )
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
