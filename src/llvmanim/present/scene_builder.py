"""Converts animation commands into a scene for LLVManim."""

from dataclasses import dataclass, field

from llvmanim.transform.commands import AnimationCommand


@dataclass(slots=True)
class LLVManimScene:
    """Holds a sequence of animation steps derived from LLVM IR commands."""

    animations: list[AnimationCommand] = field(default_factory=list)


def build_scene(commands: list[AnimationCommand]) -> LLVManimScene:
    """Convert a list of animation commands into a scene ready for presentation."""
    scene = LLVManimScene(animations=list(commands))
    return scene
