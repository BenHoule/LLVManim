from dataclasses import dataclass, field
from typing import Literal

from llvmanim.transform.models import EventKind
from llvmanim.transform.scene import SceneGraph, SceneNode

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
    node: SceneNode  # Forward reference to avoid circular import issues


def build_animation_commands(scene_graph: SceneGraph) -> list[AnimationCommand]:
    """Translate a scene graph into a list of animation commands.

    Each command corresponds to an IREvent in the scene graph, with the action
    determined by the event's kind. The node reference allows commands to be
    associated back to the original event for context during animation."""
    commands = []
    for node in scene_graph.nodes:
        # unsupported kinds are filtered out in scene graph construction,
        # so we can assume all nodes are mappable
        event_kind = node.event.kind
        action = _EVENT_TO_ACTION[event_kind]
        cmd = AnimationCommand(action=action, node=node)
        commands.append(cmd)

    return commands
