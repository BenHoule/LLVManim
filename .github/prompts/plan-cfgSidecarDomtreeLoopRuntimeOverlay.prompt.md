## Plan: CFG Sidecar + Domtree/Loop + Runtime Overlay

Preserve the original `.ll` as the canonical visualization source and introduce analysis sidecars (CFG/domtree/loop/runtime trace) to improve correctness and path highlighting without rewriting or replacing input IR. Implement in three phases: (A) replace regex CFG edge extraction with LLVM-generated CFG artifact import, (B) enrich scene metadata with dominance/loop structure, and (C) overlay runtime taken-path data on top of the unchanged original CFG.

**Guiding Constraints**
- Original IR remains authoritative for displayed instructions, block labels, and scene fidelity.
- LLVM analysis artifacts are sidecars only; they never mutate the source input used for display.
- New capabilities are optional and degrade gracefully (fallback to current behavior if tooling/sidecar missing).
- Existing CLI workflows (`--json`, `--draw`, `--animate`) continue to work unchanged by default.

**Phase A - CFG artifact import (replace regex edge extraction)**
1. Define a sidecar schema for CFG edges and block identity.
   - Include: function name, block name, unique block id, successors/predecessors, optional edge kind.
   - Add schema version and source metadata (tool name, command, timestamp).
   - Dependency: none.
2. Add ingestion utility for CFG sidecar parsing/validation.
   - New module: `src/llvmanim/ingest/cfg_sidecar.py`.
   - Validate required fields and normalize ids to current internal format (`function::block`).
   - Dependency: step 1.
3. Add LLVM tool runner for optional CFG sidecar generation.
   - New module: `src/llvmanim/ingest/llvm_tooling.py`.
   - Support two modes: external pre-existing sidecar and generated sidecar (via `opt -passes=dot-cfg` or equivalent export pipeline in a temp workspace).
   - Never overwrite input IR.
   - Dependency: step 1.
4. Integrate sidecar path into scene graph construction.
   - Extend `build_scene_graph` in `src/llvmanim/transform/scene.py` to accept optional CFG adjacency input.
   - Use sidecar edges when available; fallback to existing `_extract_edges` behavior.
   - Keep `_extract_edges` for compatibility until Phase A complete and stable.
   - Dependency: steps 2–3.
5. Add CLI flags for sidecar ingestion/generation.
   - In `src/llvmanim/cli/main.py`: add optional flags such as `--cfg-sidecar <path>` and `--emit-cfg-sidecar` (exact names to finalize in design review).
   - Preserve default path behavior when flags are absent.
   - Dependency: steps 2–4.
6. Phase A tests and verification.
   - Unit tests: parser validation (missing fields, malformed ids, duplicates).
   - Transform tests: edge source/target fidelity from sidecar; fallback parity with regex extractor.
   - CLI tests: sidecar file missing/invalid handling and fallback behavior.
   - Dependency: all prior steps.

**Phase B - Domtree + loop metadata for richer node semantics**
1. Extend transform models for structural metadata.
   - `src/llvmanim/transform/models.py`: add optional fields on `CFGBlock`/`SceneNode` for `idom`, `dom_depth`, `is_loop_header`, `loop_depth`, `loop_id`, `is_backedge_target`.
   - Ensure defaults preserve backward compatibility.
2. Add metadata sidecar schema and parser.
   - Reuse `cfg_sidecar.py` or add `analysis_sidecar.py` for domtree/loop payload sections.
   - Support partial metadata (e.g., domtree present, loops absent).
3. Build metadata import pipeline.
   - Parse outputs from LLVM analysis commands (`opt` printed analyses or pre-generated machine-readable artifacts).
   - Normalize function/block names to match scene graph ids.
4. Apply metadata during scene graph build.
   - In `src/llvmanim/transform/scene.py`: enrich blocks after base graph creation and before role/hint finalization.
   - Refine role/hint policy to use stronger semantics:
     - loop header hints (`pulse_loop_header` placeholder)
     - backedge-aware merge/branch differentiation
     - dom-depth-informed focus order for traversal animations.
5. Add tests for metadata correctness and non-regression.
   - Unit tests for metadata mapping and id normalization.
   - Scene graph tests for deterministic role/hint outcomes with/without metadata.
   - Golden tests to ensure existing expected roles remain unchanged when metadata absent.

**Phase C - Runtime path overlay on original CFG**
1. Define runtime trace sidecar contract.
   - Include ordered block visits and/or edges traversed, function context, timestamps/sequence ids, and run metadata (input args/env hash).
   - Keep trace independent from original IR text payload.
2. Add runtime trace ingestion module.
   - New module: `src/llvmanim/transform/trace_overlay.py`.
   - Convert trace records into graph overlay primitives (`visited_nodes`, `traversed_edges`, `entry_order`, `termination_reason`).
3. Integrate overlay into transform output.
   - Extend `SceneGraph` with optional overlay section rather than mutating base node/edge sets.
   - Ensure no loss of original CFG structure even when trace includes only one branch path.
4. Wire overlay to presenters.
   - `src/llvmanim/present/graphviz_export.py`: optional style changes for traversed edges/nodes.
   - `src/llvmanim/present/rich_stack_scene.py`: path-highlight cues synchronized with existing stack/IR timeline.
   - Keep feature behind flag to avoid changing baseline visuals.
5. Underflow/error alignment.
   - Keep `signal_stack_underflow` as explicit trace-driven signal for proven runtime inconsistency.
   - Do not infer underflow from static flattened IR.
6. Phase C-alpha verification (complete).
   - 28 new tests: trace_io parse/validate, Graphviz overlay styling, CLI trace flags, double.c fixture.
   - 195 total tests passing, 85.02% coverage, quality-check.sh green.
7. Phase C-beta: SanitizerCoverage trace producer (future).
   - `clang -fsanitize-coverage=trace-pc-guard` with tiny C runtime for ordered block-visit logging.
   - `scripts/produce-trace.sh` - compile + run + output trace JSON.

**XRay investigation findings**
- XRay traces function entry/exit only - NOT basic block visits. Insufficient for block-level path overlay.
- gcov/llvm-cov gives aggregate counts only - no visit order. Insufficient for step-by-step animation.
- SanitizerCoverage chosen as real trace producer (ordered sequences via user callback).
- Hand-crafted fixture (`tests/ingest/testdata/double_trace.json`) bootstraps the overlay pipeline.

**LLVM tooling recommendations by phase**
1. Phase A (CFG extraction)
   - llvmlite API only for typed edge extraction (no `opt` subprocess needed).
2. Phase B (domtree/loop metadata)
   - Use `opt` analyses equivalent to dominance and loop info, then parse into sidecar records.
   - Add caching to avoid repeated expensive subprocess calls for identical IR content.
3. Phase C (runtime path)
   - SanitizerCoverage (`-fsanitize-coverage=trace-pc-guard`) for ordered block-visit traces.
   - Hand-crafted fixtures for development bootstrapping.
   - Merge trace by normalized function/block ids into original CFG model.

**Detailed file map (current)**
- `src/llvmanim/ingest/cfg_edge_io.py` - CFG edge JSON I/O.
- `src/llvmanim/ingest/analysis_metadata_io.py` - domtree/loop metadata JSON I/O.
- `src/llvmanim/ingest/trace_io.py` - trace overlay JSON I/O (load_trace, save_trace, TraceIOError).
- `src/llvmanim/transform/scene.py` - accept sidecar edges; metadata enrichment hooks.
- `src/llvmanim/transform/models.py` - metadata + overlay fields (TraceOverlay, BlockMetadata).
- `src/llvmanim/cli/main.py` - sidecar + trace flags + graceful fallback flows.
- `src/llvmanim/present/graphviz_export.py` - overlay-aware style emission.
- `src/llvmanim/present/rich_stack_scene.py` - path overlay playback integration.
- `tests/ingest/` - sidecar parse/validation tests.
- `tests/transform/test_scene_graph.py` - sidecar edge and metadata-driven role/hint tests.
- `tests/test_pipeline.py` - end-to-end parity tests with and without sidecars.
- `tests/cli/test_main.py` - sidecar CLI contract/failure tests.
- `tests/present/` - overlay rendering behavior tests (initially non-visual structural assertions).

**Rollout strategy**
1. PR1: Sidecar schemas + parser + unit tests.
2. PR2: Scene graph consumes sidecar edges + fallback parity tests.
3. PR3: CLI flags and artifact generation plumbing.
4. PR4: Domtree/loop model extension and metadata import.
5. PR5: Metadata-informed role/hint logic + regression tests.
6. PR6: Runtime trace sidecar model + overlay data path.
7. PR7: Graphviz overlay output.
8. PR8: Rich scene overlay playback (minimal version).
9. PR9: Underflow/error visualization stub upgrade (ghost/red flash implementation).

**Verification checklist per phase**
1. Functional parity: default workflow output unchanged when no sidecar flags are used.
2. Determinism: same input + same sidecar => stable scene graph and overlay outputs.
3. Robustness: malformed sidecar paths fail with actionable messages and fallback when possible.
4. Performance: sidecar-enabled pipeline does not exceed agreed runtime overhead budget.
5. Architecture: import-linter boundaries preserved (ingest/transform stay decoupled from present).

**Risks and mitigations**
1. Name mismatch between LLVM artifacts and llvmlite block names.
   - Mitigation: canonical id normalization and mapping diagnostics.
2. Tooling portability (`opt` availability/version differences).
   - Mitigation: version guard + feature detection + fallback to current regex extraction.
3. Excessive complexity in initial overlay rendering.
   - Mitigation: ship structural overlay first (DOT/JSON), then animate incrementally.
4. Test brittleness from text-output parsing.
   - Mitigation: prefer stable sidecar schema and parser fixtures over raw text assertions.

**Scope boundaries**
- Included: sidecar-based CFG correctness, metadata enrichment, runtime overlay support.
- Excluded (for now): replacing llvmlite ingest, full interactive debugger UX, broad GUI work.
- Deferred by design: branch-value solving from static IR alone beyond what sidecars provide.

**Immediate next implementation starting point**
1. Create sidecar schema doc + parser tests (Phase A step 1–2).
2. Add optional `build_scene_graph(..., cfg_sidecar=...)` API.
3. Preserve all current behavior when sidecar is not provided.
