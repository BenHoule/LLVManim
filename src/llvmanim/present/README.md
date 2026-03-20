# llvmanim.present

Presentation-layer modules for LLVManim.

## Active CLI Rendering Paths

The CLI provides two animation pipelines:

### Stack Animation (`--animate` / `--preview`)

Rendered through `rich_stack_scene.py`:

1. Parse `.ll` file into `ProgramEventStream`.
2. Build one of two Manim scenes from that stream:
   - `RichStackSceneBadge` (`--ir-mode basic`)
   - `RichStackSceneSpotlight` (`--ir-mode rich`)
3. Call `scene.render(preview=...)`.

### CFG Traversal Animation (`--cfg-animate`)

Rendered through `cfg_animation_scene.py`:

1. Parse `.ll` file and build a `SceneGraph` with `TraceOverlay`.
2. Load DOT layout from `--dot-cfg` via `ingest.dot_layout`.
3. Build `CFGAnimationScene` with positioned nodes and routed edges.
4. Animate the runtime execution path stepping through blocks one at a time.

Requires `--dot-cfg` (DOT layout file) and `--import-trace` (runtime path trace).

`RichStackSceneSpotlight` additionally builds a per-function IR source registry from the input `.ll` and keeps a moving cursor aligned to the current instruction.

## Export Utilities

- `json_export.py`: serializes `SceneGraph` to JSON (`scene_graph.json`)
- `graphviz_export.py`: writes DOT and optionally renders PNG with `graphviz`; renders T/F labels on conditional branch edges

These are used by CLI flags:

- `--json`
- `--draw`

## Command/RenderStep Stack Path (Still Supported In Code And Tests)

The project also includes a command-to-stack-view pipeline used in unit tests and reusable for scene composition:

1. `transform.commands.build_animation_commands` converts `IREvent` values into typed `AnimationCommand` values.
2. `render_stack_model.build_render_steps` reduces commands into a sequence of stack snapshots.
3. `scene_builder.build_scene` wraps those steps in `LLVManimScene`.
4. `manim_stack.StackAnimationScene` plays frame push/pop/slot animations via `StackMobjectManager`.

## Data Model (RenderStep Path)
```
RenderStep
├── action: ActionKind        (what happened)
├── event: IREvent            (the IR event that caused it)
└── state: FrameStackView     (the full stack state AFTER this step)
      └── frames: list[StackFrameView]
            ├── function_name: str
            └── slots: list[StackSlotView]
                  └── name: str
```

## Files

| File | Purpose |
|---|---|
| `rich_stack_scene.py` | Badge and spotlight stack animation scenes |
| `cfg_animation_scene.py` | CFG traversal animation scene with DOT layout and trace overlay |
| `json_export.py` | Serialize `SceneGraph` to JSON |
| `graphviz_export.py` | Write DOT and optionally render PNG via `graphviz` |
| `render_stack_model.py` | Reduce `AnimationCommand` values into `RenderStep` stack snapshots |
| `scene_builder.py` | Wrap render steps in `LLVManimScene` |
| `manim_stack.py` | `StackAnimationScene` — frame push/pop/slot animations via `StackMobjectManager` |
