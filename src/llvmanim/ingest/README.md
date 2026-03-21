# llvmanim.ingest

Ingestion layer: reads a `.ll` file and produces a typed `ProgramEventStream`.

## Public API

```python
from llvmanim.ingest import parse_module_to_events  # file path → stream
from llvmanim.ingest import parse_ir_to_events       # IR text  → stream
```

- `parse_module_to_events(path: str) → ProgramEventStream` — reads the file at
  `path`, delegates to `parse_ir_to_events`.
- `parse_ir_to_events(llvm_ir: str, source_path: str) → ProgramEventStream` —
  parses IR text directly via `llvmlite`, useful for in-memory IR (e.g. tests).

## Data Model

```
ProgramEventStream
├── source_path: str
└── events: list[IREvent]
      ├── function_name: str
      ├── block_name: str
      ├── opcode: str
      ├── text: str             (full instruction string)
      ├── kind: EventKind       (see below)
      ├── index_in_function: int
      ├── debug_line: int | None
      └── operands: list[str]
```

`ProgramEventStream` also carries:

- `cfg_edges: list[CFGEdge]` — populated by the ingest layer for all
  terminator types (br, switch, invoke, etc.) via llvmlite.  These typed
  edges are consumed directly by the transform layer's `build_scene_graph`.
- `display_lines: dict[str, list[str]]` — per-function cleaned IR source
  lines built at ingest time by `build_display_lines`.  The presentation
  layer reads these directly for IR source panels, avoiding a second file
  read.

`EventKind` is one of: `alloca`, `load`, `store`, `binop`, `compare`, `call`, `ret`, `br`, `other`.

Arithmetic opcodes (`add`, `sub`, `mul`, `sdiv`, …) are tagged `binop`.
Comparison opcodes (`icmp`, `fcmp`) are tagged `compare`.
Instructions whose opcode does not appear in the classification table (e.g.
`getelementptr`, `phi`) are tagged `other` and are typically skipped by the
transform layer.

## Files

| File | Purpose |
|---|---|
| `llvm_events.py` | `parse_ir_to_events` and `parse_module_to_events` |
| `cfg_edge_io.py` | Import/export CFG edges as JSON sidecars |
| `trace_io.py` | Import/export runtime path traces as JSON sidecars |
| `analysis_metadata_io.py` | Import/export domtree/loop analysis metadata as JSON |
| `display_lines.py` | `build_display_lines` and `clean_ir_line` — IR text → display-ready lines |
| `dot_layout.py` | Parse `.dot` files from `opt -passes=dot-cfg` into `DotLayout` for CFG animation |
| `LEGACY_ir_helpers.py` | Superseded helpers; kept for reference |
| `LEGACY_llvmparser.py` | Superseded parser; kept for reference |
| `LEGACY_ophandlers.py` | Superseded op handlers; kept for reference |
