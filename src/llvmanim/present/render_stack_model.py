"""View models for stack frame animation rendering."""

from __future__ import annotations

from dataclasses import dataclass, field

from llvmanim.transform.commands import ActionKind, AnimationCommand


@dataclass(slots=True)
class StackSlotView:
    """A single named slot (alloca) in a stack frame."""

    name: str


@dataclass(slots=True)
class StackFrameView:
    """The visible state of one stack frame."""

    function_name: str
    slots: list[StackSlotView] = field(default_factory=list)


@dataclass(slots=True)
class FrameStackView:
    """A snapshot of the entire call stack at one point in time."""

    frames: list[StackFrameView] = field(default_factory=list)


@dataclass(slots=True)
class RenderStep:
    """One animation step: what happened, which IR event caused it, and the resulting stack state."""

    action: ActionKind
    event: object
    state: FrameStackView


def _slot_name_from_alloca(text: str) -> str:
    """Extract the LHS name from an alloca instruction text like '%x = alloca i32'."""
    return text.split("=")[0].strip()


def build_render_steps(commands: list[AnimationCommand]) -> list[RenderStep]:
    """Walk animation commands and produce one RenderStep per command.

    Each step carries an independent FrameStackView snapshot reflecting stack
    state *after* the command is applied.
    """
    stack: list[StackFrameView] = []
    steps: list[RenderStep] = []

    for cmd in commands:
        if cmd.action == "push_stack_frame":
            stack.append(StackFrameView(function_name=cmd.event.function_name))

        elif cmd.action == "pop_stack_frame":
            if stack:
                # TODO: Remove this guard once commands.py uses proper
                # control-flow analysis (see GitHub issue: multiple
                # pop_stack_frame on conditional branches). The guard
                # silently swallows spurious pops and prevents crashes,
                # but it also hides the bug from the renderer. Eventually
                # the fix should live upstream so that the renderer can
                # surface incorrect control flow visually if it recurs.
                stack.pop()

        elif cmd.action == "create_stack_slot" and stack:
            slot_name = _slot_name_from_alloca(cmd.event.text)
            stack[-1].slots.append(StackSlotView(name=slot_name))

        snapshot = FrameStackView(
            frames=[
                StackFrameView(
                    function_name=frame.function_name,
                    slots=list(frame.slots),
                )
                for frame in stack
            ]
        )
        steps.append(RenderStep(action=cmd.action, event=cmd.event, state=snapshot))

    return steps
