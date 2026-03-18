"""CLI entrypoint for LLVManim."""

from __future__ import annotations

import argparse
from pathlib import Path

from llvmanim.ingest import parse_module_to_events
from llvmanim.present import export_cfg_dot, export_cfg_png, export_scene_graph_json
from llvmanim.present.rich_stack_scene import RichStackSceneBadge, RichStackSceneSpotlight
from llvmanim.transform.scene import build_scene_graph

try:
    from manim import config as manim_config
except ImportError:
    manim_config = None  # type: ignore[assignment]


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

    args = parser.parse_args(argv)

    input_path = Path(args.input)
    outdir = Path(args.outdir)

    if not input_path.exists():
        print(f"Error: input file not found: {input_path}")
        return 1

    outdir.mkdir(parents=True, exist_ok=True)

    stream = parse_module_to_events(input_path.as_posix())
    graph = build_scene_graph(stream)

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
        if manim_config is not None:
            manim_config.media_dir = str(outdir)
        if args.ir_mode == "rich":
            animation_scene = RichStackSceneSpotlight(stream, speed=args.speed)
        else:
            animation_scene = RichStackSceneBadge(stream, speed=args.speed)
        animation_scene.render(preview=args.preview)

    return 0
