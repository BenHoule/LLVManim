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

    @property
    def function_names(self) -> set[str]:
        """Set of all function names represented in the scene graph."""
        return {node.event.function_name for node in self.nodes}

    @property
    def block_names(self) -> set[str]:
        """Set of all block names represented in the scene graph."""
        return {node.event.block_name for node in self.nodes}

    def get_function_nodes(self, function_name: str) -> list[SceneNode]:
        """Retrieve all nodes corresponding to a specific function."""
        return [node for node in self.nodes if node.event.function_name == function_name]

    def get_block_nodes(self, function_name: str, block_name: str) -> list[SceneNode]:
        """Retrieve all nodes corresponding to a specific block."""
        return [
            node
            for node in self.get_function_nodes(function_name)
            if node.event.block_name == block_name
        ]


def build_scene_graph(event_stream: ProgramEventStream) -> SceneGraph:
    """Construct a scene graph from a stream of IREvents.

    Groups events by function and block structure, creating parent-child
    relationships between instructions in the same block and nesting blocks
    within their functions. The exact structure can be adjusted to support
    different visualization styles."""
    graph = SceneGraph()

    for event in event_stream.events:
        if event.kind == "other":
            continue  # Skip events we do not plan to visualize
        node = SceneNode(event=event)
        graph.nodes.append(node)

    return graph
