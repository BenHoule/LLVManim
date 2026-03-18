"""Converts animation commands into a scene for LLVManim."""

from dataclasses import dataclass, field

from llvmanim.present.render_stack_model import RenderStep, build_render_steps
from llvmanim.transform.commands import AnimationCommand


@dataclass(slots=True)
class LLVManimScene:
    """Holds a sequence of animation steps derived from LLVM IR commands."""

    steps: list[RenderStep] = field(default_factory=list)


def build_scene(commands: list[AnimationCommand]) -> LLVManimScene:
    """Convert a list of animation commands into a scene ready for presentation."""
    steps = build_render_steps(commands)
    scene = LLVManimScene(steps=steps)
    return scene
