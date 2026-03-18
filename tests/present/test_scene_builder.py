"""tests/present/test_scene_builder.py"""

from llvmanim.ingest.llvm_events import parse_ir_to_events
from llvmanim.present.scene_builder import LLVManimScene, build_scene
from llvmanim.transform.commands import build_animation_commands
from llvmanim.transform.scene import build_scene_graph

# Minimal IR exercising every supported EventKind plus one "other" (icmp).
_ALL_KINDS_IR = """
define void @f(ptr %p) {
entry:
  %x = alloca i32
  store i32 99, ptr %x
  %v = load i32, ptr %x
  %cond = icmp eq i32 %v, 0
  br i1 %cond, label %yes, label %no
yes:
  call void @g()
  ret void
no:
  ret void
}

declare void @g()
"""


def test_build_scene_empty_commands_returns_empty():
    """Test that build_animations returns an empty list when given no commands."""
    scene = build_scene([])
    assert len(scene.animations) == 0, (
        "build_scene should return an empty list when given no commands"
    )


def test_build_animations_returns_one_per_command():
    """Test that build_animations produces one scene per command."""

    stream = parse_ir_to_events(_ALL_KINDS_IR, source_path="<test_ir>")
    graph = build_scene_graph(stream)
    commands = build_animation_commands(graph)
    scene = build_scene(commands)
    assert isinstance(scene, LLVManimScene), "build_scene should return a single scene instance"
    assert len(scene.animations) == len(commands), (
        "build_scene should produce one animation per command"
    )
