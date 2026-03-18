"""CLI entrypoint for LLVManim."""

from __future__ import annotations

import argparse
from pathlib import Path

from llvmanim.ingest import parse_module_to_events
from llvmanim.present import export_cfg_dot, export_cfg_png, export_scene_graph_json
from llvmanim.transform.scene import build_scene_graph


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

    return 0
