"""Core data models shared by ingestion and transformation layers."""

from dataclasses import dataclass, field

from llvmanim.transform.models import IREvent, ProgramEventStream


@dataclass(slots=True)
class SceneNode:
    """A node in the scene graph, representing one IREvent and its relationships."""

    event: IREvent


@dataclass(slots=True)
class SceneGraph:
    """Hierarchical scene graph for LLVM IR visualization."""

    nodes: list[SceneNode] = field(default_factory=list)


def build_scene_graph(event_stream: ProgramEventStream) -> SceneGraph:
    """Construct a scene graph from a stream of IREvents.

    Groups events by function and block structure, creating parent-child
    relationships between instructions in the same block and nesting blocks
    within their functions. The exact structure can be adjusted to support
    different visualization styles."""
    graph = SceneGraph()

    for event in event_stream.events:
        # TODO: Implement actual grouping logic based on function and block structure.
        node = SceneNode(event=event)
        graph.nodes.append(node)

    return graph
