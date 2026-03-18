# llvmanim.cli

Command-line interface for LLVManim.

## Entry Point

```bash
uv run llvmanim [input.ll] [flags]
```

Equivalent invocations:

```bash
python -m llvmanim [input.ll] [flags]
python -m llvmanim.cli [input.ll] [flags]
```

Default input when none is supplied: `tests/ingest/testdata/double.ll`.

## Flags

| Flag | Default | Description |
|---|---|---|
| `input` (positional) | `tests/ingest/testdata/double.ll` | Path to `.ll` file |
| `--json` | off | Write `scene_graph.json` to `--outdir` |
| `--draw` | off | Write `cfg_main.dot` (and `cfg_main.png` if Graphviz binaries are present) |
| `--animate` | off | Render stack animation video via Manim |
| `--preview` | off | Render and open video in viewer (implies `--animate`) |
| `--ir-mode {basic,rich}` | `basic` | Animation display mode |
| `--speed FLOAT` | `1.0` | Animation speed multiplier |
| `--outdir PATH` | `.` | Output directory (created if absent) |

## Animation Modes

- `basic` — stack-only layout; arriving cells flash yellow then settle to white (`RichStackSceneBadge`)
- `rich` — two-column layout with full IR source on the left and a moving yellow cursor; stack on the right (`RichStackSceneSpotlight`)

## Exit Codes

- `0` — success
- `1` — input file not found

## Files

| File | Purpose |
|---|---|
| `main.py` | Argument parsing and dispatch (`main()`) |
| `__main__.py` | `python -m llvmanim.cli` entrypoint |
