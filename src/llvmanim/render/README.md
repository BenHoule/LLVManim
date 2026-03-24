# llvmanim.render

Render-layer modules for LLVManim.

## Active CLI Rendering Paths

The CLI provides two animation pipelines, both using the `CommandDrivenScene` base:

### Stack Animation (`--animate` / `--preview`)

Rendered through `stack_renderer.py`:

1. Parse `.ll` file into `ProgramEventStream`.
2. Build a `SceneGraph` via `build_scene_graph(stream, mode="stack")`.
3. Create a `StackRenderer` with one of three `ir_mode` settings:
   - `"basic"` (`--ir-mode basic`) — stack-only layout with yellow badge flash
   - `"rich"` (`--ir-mode rich`) — two-column: IR source with spotlight cursor + stack
   - `"rich-ssa"` (`--ir-mode rich-ssa`) — three-column: IR source + SSA values + stack
4. Call `scene.render(preview=...)`.

### CFG Traversal Animation (`--cfg-animate`)

Rendered through `cfg_renderer.py`:

1. Parse `.ll` file and build a `SceneGraph` with `TraceOverlay`.
2. Load DOT layout from `--dot-cfg` via `ingest.dot_layout`.
3. Build `CFGRenderer` with positioned nodes and routed edges.
4. Animate the runtime execution path stepping through blocks one at a time.

Requires `--dot-cfg` (DOT layout file).  If `--import-trace` is not provided, a
static trace is automatically derived from the CFG edges (with an interactive
confirmation prompt, skippable via `-y`).

`StackRenderer` in rich/rich-ssa modes reads per-function IR display lines from
`ProgramEventStream.display_lines` (populated at ingest time) and keeps a
moving cursor aligned to the current instruction.  It never re-reads the
`.ll` file.

## Export Utilities

- `json_export.py`: serializes `SceneGraph` to JSON (`scene_graph.json`)
- `graphviz_export.py`: writes DOT and optionally renders PNG with `graphviz`; renders T/F labels on conditional branch edges

These are used by CLI flags:

- `--json`
- `--draw`

## Files

| File | Purpose |
|---|---|
| `command_driven_scene.py` | Base class for command-driven Manim scenes with handler registry |
| `stack_renderer.py` | Stack animation renderer — basic, rich (IR+cursor), and rich-ssa (IR+SSA+stack) modes |
| `cfg_renderer.py` | CFG traversal animation renderer with DOT layout and trace overlay |
| `ssa_formatting.py` | Shared SSA display formatting (value labels, op colors, name extraction) |
| `cfg_animation_scene.py` | Shared helpers for CFG mobject construction (`_build_block_mob`, `_build_edge_mob`, `_CoordMapper`) |
| `json_export.py` | Serialize `SceneGraph` to JSON |
| `graphviz_export.py` | Write DOT and optionally render PNG via `graphviz` |
