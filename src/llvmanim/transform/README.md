# llvmanim.transform

Transformation layer: converts a `ProgramEventStream` into scene-ready data structures.

## Modules

### `models.py`

Core data models shared by the ingest and transform layers.

Key types:

| Type | Description |
|---|---|
| `IREvent` | Single normalised LLVM instruction |
| `ProgramEventStream` | Ordered list of `IREvent` values for one module |
| `CFGBlock` | Basic block grouped from events; carries role, edges, memory ops |
| `CFGEdge` | Control-flow edge between two blocks (`source`, `target`, `kind`) |
| `SceneNode` | One CFG block ready for presentation (`id`, `label`, `role`, `animation_hint`) |
| `SceneGraph` | Full scene graph: `nodes: list[SceneNode]`, `edges: list[CFGEdge]` |

`BlockRole` values: `entry`, `linear`, `branch`, `merge`, `exit`.

### `scene.py`

```python
from llvmanim.transform.scene import build_scene_graph

graph: SceneGraph = build_scene_graph(stream)
```

Steps performed by `build_scene_graph`:

1. Groups events by `(function_name, block_name)` into `CFGBlock` objects.
2. Extracts control-flow edges by parsing `br` terminator instruction text.
3. Assigns a `BlockRole` to each block based on in/out degree and terminator opcode.
4. Wraps each block in a `SceneNode` with an `animation_hint` string.

### `commands.py`

Flat event-to-action translation used by the `present` layer's
command/render-step path.

```python
from llvmanim.transform.commands import build_animation_commands

commands: list[AnimationCommand] = build_animation_commands(stream)
```

`ActionKind` values and their source `EventKind`:

| EventKind | ActionKind |
|---|---|
| `alloca` | `create_stack_slot` |
| `load` | `animate_memory_read` |
| `store` | `animate_memory_write` |
| `call` | `push_stack_frame` |
| `ret` | `pop_stack_frame` |
| `br` | `highlight_branch` |
| `other` | *(skipped)* |
