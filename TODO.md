# Roadmap (Now / Next / Later)

## Now
- [ ] Add `binop` ingestion support + classify event kinds
- [ ] Define `binop` → animation command mapping in transform layer
- [ ] Add focused tests for `binop` ingest/transform/presentation path

## Next
- [ ] Fix double-pop behavior at transform/trace level (remove renderer guard dependency)
- [ ] Drive rich IR panel from pipeline display model instead of reparsing `.ll`

## Later
- [x] Design and implement CFG animations
- [x] Add CLI flag(s) for CFG animation mode once feature lands
- [x] Add test coverage for non-br terminators (switch, invoke, indirectbr, callbr)
- [x] Deprecate regex edge-extraction fallback in `scene.py` once terminator tests pass (removed entirely)
- [x] Add T/F branch-direction labels to semantic DOT in `graphviz_export.py`

## Issue Dependency Sequence

### Milestone 1 — `binop` foundation
- [ ] Ingest: classify LLVM `binop` opcodes as first-class `EventKind`s
- [ ] Transform: map `binop` events to typed animation actions
	Depends on: Ingest `binop` classification
- [ ] Tests: add end-to-end coverage for `binop` parse → command → render
	Depends on: Ingest + Transform `binop` issues

### Milestone 2 — call-stack correctness + architecture
- [ ] Transform: fix duplicate `pop_stack_frame` generation on conditional branches
- [x] Architecture: move execution-trace builder from presentation to transform layer
- [ ] Architecture: remove `.ll` reparsing in `rich_stack_scene` via pipeline display lines
	Depends on: transform-owned trace/display model

### Milestone 3 — CFG animation productization
- [x] Presentation: add CFG animation scenes from `SceneGraph` nodes/edges
- [x] CLI: expose CFG animation mode and output controls
	Depends on: CFG animation scenes

### Recommended PR Order
- [ ] PR1: Ingest `binop` kinds
- [ ] PR2: Transform `binop` action mapping
- [ ] PR3: `binop` test coverage
- [ ] PR4: double-pop root-cause fix
- [x] PR5: move trace builder to transform
- [ ] PR6: remove rich-scene `.ll` reparsing
- [x] PR7: CFG animations
- [x] PR8: CLI CFG flags + docs

---

# Ingestion Layer
- [x] Parse `.ll` into deterministic `ProgramEventStream` via `llvmlite`
- [x] Classify core event kinds (`alloca`, `load`, `store`, `call`, `ret`, `br`)
- [ ] Cover `binop` family of IR instructions (currently falls into `other`)

---

# Transformation Layer
- [x] Build CFG scene graph (`build_scene_graph`) with block roles + edges
- [x] Translate supported events into `AnimationCommand`s (`build_animation_commands`)
- [ ] Decide on animation actions for `binop`s
- [ ] Resolve double-pop GitHub issue (temporary pop guard exists in `render_stack_model.py`)

---

# Presentation Layer
- [x] Export scene graph JSON (`scene_graph.json`)
- [x] Export Graphviz DOT (and PNG when Graphviz is available)
- [x] Support stack animation modes (`basic` badge + `rich` spotlight)
- [ ] Generate `rich_stack_scene.py` from actual pipeline output instead of reparsing `.ll`
- [ ] Design `binop` animations and implement them in existing scenes
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
- [x] Add broad unit test coverage across ingest / transform / present / cli modules
- [ ] Add focused tests for `binop` classification + command mapping + rendering behavior
- [ ] Open/track issue(s) for remaining architectural TODOs (rich-scene parser dependency, call-trace ownership)
