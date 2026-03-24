"""Translation from IR event streams to typed animation commands."""

from __future__ import annotations

from llvmanim.transform.models import (
    ActionKind,
    AnimationCommand,
    EventKind,
    ProgramEventStream,
)

_EVENT_TO_ACTION: dict[EventKind, ActionKind] = {
    "alloca": "create_stack_slot",
    "load": "animate_memory_read",
    "store": "animate_memory_write",
    "binop": "animate_binop",
    "compare": "animate_compare",
    "call": "push_stack_frame",
    "ret": "pop_stack_frame",
    "br": "highlight_branch",
}


def build_animation_commands(stream: ProgramEventStream) -> list[AnimationCommand]:
    """Translate an event stream into a list of stack animation commands.

    Events with kind 'other' are skipped. Each remaining event maps to an
    ActionKind that drives the stack-frame visualization.

    Returns are translated into pop commands only when a matching prior push
    exists in the flattened stream. This avoids false-positive underflow
    signals on control-flow-alternative return blocks until trace generation
    becomes control-flow aware.

    Note: `signal_stack_underflow` remains available as an explicit action for
    future trace-driven pipelines that can prove underflow behavior."""
    commands: list[AnimationCommand] = []
    pushed_frames = 0

    for event in stream.events:
        if event.kind == "other":
            continue

        action = _EVENT_TO_ACTION[event.kind]

        if action == "push_stack_frame":
            pushed_frames += 1
            commands.append(AnimationCommand(
                action=action,
                target=event.function_name,
                event=event,
            ))
            continue

        if action == "pop_stack_frame":
            if pushed_frames == 0:
                continue
            pushed_frames -= 1
            commands.append(AnimationCommand(
                action=action,
                target=event.function_name,
                event=event,
            ))
            continue

        commands.append(AnimationCommand(
            action=action,
            target=f"{event.function_name}::{event.block_name}",
            event=event,
        ))

    return commands
