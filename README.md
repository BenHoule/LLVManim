# LLVManim

LLVManim parses LLVM IR (`.ll`) into a typed event stream, derives a CFG-style scene graph, and can export machine-readable artifacts or render stack-focused animations with Manim.

## Current Capabilities

- Parse LLVM IR into `ProgramEventStream` events using `llvmlite`
- Build a scene graph where each CFG block becomes a `SceneNode`
- Export scene graph JSON (`scene_graph.json`)
- Export Graphviz DOT (`cfg_main.dot`) and, when Graphviz binaries are available, PNG (`cfg_main.png`)
- Render call-stack animations through Manim CE:
  - `--ir-mode basic`: stack-only with per-cell badge flash
  - `--ir-mode rich`: IR source panel + moving spotlight cursor + stack view

## Requirements

- Python 3.12+
- `uv`
- LLVM toolchain (for producing `.ll` from C/C++ during local experiments)
- Linux packages commonly required by Manim dependencies:

```bash
sudo apt install pkg-config libcairo2-dev libpango1.0-dev
```

- Optional but recommended for PNG graph export:

```bash
sudo apt install graphviz
```

## Setup And Validation

Install project dependencies:

```bash
uv sync --dev
```

Run full quality checks:

```bash
./scripts/quality-check.sh
```

Run tests directly:

```bash
uv run pytest -q
```

## CLI Usage

Entry point:

```bash
uv run llvmanim [input.ll] [flags]
```

Default input is `tests/ingest/testdata/double.ll` when no positional argument is supplied.

### Flags

- `--json`: write `scene_graph.json`
- `--draw`: write `cfg_main.dot`; also attempts `cfg_main.png`
- `--animate`: render animation video via Manim
- `--preview`: open rendered animation in viewer (implies animation render)
- `--ir-mode {basic,rich}`: choose animation style (default: `basic`)
- `--speed <float>`: animation speed multiplier (default: `1.0`)
- `--format {mp4,gif}`: animation output format (default: `mp4`)
- `--gif-fps <int>`: GIF conversion FPS when `--format gif` (default: `12`)
- `--gif-width <int>`: GIF conversion width in px when `--format gif` (default: `960`)
- `--outdir <path>`: output directory (default: current directory)

### Common Examples

Parse and print summary only:

```bash
uv run llvmanim tests/ingest/testdata/double.ll
```

Export JSON + DOT/PNG:

```bash
uv run llvmanim tests/ingest/testdata/double.ll --json --draw --outdir llvmanim_out
```

Render stack animation (basic mode):

```bash
uv run llvmanim tests/ingest/testdata/double.ll --animate --ir-mode basic --outdir llvmanim_out
```

Render as GIF:

```bash
uv run llvmanim tests/ingest/testdata/double.ll --animate --format gif --outdir llvmanim_out
```

Low-memory GIF render (recommended for WSL):

```bash
uv run llvmanim tests/ingest/testdata/double.ll --animate --format gif --gif-fps 10 --gif-width 720 --outdir llvmanim_out
```

Render rich IR+stack animation and preview:

```bash
uv run llvmanim tests/ingest/testdata/double.ll --preview --ir-mode rich --speed 1.5 --outdir llvmanim_out
```

## Pipeline (Current Implementation)

```
┌─────────────────────────────────────────────────────────────┐
│                         CLI (cli/)                          │
│  uv run llvmanim input.ll [--json] [--draw] [--animate]     │
│                           [--preview] [--ir-mode basic|rich]│
│                           [--speed N] [--outdir PATH]       │
│                                                             │
│  • Parses flags; opens .ll file                             │
│  • Calls parse_module_to_events → build_scene_graph         │
│  • Dispatches to export and/or animation paths              │
└──────────────┬─────────────────────────────────────────────-┘
               │ .ll file path
               ▼
┌─────────────────────────────────────────────────────────────┐
│                      Ingest (ingest/)                       │
│                                                             │
│  parse_module_to_events(path) → ProgramEventStream          │
│                                                             │
│  • llvmlite: parse module, walk functions/blocks/instrs     │
│  • Each IREvent carries: function_name, block_name, opcode, │
│    text, kind, index_in_function, debug_line, operands      │
│  • kind ∈ {alloca, load, store, call, ret, br, other}       │
└──────────────┬──────────────────────────────────────────────┘
               │ ProgramEventStream
               ▼
┌─────────────────────────────────────────────────────────────┐
│                   Transform (transform/)                    │
│                                                             │
│  build_scene_graph(stream) → SceneGraph                     │
│                                                             │
│  • Groups events by (function, block) → CFGBlock            │
│  • Extracts branch edges from br terminator text            │
│  • Assigns block roles from edge topology:                  │
│      entry · linear · branch · merge · exit                 │
│  • Each block → SceneNode with id, label, role,             │
│    animation_hint                                           │
└──────┬────────────────────────────────────┬─────────────────┘
       │ SceneGraph                         │ ProgramEventStream
       ▼                                    ▼
┌──────────────────────┐      ┌─────────────────────────────────┐
│  Export (present/)   │      │  Animation (present/)           │
│                      │      │                                 │
│  --json →            │      │  --animate / --preview          │
│    scene_graph.json  │      │                                 │
│                      │      │  build_execution_trace(stream)  │
│  --draw →            │      │   → TraceStep list              │
│    cfg_main.dot      │      │                                 │
│    cfg_main.png      │      │  --ir-mode basic                │
│    (needs graphviz)  │      │    RichStackSceneBadge          │
│                      │      │      stack-only, badge flash    │
│                      │      │  --ir-mode rich                 │
│                      │      │    RichStackSceneSpotlight      │
│                      │      │      IR panel + cursor + stack  │
│                      │      │                                 │
│                      │      │  scene.render(preview=...)      │
│                      │      │   → Manim CE MP4                │
└──────────────────────┘      └─────────────────────────────────┘
```

## Notes

- DOT export does not require system Graphviz binaries; PNG export does.
- GIF output renders MP4 first and then converts via `ffmpeg` palette workflow to reduce peak memory usage.
- `pyproject.toml` includes both `manim` and `manimgl` dependencies, but the current CLI animation path uses Manim Community Edition scenes in `src/llvmanim/present/rich_stack_scene.py`.
- Sandbox directories contain experimental scripts and examples and are not used by the package entrypoint.
