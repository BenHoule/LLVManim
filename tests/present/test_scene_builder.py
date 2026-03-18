"""tests/present/test_scene_builder.py"""

from llvmanim.ingest.llvm_events import parse_ir_to_events
from llvmanim.present.render_stack_model import RenderStep
from llvmanim.present.scene_builder import LLVManimScene, build_scene
from llvmanim.transform.commands import build_animation_commands

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
    """build_scene with no commands produces a scene with no steps."""
    scene = build_scene([])
    assert len(scene.steps) == 0


def test_build_scene_returns_one_step_per_command():
    """build_scene produces one RenderStep per animation command."""
    stream = parse_ir_to_events(_ALL_KINDS_IR, source_path="<test_ir>")
    commands = build_animation_commands(stream)
    scene = build_scene(commands)
    assert isinstance(scene, LLVManimScene)
    assert len(scene.steps) == len(commands)
    assert all(isinstance(s, RenderStep) for s in scene.steps)
