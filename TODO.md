# Roadmap (Now / Next / Later)

## Now
- [ ] Add `binop` ingestion support + classify event kinds
- [ ] Define `binop` → animation command mapping in transform layer
- [ ] Add focused tests for `binop` ingest/transform/presentation path

## Next
- [ ] Fix double-pop behavior at transform/trace level (remove renderer guard dependency)
- [ ] Move call-trace ownership out of presentation (`rich_stack_scene`) into transform pipeline
- [ ] Drive rich IR panel from pipeline display model instead of reparsing `.ll`

## Later
- [ ] Design and implement CFG animations
- [ ] Add CLI flag(s) for CFG animation mode once feature lands

## Issue Dependency Sequence

### Milestone 1 — `binop` foundation
- [ ] Ingest: classify LLVM `binop` opcodes as first-class `EventKind`s
- [ ] Transform: map `binop` events to typed animation actions
	Depends on: Ingest `binop` classification
- [ ] Tests: add end-to-end coverage for `binop` parse → command → render
	Depends on: Ingest + Transform `binop` issues

### Milestone 2 — call-stack correctness + architecture
- [ ] Transform: fix duplicate `pop_stack_frame` generation on conditional branches
- [ ] Architecture: move execution-trace builder from presentation to transform layer
	Depends on: double-pop fix (or lands together in same PR)
- [ ] Architecture: remove `.ll` reparsing in `rich_stack_scene` via pipeline display lines
	Depends on: transform-owned trace/display model

### Milestone 3 — CFG animation productization
- [ ] Presentation: add CFG animation scenes from `SceneGraph` nodes/edges
- [ ] CLI: expose CFG animation mode and output controls
	Depends on: CFG animation scenes

### Recommended PR Order
- [ ] PR1: Ingest `binop` kinds
- [ ] PR2: Transform `binop` action mapping
- [ ] PR3: `binop` test coverage
- [ ] PR4: double-pop root-cause fix
- [ ] PR5: move trace builder to transform
- [ ] PR6: remove rich-scene `.ll` reparsing
- [ ] PR7: CFG animations
- [ ] PR8: CLI CFG flags + docs

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
- [ ] CFG animations

---

# CLI
- [x] Parse input + run ingest → transform pipeline
- [x] Support `--json`, `--draw`, `--animate`, `--preview`, `--ir-mode`, `--speed`, `--outdir`
- [x] Support animation output format selection (`mp4` / `gif`) with ffmpeg conversion
- [ ] Add dedicated CLI flag(s) for CFG animation mode (once CFG animations exist)

---

# Other
- [x] Add broad unit test coverage across ingest / transform / present / cli modules
- [ ] Add focused tests for `binop` classification + command mapping + rendering behavior
- [ ] Open/track issue(s) for remaining architectural TODOs (rich-scene parser dependency, call-trace ownership)
