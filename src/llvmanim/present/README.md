# llvmanim.present

Presentation-layer modules for LLVManim.

## Active CLI Rendering Path

The CLI currently renders animations through `rich_stack_scene.py`.

Flow used by `llvmanim.cli.main`:

1. Parse `.ll` file into `ProgramEventStream`.
2. Build one of two Manim scenes from that stream:
   - `RichStackSceneBadge` (`--ir-mode basic`)
   - `RichStackSceneSpotlight` (`--ir-mode rich`)
3. Call `scene.render(preview=...)`.

`RichStackSceneSpotlight` additionally builds a per-function IR source registry from the input `.ll` and keeps a moving cursor aligned to the current instruction.

## Export Utilities

- `json_export.py`: serializes `SceneGraph` to JSON (`scene_graph.json`)
- `graphviz_export.py`: writes DOT and optionally renders PNG with `graphviz`

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
