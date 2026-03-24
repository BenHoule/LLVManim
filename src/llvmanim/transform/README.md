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
| `CFGEdge` | Control-flow edge between two blocks (`source`, `target`, `kind`, `label`) |
| `SceneNode` | One CFG block ready for presentation (`id`, `label`, `role`, `animation_hint`) |
| `SceneGraph` | Full scene graph: `nodes`, `edges`, `overlay: TraceOverlay | None` |
| `TraceOverlay` | Runtime path overlay: `visited_nodes`, `traversed_edges`, `entry_order`, `termination_reason` |
| `BlockMetadata` | Per-block dominator-tree and loop-structure metadata |

`BlockRole` values: `entry`, `linear`, `branch`, `merge`, `exit`.

### `scene.py`

```python
from llvmanim.transform.scene import build_scene_graph

graph: SceneGraph = build_scene_graph(stream)
```

Steps performed by `build_scene_graph`:

1. Groups events by `(function_name, block_name)` into `CFGBlock` objects.
2. Takes control-flow edges from `event_stream.cfg_edges` (populated by the ingest layer via llvmlite).
3. Assigns a `BlockRole` to each block based on in/out degree and terminator opcode.
4. Optionally applies analysis metadata (domtree/loop) onto matching blocks.
5. Wraps each block in a `SceneNode` with an `animation_hint` string.

### `trace.py`

CFG-trace derivation: builds a static traversal path by walking CFG edges.

#### `derive_cfg_trace`

Derives a static CFG trace by walking edges from the entry block:

```python
from llvmanim.transform.trace import derive_cfg_trace

overlay: TraceOverlay = derive_cfg_trace(graph, function="main")
```

- Prefers `T`-labelled (true-branch) edges at conditional branches.
- Unrolls loops up to `max_loop_iterations` times (default: 7).
- Returns a `TraceOverlay` with `entry_order`, `visited_nodes`, `traversed_edges`, and `termination_reason`.
- Used by the CLI when `--cfg-animate` is given without `--import-trace`.

### `scene.py`

`build_scene_graph` is complemented by `build_stack_scene_graph`, which wraps
the call for the stack-animation path (always passes `include_cfg_edges=True`).
