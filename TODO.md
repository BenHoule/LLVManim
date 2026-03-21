# Roadmap (Now / Next / Later)

## Now
- [ ] Fix double-pop behavior at transform/trace level (remove renderer guard dependency)
- [ ] Drive rich IR panel from pipeline display model instead of reparsing `.ll`
- [x] Wire `enable_ssa` into CLI (`--ir-mode rich-ssa`)

## Next
- [ ] Numeric runtime values in SSA panel (`display_value` swap-point is ready in `ssa_formatting.py`)
- [ ] Improve sandbox CFG animation prototype (see TODOs in `sandbox/manim_CE/cfg_traversal.py`)

## Later / Done
- [x] Add `binop` ingestion support + classify event kinds
- [x] Add `compare` (icmp/fcmp) ingestion support
- [x] Define `binop`/`compare` → animation command mapping in transform layer
- [x] Add focused tests for `binop`/`compare` ingest/transform/presentation path
- [x] SSA bridge panel: 3-column layout (IR Source | SSA Values | Stack) with `enable_ssa=True`
- [x] Design and implement CFG animations
- [x] Add CLI flag(s) for CFG animation mode once feature lands
- [x] Add test coverage for non-br terminators (switch, invoke, indirectbr, callbr)
- [x] Deprecate regex edge-extraction fallback in `scene.py` once terminator tests pass (removed entirely)
- [x] Add T/F branch-direction labels to semantic DOT in `graphviz_export.py`

## Issue Dependency Sequence

### Milestone 1 — `binop`/`compare` foundation ✅
- [x] Ingest: classify LLVM `binop` and `compare` opcodes as first-class `EventKind`s
- [x] Transform: map `binop`/`compare` events to typed animation actions (`animate_binop`, `animate_compare`)
- [x] Tests: end-to-end coverage for `binop`/`compare` parse → command → render

### Milestone 2 — SSA bridge panel ✅
- [x] `RichTraceStep` NamedTuple in `transform/trace.py` with `include_ssa` parameter
- [x] `ssa_formatting.py` module (format_display_value, OP_COLORS, extract_ssa_name, etc.)
- [x] Opt-in 3-column layout in `RichStackSceneSpotlight(enable_ssa=True)`
- [x] Per-frame SSA cleanup on pop (fade + Y-space reclamation)
- [x] Sandbox prototype: `sandbox/manim_CE/register_panel_demo.py`

### Milestone 3 — call-stack correctness + architecture
- [ ] Transform: fix duplicate `pop_stack_frame` generation on conditional branches
	Note: temporary pop guard exists in `render_stack_model.py`
- [x] Architecture: move execution-trace builder from presentation to transform layer
- [ ] Architecture: remove `.ll` reparsing in `rich_stack_scene` via pipeline display lines
	Depends on: transform-owned trace/display model

### Milestone 4 — CFG animation productization ✅
- [x] Presentation: add CFG animation scenes from `SceneGraph` nodes/edges
- [x] CLI: expose CFG animation mode and output controls

### Recommended PR Order
- [x] PR1: Ingest `binop`/`compare` kinds
- [x] PR2: Transform `binop`/`compare` action mapping
- [x] PR3: `binop`/`compare` test coverage
- [ ] PR4: double-pop root-cause fix
- [x] PR5: move trace builder to transform
- [ ] PR6: remove rich-scene `.ll` reparsing
- [x] PR7: CFG animations
- [x] PR8: CLI CFG flags + docs
- [x] PR9: SSA bridge panel (`feature/ssa-bridge-panel`)
- [x] PR10: wire `enable_ssa` into CLI

---

# Ingestion Layer
- [x] Parse `.ll` into deterministic `ProgramEventStream` via `llvmlite`
- [x] Classify core event kinds (`alloca`, `load`, `store`, `call`, `ret`, `br`)
- [x] Classify `binop` family (add, sub, mul, sdiv, udiv, srem, urem, shl, lshr, ashr, and, or, xor, fadd, fsub, fmul, fdiv, frem)
- [x] Classify `compare` family (icmp, fcmp)

---

# Transformation Layer
- [x] Build CFG scene graph (`build_scene_graph`) with block roles + edges
- [x] Translate supported events into `AnimationCommand`s (`build_animation_commands`)
- [x] Map `binop` → `animate_binop`, `compare` → `animate_compare` actions
- [x] `RichTraceStep` and `build_execution_trace(include_ssa=True)` for binop/compare/load trace steps
- [ ] Resolve double-pop GitHub issue (temporary pop guard exists in `render_stack_model.py`)

---

# Presentation Layer
- [x] Export scene graph JSON (`scene_graph.json`)
- [x] Export Graphviz DOT (and PNG when Graphviz is available)
- [x] Support stack animation modes (`basic` badge + `rich` spotlight)
- [x] SSA bridge panel: opt-in 3-column layout via `RichStackSceneSpotlight(enable_ssa=True)`
- [x] `ssa_formatting.py` — shared SSA display formatting (single swap-point for future numeric values)
- [ ] Generate `rich_stack_scene.py` from actual pipeline output instead of reparsing `.ll`
- [x] CFG animations (via `cfg_animation_scene.py` + `dot_layout.py`)
- [x] Add T/F branch labels to semantic DOT export
- [ ] Improve sandbox CFG animation prototype (see TODOs in `sandbox/manim_CE/cfg_traversal.py`)

---

# CLI
- [x] Parse input + run ingest → transform pipeline
- [x] Support `--json`, `--draw`, `--animate`, `--preview`, `--ir-mode`, `--speed`, `--outdir`
- [x] Support animation output format selection (`mp4` / `gif`) with ffmpeg conversion
- [x] Add dedicated CLI flag(s) for CFG animation mode (`--cfg-animate`, `--dot-cfg`)

---

# Other
- [x] Add broad unit test coverage across ingest / transform / present / cli modules (288 tests, 84% coverage)
- [x] Add focused tests for `binop`/`compare` classification + command mapping + rendering behavior
- [x] SSA panel integration tests (trace dispatch, 3-column layout, pop cleanup)
- [ ] Open/track issue(s) for remaining architectural TODOs (rich-scene parser dependency, call-trace ownership)
- [x] Wire `enable_ssa` into CLI (`--ir-mode rich-ssa`)
