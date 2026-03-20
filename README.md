# LLVManim

LLVManim parses LLVM IR (`.ll`) into a typed event stream, derives a CFG-style scene graph, and can export machine-readable artifacts or render stack-focused animations with Manim.

## Current Capabilities

- Parse LLVM IR into `ProgramEventStream` events using `llvmlite`
- Classify events: `alloca`, `load`, `store`, `binop`, `compare`, `call`, `ret`, `br` (others tagged `other`)
- Extract typed CFG edges directly from llvmlite terminator operands (`br`, `switch`, `invoke`, `indirectbr`, `callbr`)
- Assign T/F direction labels to conditional branch edges
- Import/export CFG edges as JSON (`--import-cfg-edges` / `--export-cfg-edges`)
- Import/export domtree and loop analysis metadata as JSON (`--import-analysis-metadata` / `--export-analysis-metadata`)
- Import/export runtime path traces as JSON (`--import-trace` / `--export-trace`)
- Build a scene graph where each CFG block becomes a `SceneNode` with optional `TraceOverlay`
- Export scene graph JSON (`scene_graph.json`)
- Export Graphviz DOT (`cfg_main.dot`) and, when Graphviz binaries are available, PNG (`cfg_main.png`)
- Render call-stack animations through Manim CE:
  - `--ir-mode basic`: stack-only with per-cell badge flash
  - `--ir-mode rich`: IR source panel + moving spotlight cursor + stack view
- Render CFG traversal animations (`--cfg-animate`) using DOT-derived layout from `opt -passes=dot-cfg`

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

Clone the repository:

```bash
git clone https://github.com/BenHoule/LLVManim.git
cd LLVManim
```

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

Run tests with coverage visibility:

```bash
uv run pytest -q --cov=llvmanim --cov-report=term-missing
```

## Test-Driven Development Workflow

Use a small-loop TDD cycle for new behavior and bug fixes:

1. Write a failing test first.
2. Implement the minimal change to make it pass.
3. Refactor while keeping tests green.
4. Run quality gates before opening/merging a PR.

```bash
./scripts/quality-check.sh
```

### Test Taxonomy

Pytest markers used by the suite:

- `unit`: deterministic tests without external dependencies
- `integration`: tests crossing multiple LLVManim layers
- `contract`: tests asserting behavior at external dependency boundaries
- `e2e`: end-to-end entrypoint/workflow tests

Markers are applied automatically by directory path convention in `tests/conftest.py` — no per-test decoration needed:

| Path prefix | Marker(s) applied |
|---|---|
| `tests/ingest/`, `tests/transform/` | `unit` |
| `tests/present/` | `integration` (+ `contract` for `test_exports.py`) |
| `tests/cli/`, `tests/test_pipeline.py` | `integration` |
| `tests/test_entrypoints.py` | `e2e` |

Example marker runs:

```bash
uv run pytest -q -m unit
uv run pytest -q -m integration
uv run pytest -q -m "contract or e2e"
```

### Shared Test Fixtures

Common deterministic inputs are defined in `tests/conftest.py` and available to all tests:

| Fixture | Type | Contents |
|---|---|---|
| `all_kinds_ir` | `str` | IR snippet exercising every supported `EventKind` |
| `double_ll_path` | `Path` | Path to `tests/ingest/testdata/double.ll` |
| `double_ll_text` | `str` | Contents of `double.ll` |
| `minimal_stream` | `ProgramEventStream` | Parsed stream from a single-block `ret i32 0` function |
| `branch_stream` | `ProgramEventStream` | Parsed stream from a two-branch `entry → yes/no` function |
| `branch_graph` | `SceneGraph` | Scene graph from `branch_stream` (3 nodes, 2 edges) |

## CLI Usage

Entry point:

```bash
uv run llvmanim [input.ll] [flags]
```

Default input is `tests/ingest/testdata/double.ll` when no positional argument is supplied.

### Flags

- `--json`: write `scene_graph.json`
- `--draw`: write `cfg_main.dot`; also attempts `cfg_main.png`
- `--animate`: render stack animation video via Manim
- `--preview`: open rendered animation in viewer (implies animation render)
- `--ir-mode {basic,rich}`: choose animation style (default: `basic`)
- `--speed <float>`: animation speed multiplier (default: `1.0`)
- `--format {mp4,gif}`: animation output format (default: `mp4`)
- `--gif-fps <int>`: GIF conversion FPS when `--format gif` (default: `12`)
- `--gif-width <int>`: GIF conversion width in px when `--format gif` (default: `960`)
- `--outdir <path>`: output directory (default: current directory)
- `--cfg-animate`: render a CFG traversal animation (requires `--dot-cfg` and `--import-trace`)
- `--dot-cfg <path>`: path to a `.dot` file from `opt -passes=dot-cfg` for CFG layout
- `--import-cfg-edges <path>`: load CFG edges from a JSON file instead of extracting them from IR
- `--export-cfg-edges <path>`: write extracted CFG edges to a JSON file
- `--import-analysis-metadata <path>`: load domtree/loop analysis metadata from a JSON file
- `--export-analysis-metadata <path>`: write analysis metadata to a JSON file
- `--import-trace <path>`: load a runtime path trace from a JSON file for overlay visualization
- `--export-trace <path>`: write the trace overlay to a JSON file

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
┌────────────────────────────────────────────────────────────────┐
│                           CLI (cli/)                           │
│  uv run llvmanim input.ll [--json] [--draw] [--animate]        │
│                           [--preview] [--ir-mode basic|rich]   │
│                           [--speed N] [--format mp4|gif]       │
│                           [--cfg-animate] [--dot-cfg PATH]     │
│                           [--import-trace PATH]                │
│                           [--import-cfg-edges PATH]            │
│                           [--import-analysis-metadata PATH]    │
│                           [--outdir PATH]                      │
│                                                                │
│  • Parses flags; opens .ll file                                │
│  • Calls parse_module_to_events → build_scene_graph            │
│  • Optionally loads additional JSON (edges, metadata, trace)   │
│  • Dispatches to export and/or animation paths                 │
└──────────────┬─────────────────────────────────────────────────┘
               │ .ll file path
               ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Ingest (ingest/)                         │
│                                                                 │
│  parse_module_to_events(path) → ProgramEventStream              │
│  load_cfg_edges(path) → list[CFGEdge]                           │
│  load_analysis_metadata(path) → dict[str, BlockMetadata]        │
│  load_trace(path) → TraceOverlay                                │
│  compute_dot_layout(path) → DotLayout                           │
│                                                                 │
│  • llvmlite: parse module, walk functions/blocks/instrs         │
│  • Typed CFG edges from all terminator operands (br, switch,    │
│    invoke, indirectbr, callbr) with T/F labels on cond. br      │
│  • Each IREvent carries: function_name, block_name, opcode,     │
│    text, kind, index_in_function, debug_line, operands          │
│  • kind ∈ {alloca,load,store,binop,compare,call,ret,br,other}   │
└──────────────┬──────────────────────────────────────────────────┘
               │ ProgramEventStream
               ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Transform (transform/)                      │
│                                                                 │
│  build_scene_graph(stream, analysis_metadata=...) → SceneGraph  │
│  build_execution_trace(stream) → list[TraceStep]                │
│  build_animation_commands(stream) → list[AnimationCommand]      │
│                                                                 │
│  • Groups events by (function, block) → CFGBlock                │
│  • Uses typed CFG edges from ingest (or imported JSON)          │
│  • Assigns block roles from edge topology:                      │
│      entry · linear · branch · merge · exit                     │
│  • Applies optional domtree/loop metadata                       │
│  • Attaches optional TraceOverlay for runtime path highlighting │
└──────┬────────────────────────────────────────┬─────────────────┘
       │ SceneGraph                              │ ProgramEventStream
       ▼                                        ▼
┌──────────────────────┐ ┌─────────────────────────────────────────┐
│  Export (present/)   │ │  Animation (present/)                   │
│                      │ │                                         │
│  --json →            │ │  --animate / --preview                  │
│    scene_graph.json  │ │    --ir-mode basic → RichStackSceneBadge│
│                      │ │    --ir-mode rich →                     │
│  --draw →            │ │      RichStackSceneSpotlight            │
│    cfg_main.dot      │ │                                         │
│    cfg_main.png      │ │  --cfg-animate →                        │
│    (needs graphviz)  │ │    CFGAnimationScene (DOT layout +      │
│                      │ │    trace overlay traversal)             │
└──────────────────────┘ └─────────────────────────────────────────┘
```

## Notes

- DOT export does not require system Graphviz binaries; PNG export does.
- GIF output renders MP4 first and then converts via `ffmpeg` palette workflow to reduce peak memory usage.
- `--cfg-animate` renders a CFG traversal animation using Graphviz layout from an `opt -passes=dot-cfg` DOT file (`--dot-cfg`) and a runtime trace (`--import-trace`).
- `pyproject.toml` includes both `manim` and `manimgl` dependencies, but the current CLI animation path uses Manim Community Edition scenes in `src/llvmanim/present/`.
- Sandbox directories contain experimental scripts and examples and are not used by the package entrypoint.
