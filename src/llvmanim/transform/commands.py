"""Translation from IR event streams to typed animation commands."""

from dataclasses import dataclass
from typing import Literal

from llvmanim.transform.models import EventKind, IREvent, ProgramEventStream

ActionKind = Literal[
    "create_stack_slot",
    "animate_memory_read",
    "animate_memory_write",
    "push_stack_frame",
    "pop_stack_frame",
    "highlight_branch",
]

_EVENT_TO_ACTION: dict[EventKind, ActionKind] = {
    "alloca": "create_stack_slot",
    "load": "animate_memory_read",
    "store": "animate_memory_write",
    "call": "push_stack_frame",
    "ret": "pop_stack_frame",
    "br": "highlight_branch",
}


@dataclass(slots=True)
class AnimationCommand:
    """Represents a single animation command derived from an IREvent."""

    action: ActionKind
    event: IREvent


def build_animation_commands(stream: ProgramEventStream) -> list[AnimationCommand]:
    """Translate an event stream into a list of stack animation commands.

    Events with kind 'other' are skipped. Each remaining event maps to an
    ActionKind that drives the stack-frame visualization.

    Pop commands are emitted only when a matching prior push exists. This
    avoids unmatched extra pops when a flat IR event stream includes multiple
    return terminators from mutually exclusive control-flow branches."""
    commands: list[AnimationCommand] = []
    pushed_frames = 0

    for event in stream.events:
        if event.kind == "other":
            continue

        action = _EVENT_TO_ACTION[event.kind]

        if action == "push_stack_frame":
            pushed_frames += 1
            commands.append(AnimationCommand(action=action, event=event))
            continue

        if action == "pop_stack_frame":
            if pushed_frames == 0:
                continue
            pushed_frames -= 1
            commands.append(AnimationCommand(action=action, event=event))
            continue

        commands.append(AnimationCommand(action=action, event=event))

    return commands
