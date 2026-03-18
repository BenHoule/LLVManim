"""CLI entrypoint for LLVManim."""

from __future__ import annotations

import sys

from llvmanim.ingest.llvm_events import parse_module_to_events
from llvmanim.present.scene_builder import LLVManimScene, build_scene
from llvmanim.transform.commands import build_animation_commands
from llvmanim.transform.scene import build_scene_graph


def main(args: list[str] | None = None) -> int:
    """Main function for the CLI."""
    argv = args if args is not None else sys.argv[1:]
    if not argv:
        print("Usage: llvmanim <path-to-file.ll>")
        return 1

    path = argv[0]
    stream = parse_module_to_events(path)
    graph = build_scene_graph(stream)
    commands = build_animation_commands(graph)

    # For this prototype, we just print the commands instead of rendering a scene.
    for cmd in commands:
        print(f"{cmd.action}: {cmd.node.event.text.strip()}")

    return 0
