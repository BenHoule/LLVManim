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

`EventKind` is one of: `alloca`, `load`, `store`, `call`, `ret`, `br`, `other`.

Instructions whose opcode does not appear in the classification table (e.g.
`icmp`, `add`, `getelementptr`) are tagged `other` and are typically skipped
by the transform layer.

## Files

| File | Purpose |
|---|---|
| `llvm_events.py` | `parse_ir_to_events` and `parse_module_to_events` |
| `LEGACY_ir_helpers.py` | Superseded helpers; kept for reference |
| `LEGACY_llvmparser.py` | Superseded parser; kept for reference |
| `LEGACY_ophandlers.py` | Superseded op handlers; kept for reference |
