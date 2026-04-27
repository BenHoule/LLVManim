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
  - `--ir-mode rich-ssa`: 3-column layout (IR Source | SSA Values | Stack) showing binop/compare/load results
- `--color-scheme dark|light`: switch the animation color scheme (dark = default black background; light = white background)
- `ssa_formatting.py`: shared SSA display formatting with a single swap-point for future numeric runtime values
- `RichTraceStep` and `build_execution_trace(include_ssa=True)` for binop/compare/load trace steps
- Render CFG traversal animations (`--cfg-animate`) using DOT-derived layout from `opt -passes=dot-cfg`
- Auto-derive a static CFG trace when `--import-trace` is not provided (with interactive confirmation, skippable via `-y`)

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
| `tests/render/` | `integration` (+ `contract` for `test_exports.py`) |
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

## Generating Charts and Images

All charts are written to `docs/metrics/`. Running `uv sync --dev` (see [Setup And Validation](#setup-and-validation)) installs every required library — `matplotlib` is pulled in as a transitive dependency of `manimgl`.

### Static metrics charts (01–04)

Coverage, test count, lines-of-code, and size-vs-coverage charts. Data is hard-coded in the script and requires no live pipeline execution.

```bash
uv run python docs/metrics/generate_metrics.py
```

| File | Description |
|---|---|
| `docs/metrics/01_coverage_by_module.png` | Statement coverage percentage per module |
| `docs/metrics/02_tests_per_module.png` | Test count breakdown by module |
| `docs/metrics/03_lines_of_code.png` | Lines of code per module |
| `docs/metrics/04_size_vs_coverage.png` | LOC vs. coverage scatter |

### Performance scaling charts (05–10)

Benchmarks the live pipeline against synthetically generated IR. Runs the actual `llvmanim` ingest and transform functions — no Manim rendering required.

```bash
uv run python docs/metrics/generate_perf_metrics.py
```

| File | Description |
|---|---|
| `docs/metrics/05_parse_scaling.png` | `parse_module_to_events` time vs. instruction count |
| `docs/metrics/06_scene_graph_cfg_scaling.png` | `build_scene_graph` (CFG mode) time vs. block count |
| `docs/metrics/07_trace_scaling.png` | `derive_cfg_trace` time vs. block count |
| `docs/metrics/08_scene_graph_stack_scaling.png` | `build_scene_graph` (stack mode) time vs. call depth |
| `docs/metrics/09_memory_scaling.png` | Peak memory (ingest + build) vs. IR size |
| `docs/metrics/10_pipeline_stage_latency.png` | Per-stage latency breakdown |

### Regenerate all charts at once

```bash
uv run python docs/metrics/generate_metrics.py && uv run python docs/metrics/generate_perf_metrics.py
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
- `--animate`: render stack animation video via Manim
- `--preview`: open rendered animation in viewer (implies animation render)
- `--ir-mode {basic,rich,rich-ssa}`: choose animation style (default: `basic`; `rich-ssa` enables 3-column SSA panel)
- `--speed <float>`: animation speed multiplier (default: `1.0`)
- `--format {mp4,gif}`: animation output format (default: `mp4`)
- `--gif-fps <int>`: GIF conversion FPS when `--format gif` (default: `12`)
- `--gif-width <int>`: GIF conversion width in px when `--format gif` (default: `960`)
- `--outdir <path>`: output directory (default: current directory)
- `-n` / `--name <name>`: base name for output artifacts (default: stem of input file)
- `--cfg-animate`: render a CFG traversal animation (requires `--dot-cfg`; auto-derives trace if `--import-trace` is not given)
- `-y` / `--yes`: skip confirmation prompts (e.g. auto-derive trace)
- `--dot-cfg <path>`: path to a `.dot` file from `opt -passes=dot-cfg` for CFG layout
- `--import-cfg-edges <path>`: load CFG edges from a JSON file instead of extracting them from IR
- `--export-cfg-edges <path>`: write extracted CFG edges to a JSON file
- `--import-analysis-metadata <path>`: load domtree/loop analysis metadata from a JSON file
- `--export-analysis-metadata <path>`: write analysis metadata to a JSON file
- `--import-trace <path>`: load a runtime path trace from a JSON file for overlay visualization
- `--export-trace <path>`: write the trace overlay to a JSON file
- `--color-scheme {dark,light}`: animation color scheme (default: `dark` — black background; `light` — white background)
- `--C`: treat the input file as a `C` source file instead of LLVM textual IR and compile it to LLVM IR automatically

### Environment Variables
LLVManim has to use external tools to perform certain operations and therefore needs a way to locate these tools. 
For any of the external tools LLVManim uses, you can specify the environment variable with the tool's name in `SCREAMING_SNAKE_CASE`
to provide a path to the tool's binary.

By default LLVMAnim searches for the following external tools in the directories listed in the `PATH` environment variable if their corresponding
environment variable is not set:
- `ffmpeg`
- `dot`

LLVManim also needs to use some of LLVM's binary tools when compiling a C source file, specifially `clang` and `opt`. 
Since these tools may have non-standard locations, you can specify a convenient fallback search directory
for these tools in the `LLVM_BIN_DIR` environment variable. 

LLVManim has a special case search for LLVM tools on Linux since it is common to have multiple versions of LLVM installed and therefore the tools
may not be on PATH. LLVManim attempts to search `/usr/lib/llvm/bin` and then tries to find the latest LLVM version from the candidates in `/usr/lib/llvm-*/bin` 
before falling back to to `PATH`. You can disable this special case search by setting the `NO_LLVM_DEFAULT_SEARCH` environment variable to any value.

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

Render CFG traversal animation with auto-derived trace:

```bash
uv run llvmanim tests/ingest/testdata/double.ll --cfg-animate --dot-cfg .main.dot -y --outdir llvmanim_out
```

## Pipeline (Current Implementation)

```
┌────────────────────────────────────────────────────────────────┐
│                           CLI (cli/)                           │
│  uv run llvmanim input.ll [--json] [--draw] [--animate]        │
│                     [--preview] [--ir-mode basic|rich|rich-ssa]│
│                           [--speed N] [--format mp4|gif]       │
│                           [--color-scheme dark|light]          │
│                           [--cfg-animate] [--dot-cfg PATH]     │
│                           [--import-trace PATH] [-y]           │
│                           [-n NAME] [--import-cfg-edges PATH]  │
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
│  build_display_lines(ir_text) → dict[str, list[str]]            │
│                                                                 │
│  • llvmlite: parse module, walk functions/blocks/instrs         │
│  • Typed CFG edges from all terminator operands (br, switch,    │
│    invoke, indirectbr, callbr) with T/F labels on cond. br      │
│  • Each IREvent carries: function_name, block_name, opcode,     │
│    text, kind, index_in_function, debug_line, operands          │
│  • kind ∈ {alloca,load,store,binop,compare,call,ret,br,other}   │
│  • display_lines: per-function cleaned IR for rich-scene panels │
└──────────────┬──────────────────────────────────────────────────┘
               │ ProgramEventStream
               ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Transform (transform/)                      │
│                                                                 │
│  build_scene_graph(stream, mode="cfg",            							│
│      analysis_metadata=...) → SceneGraph          							│
│  build_scene_graph(stream, mode="stack",         								│
│      include_ssa=...) → SceneGraph                							│
│  derive_cfg_trace(graph, function) → TraceOverlay 							│
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
│  Export (render/)    │ │  Animation (render/)                    │
│                      │ │                                         │
│  --json →            │ │  --animate / --preview                  │
│    scene_graph.json  │ │    --ir-mode basic → StackRenderer      │
│                      │ │    --ir-mode rich →                     │
│  --draw →            │ │      StackRenderer (2-col IR+stack)     │
│    cfg_main.dot      │ │    --ir-mode rich-ssa →                 │
│    cfg_main.png      │ │      StackRenderer (3-col IR+SSA+stack) │
│    (needs graphviz)  │ │  --cfg-animate →                        │
│    (needs graphviz)  │ │    CFGRenderer (DOT layout +            │
│                      │ │    trace overlay traversal)             │
└──────────────────────┘ └─────────────────────────────────────────┘
```

## Notes

- DOT export does not require system Graphviz binaries; PNG export does.
- GIF output renders MP4 first and then converts via `ffmpeg` palette workflow to reduce peak memory usage.
- `--cfg-animate` renders a CFG traversal animation using Graphviz layout from an `opt -passes=dot-cfg` DOT file (`--dot-cfg`). If `--import-trace` is not provided, a static trace is auto-derived from the CFG edges (with an interactive confirmation prompt, skippable via `-y`).
- `pyproject.toml` includes both `manim` and `manimgl` dependencies, but the current CLI animation path uses Manim Community Edition scenes in `src/llvmanim/render/`.
- Sandbox directories contain experimental scripts and examples and are not used by the package entrypoint.
