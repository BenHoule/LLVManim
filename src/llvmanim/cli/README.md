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
| `--format {mp4,gif}` | `mp4` | Animation output format |
| `--gif-fps FPS` | `12` | GIF conversion frame rate when `--format gif` |
| `--gif-width PX` | `960` | GIF conversion width when `--format gif` |
| `--outdir PATH` | `.` | Output directory (created if absent) |
| `--cfg-animate` | off | Render a CFG traversal animation (requires `--dot-cfg` and `--import-trace`) |
| `--dot-cfg PATH` | — | Path to a `.dot` file from `opt -passes=dot-cfg` for CFG layout |
| `--import-cfg-edges PATH` | — | Import CFG edges from a JSON file instead of extracting from IR |
| `--export-cfg-edges PATH` | — | Export extracted CFG edges to a JSON file |
| `--import-analysis-metadata PATH` | — | Import domtree/loop analysis metadata from a JSON file |
| `--export-analysis-metadata PATH` | — | Export analysis metadata to a JSON file |
| `--import-trace PATH` | — | Import a runtime path trace from a JSON file for overlay visualization |
| `--export-trace PATH` | — | Export the trace overlay to a JSON file |

## Animation Modes

- `basic` — stack-only layout; arriving cells flash yellow then settle to white (`RichStackSceneBadge`)
- `rich` — two-column layout with full IR source on the left and a moving yellow cursor; stack on the right (`RichStackSceneSpotlight`)

## GIF Output Notes

- `--format gif` renders MP4 first, then converts to GIF with `ffmpeg`.
- This avoids Manim's high-memory GIF combine path and is safer under WSL memory pressure.
- If `ffmpeg` is unavailable, the CLI prints a warning and leaves the MP4 output intact.

## Exit Codes

- `0` — success
- `1` — input file not found

## Files

| File | Purpose |
|---|---|
| `main.py` | Argument parsing and dispatch (`main()`) |
| `__main__.py` | `python -m llvmanim.cli` entrypoint |
