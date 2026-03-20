## Plan: CFG Sidecar + Domtree/Loop + Runtime Overlay

> **Status:** Phases A, B, and C are **complete**. All items below have been implemented and merged to `main`. This document is retained for historical reference.

Preserve the original `.ll` as the canonical visualization source and introduce analysis sidecars (CFG/domtree/loop/runtime trace) to improve correctness and path highlighting without rewriting or replacing input IR. Implement in three phases: (A) replace regex CFG edge extraction with LLVM-generated CFG artifact import, (B) enrich scene metadata with dominance/loop structure, and (C) overlay runtime taken-path data on top of the unchanged original CFG.

**Guiding Constraints**
- Original IR remains authoritative for displayed instructions, block labels, and scene fidelity.
- LLVM analysis artifacts are sidecars only; they never mutate the source input used for display.
- New capabilities are optional and degrade gracefully (fallback to current behavior if tooling/sidecar missing).
- Existing CLI workflows (`--json`, `--draw`, `--animate`) continue to work unchanged by default.

**Phase A — CFG artifact import (replace regex edge extraction)**
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

**Phase B — Domtree + loop metadata for richer node semantics**
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

**Phase C — Runtime path overlay on original CFG**
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
6. Phase C verification.
   - Deterministic fixtures with known branch outcomes and expected overlays.
   - CLI contract tests for missing trace sidecar (fallback to no overlay).
   - End-to-end test asserting original CFG unchanged while overlay reflects path.

**LLVM tooling recommendations by phase**
1. Phase A (CFG extraction)
   - Use `opt` CFG emit path in sandboxed temp dir (`dot-cfg` style artifacts) and convert to normalized sidecar.
   - Keep llvmlite ingestion unchanged for event parsing.
2. Phase B (domtree/loop metadata)
   - Use `opt` analyses equivalent to dominance and loop info, then parse into sidecar records.
   - Add caching to avoid repeated expensive subprocess calls for identical IR content.
3. Phase C (runtime path)
   - Prefer runtime instrumentation sidecars (e.g., LLVM-XRay/profiling traces) for executed-path certainty.
   - Merge trace by normalized function/block ids into original CFG model.

**Detailed file map (planned)**
- `src/llvmanim/ingest/cfg_sidecar.py` (new) — sidecar schemas + parsers + validators.
- `src/llvmanim/ingest/llvm_tooling.py` (new) — subprocess orchestration for analysis artifact generation.
- `src/llvmanim/transform/scene.py` — accept sidecar edges; metadata enrichment hooks.
- `src/llvmanim/transform/models.py` — optional metadata + overlay fields.
- `src/llvmanim/transform/trace_overlay.py` (new) — runtime overlay construction.
- `src/llvmanim/cli/main.py` — optional sidecar flags + graceful fallback flows.
- `src/llvmanim/present/graphviz_export.py` — overlay-aware style emission.
- `src/llvmanim/present/rich_stack_scene.py` — path overlay playback integration.
- `tests/ingest/` — sidecar parse/validation tests.
- `tests/transform/test_scene_graph.py` — sidecar edge and metadata-driven role/hint tests.
- `tests/test_pipeline.py` — end-to-end parity tests with and without sidecars.
- `tests/cli/test_main.py` — sidecar CLI contract/failure tests.
- `tests/present/` — overlay rendering behavior tests (initially non-visual structural assertions).

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
---
## Plan Review: Issues Found
### Critical
1. **Missing prerequisite:** `build_execution_trace` relocation. This function lives in _rich_stack_scene.py:150_ — the presentation layer. It reparses IR, simulates a call tree, and builds `TraceStep` tuples. TODO.md explicitly flags this for relocation. Phase C (and even Phase A's cleaner pipeline) depends on the trace living in the transform layer. The original plan ignores this entirely.

2. **Over-engineered Phase A:** opt subprocess unnecessary. The codebase already uses `llvmlite.binding` which provides typed iteration over module.functions → func.blocks → block.instructions → instr.operands. The regex in `_extract_branch_targets_from_text` can be replaced by extracting successor blocks directly from llvmlite's API during ingestion — no opt subprocess, no DOT parsing, no new llvm_tooling.py module needed for basic CFG edges. This eliminates a portability risk and a whole module.

3. Import-linter config doesn't exist. The quality gate runs `lint-imports` (_quality-check.sh:15_) but there's no `[tool.import-linter]` section in *pyproject.toml*. The plan says "import-linter boundaries preserved" but there's nothing to preserve yet. This must be set up first.

### Significant
4. `_extract_edges` only handles br. LLVM IR also has switch, invoke, indirectbr, and callbr terminators with block successors. The original plan doesn't mention broadening terminator coverage — the llvmlite approach would naturally handle all of them.

5. 9-PR rollout is excessive for a solo project. Recommend 4–5 PRs aligned with phases, not 9 micro-PRs.

6. Sidecar format never specified. JSON is the obvious choice given `export_scene_graph_json` exists, but the plan never commits to a format.

7. `build_ir_registry()` in *rich_stack_scene.py* also reparses .ll. This is separate from build_execution_trace but the same category of architectural debt. The plan should note it.

8. The xray ELF binary in the repo root appears to be an XRay-instrumented binary relevant to Phase C. Not mentioned in the plan.

### Minor
9. `_extract_branch_targets_from_text` regex won't match quoted block names (e.g., %"block name"). The llvmlite API approach fixes this for free.

10. No caching strategy for Phase A. (Mentioned for Phase B but not A.)

11. Phase heading says "replace regex" but steps say "fallback to regex." Mixed messaging.
---
## Improved Plan: CFG Sidecar + Domtree/Loop + Runtime Overlay
Preserve the original .ll as canonical visualization source. Introduce typed CFG edges from llvmlite, structural metadata sidecars, and runtime trace overlay — all without mutating input IR.

### Guiding Constraints

- Original IR remains authoritative for displayed instructions, block labels, and scene fidelity.
- Analysis artifacts are sidecars; they never mutate the source input.
- New capabilities degrade gracefully (fallback to current behavior when absent).
- Existing CLI workflows (`--json`, `--draw`, `--animate`) continue unchanged by default.
---
### Phase 0 — Foundation (prerequisite)
#### Step 0.1: Add import-linter configuration
- Add `[tool.import-linter]` contracts to *pyproject.toml* enforcing ingest → transform → present layering.
- Contracts: ingest cannot import transform/present; transform cannot import present; present can depend on both.
- Verify *quality-check.sh* passes with the new boundaries.
- Dependency: none.

#### Step 0.2: Relocate `build_execution_trace` to transform layer
- Move `build_execution_trace()`, `_extract_callee()`, `_CALLEE_RE`, and the `TraceStep` type from _rich_stack_scene.py:127-183_ to a new module *src/llvmanim/transform/trace.py*.
- Re-export from transform's *__init__.py*.
- Update imports in *rich_stack_scene.py* (both `RichStackSceneBadge` and `RichStackSceneSpotlight`).
- Move existing tests from *test_rich_stack_scene_helpers.py* into *tests/transform/test_trace.py*.
- Verify: import-linter passes, all existing tests pass, no behavior change.
- Dependency: step 0.1.


#### Step 0.3: Note build_ir_registry reparse debt
- `build_ir_registry` in the present layer reparses the .ll file for IR display lines. Document as future work — not blocking but should eventually be pipeline-driven.
- Dependency: none (documentation only).

#### Relevant files:
*pyproject.toml* — add import-linter contracts
*rich_stack_scene.py* — extract trace builder
*src/llvmanim/transform/trace.py* (new) — relocated trace builder
*test_rich_stack_scene_helpers.py* — move trace tests

### Phase A — Typed CFG edge extraction (replace regex)
#### Step A.1: Extract CFG edges from llvmlite API during ingestion
- In *llvm_events.py*, `extend parse_ir_to_events` to also produce a list of `CFGEdge` objects by iterating `block.instructions[-1].operands` for terminators (`br`, `switch`, `invoke`, `indirectbr`, `callbr`).
- Add a `block_edges` field (or separate return value) to `ProgramEventStream`, or create a new `CFGAdjacency` dataclass in _models.py_.
- This replaces the regex in `_extract_branch_targets_from_text` with llvmlite's typed operand inspection. Handles all terminator types and quoted block names for free.
- Dependency: none.

#### Step A.2: Update scene graph to consume typed edges
- Modify `build_scene_graph` in *scene.py* to accept optional `cfg_edges: list[CFGEdge] | None` parameter.
- When provided, use them directly instead of calling `_extract_edges`.
- Keep `_extract_edges` temporarily as fallback (remove once A is stable).
- Wire `parse_module_to_events` → typed edges → `build_scene_graph` in CLI main.
- Dependency: step A.1.

#### Step A.3: Add optional JSON sidecar import/export
- New module: *src/llvmanim/ingest/cfg_sidecar.py*.
- Define JSON schema: `{ "version": 1, "source": "...", "functions": [{ "name": "...", "blocks": [{ "name": "...", "id": "...", "successors": [...], "predecessors": [...] }] }] }`.
- `load_cfg_sidecar(path) -> list[CFGEdge]` — parse + validate.
- `save_cfg_sidecar(edges, path)` — serialize for external tooling.
- Add CLI flags `--cfg-sidecar <path>` (import) and `--emit-cfg-sidecar` (export from llvmlite).
- Dependency: step A.1.

#### Step A.4: Phase A tests
- Unit: llvmlite edge extraction covers br, switch, conditional br, unconditional br. Edge-dedup preserved.
- Unit: sidecar parser rejects malformed JSON, missing fields, unknown version.
- Integration: scene graph built with typed edges matches scene graph from regex fallback (parity).
- Contract: CLI --cfg-sidecar with bad path gives actionable error.
- Dependency: steps A.1–A.3.

#### Relevant files:
*llvm_events.py* — typed edge extraction
*models.py* — optional CFGAdjacency or edge list on stream
*scene.py* — accept optional edges, retain _extract_edges as fallback
*src/llvmanim/ingest/cfg_sidecar.py (new)* — JSON sidecar I/O
*main.py* — sidecar CLI flags
*test_scene_graph.py* — parity tests

### Phase B — Domtree + loop metadata enrichment
#### Step B.1: Extend models with structural metadata
- Add optional fields to `CFGBlock` in *models.py*: `idom: str | None = None`, `dom_depth: int = 0`, `is_loop_header: bool = False`, `loop_depth: int = 0`, `loop_id: str | None = None`, `is_backedge_target: bool = False`.
- Defaults preserve backward compat.
- Dependency: Phase A complete.

#### Step B.2: Metadata sidecar schema and parser
- Extend *cfg_sidecar.py* or add *src/llvmanim/ingest/analysis_sidecar.py*.
- Support partial metadata (domtree only, loops only, or both).
- Parse from JSON sidecar (externally generated from opt printed analyses).
- Dependency: step B.1.

#### Step B.3: Metadata-aware role/hint assignment
- In scene.py, enhance `_assign_roles` and `_animation_hint_for_block` to use metadata when available: loop headers get `pulse_loop_header`, backedge targets get specialized hints, dom-depth informs focus ordering.
No change when metadata absent (backward compat).
Dependency: step B.2.

#### Step B.4: Phase B tests
- Unit: metadata mapping, id normalization, partial metadata handling.
- Golden: existing role assignments unchanged when metadata absent.
- Integration: scene graph with metadata produces richer hints.
- Dependency: steps B.1–B.3.


#### Relevant files:
*models.py* — metadata fields
*src/llvmanim/ingest/analysis_sidecar.py* (new or extend cfg_sidecar.py) — metadata parser
*scene.py* — metadata-informed role/hint

### Phase C — Runtime path overlay

#### XRay Investigation Findings
- The `xray` ELF binary in the repo (316 KB, compiled from `double.c` with `-fxray-instrument`) was investigated.
- **Critical finding:** XRay traces function entry/exit only — NOT basic block visits. Function-level granularity is insufficient for block-level path overlay.
- **gcov/llvm-cov** gives per-block execution counts but NOT visit order (aggregated counters only). Insufficient for step-by-step animation.
- **SanitizerCoverage** (`-fsanitize-coverage=trace-pc-guard`) provides exact block/edge visit sequences via user callback — suitable for ordered trace production.
- **Decision:** SanitizerCoverage is the real trace producer (Phase C-beta). Hand-crafted fixture bootstraps the overlay pipeline first (Phase C-alpha).

#### Step C.1: Trace JSON schema + hand-crafted fixture ✅
- JSON schema: `{ "version": 1, "source": "...", "entry_order": [...], "visited_nodes": [...], "traversed_edges": [[src, tgt], ...], "termination_reason": "ret" }`
- `entry_order` is ordered block visit sequence (with repeats for loops).
- `visited_nodes` and `traversed_edges` optional — derived from `entry_order` when absent.
- Hand-crafted fixture: `tests/ingest/testdata/double_trace.json` with 7-iteration loop path.
- Dependency: Phase A complete (stable block ids).

#### Step C.2: Trace I/O module ✅
- New module: *src/llvmanim/ingest/trace_io.py*.
- `load_trace(path) -> TraceOverlay` — parse + validate JSON, derive visited_nodes/traversed_edges when absent.
- `save_trace(overlay, path)` — serialize for round-trip.
- `TraceIOError` for malformed input.
- Follows same pattern as `cfg_edge_io.py` and `analysis_metadata_io.py`.
- Dependency: step C.1.

#### Step C.3: Overlay-aware Graphviz export ✅
- *graphviz_export.py*: when `graph.overlay` is set, visited nodes get green fill (`#d4edda`), unvisited nodes get gray fill (`#e0e0e0`), traversed edges get bold blue (`#0056b3`, penwidth 2.0), non-traversed edges get gray dashed.
- Both `export_cfg_dot` and `export_cfg_png` updated.
- No change when overlay absent (backward compat).
- Dependency: step C.2.

#### Step C.4: CLI flags ✅
- `--import-trace <path>` — load trace JSON into `SceneGraph.overlay`.
- `--export-trace <path>` — export overlay to JSON file.
- Graceful handling: missing file → error; no overlay to export → warning.
- Dependency: steps C.2–C.3.

#### Step C.5: Phase C-alpha tests ✅
- 28 new tests: trace_io parse/validate (17), Graphviz overlay styling (4), CLI trace flags (6), double.c fixture (1).
- 195 total tests passing, 85.02% coverage.
- `quality-check.sh` fully green.
- Dependency: steps C.1–C.4.

#### Step C.6: SanitizerCoverage trace producer (future)
- `clang -fsanitize-coverage=trace-pc-guard double.c -o double_sancov`
- Tiny C runtime logging block entry in LLVManim trace JSON format.
- `scripts/produce-trace.sh` — compile + run + output trace JSON.
- Dependency: steps C.1–C.5 (pipeline must work with fixtures first).

#### Relevant files:
- *src/llvmanim/ingest/trace_io.py* — trace JSON I/O (load_trace, save_trace, TraceIOError)
- *models.py* — `TraceOverlay` type, optional field on `SceneGraph`
- *graphviz_export.py* — overlay-aware styles (visited=green, traversed=bold blue)
- *main.py* — `--import-trace` / `--export-trace` flags
- *tests/ingest/testdata/double_trace.json* — hand-crafted fixture

### Rollout (4 PRs)
PR |	Content |	Depends on
|---|---|---|
| PR1	| Phase 0: import-linter config + trace builder relocation | — |
| PR2	| Phase A: llvmlite typed edges + sidecar I/O + CLI flags	| PR1 |
| PR3	| Phase B: metadata model + sidecar parser + enriched hints	| PR2 |
| PR4	| Phase C: trace overlay model + presenter integration + underflow alignment | PR2 (independent of PR3) |

### Verification (per phase)
- *quality-check.sh* passes (Ruff, Pyright, import-linter, pytest 80%+ coverage).
- Functional parity: default workflow output unchanged when no sidecar flags used.
- Determinism: same input + same sidecar → stable scene graph and overlay.
- Robustness: bad sidecar paths fail with actionable errors.

### Key Decisions
- **llvmlite API only** for CFG edge extraction (no `opt` subprocess in Phase A).
- **No `llvm_tooling.py` module** needed for Phase A — removed from plan.
- **B before C** phase ordering preserved per your preference.
- **`build_execution_trace` relocation** is prerequisite Step 0.
- **JSON** as the sidecar format throughout.
- **`opt` subprocess** deferred to Phase B/C only if needed for domtree/loop/trace generation.
- **SanitizerCoverage** (`-fsanitize-coverage=trace-pc-guard`) chosen as real trace producer for Phase C (ordered block visits). gcov rejected (aggregate counts only). XRay rejected (function-level only).
- **Consumer before producer**: overlay pipeline built against hand-crafted fixture first.
- **xray binary**: 316 KB artifact with no consumer — recommend removal or `.gitignore`.

### Risks and Mitigations
1. **llvmlite operand API may not expose block targets cleanly** — Mitigation: investigate `str(op)` output for `br` operands in a spike; fallback to existing regex if llvmlite API is insufficient.
2. **Name mismatch between sidecar block ids and internal ids** — Mitigation: canonical `function::block` normalization and mapping diagnostics.
3. **Phase C trace source resolved** — SanitizerCoverage chosen. Hand-crafted fixtures bootstrap development. Real instrumentation deferred to Phase C-beta.
