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
| `--ir-mode {basic,rich,rich-ssa}` | `basic` | Animation display mode |
| `--speed FLOAT` | `1.0` | Animation speed multiplier |
| `--format {mp4,gif}` | `mp4` | Animation output format |
| `--gif-fps FPS` | `12` | GIF conversion frame rate when `--format gif` |
| `--gif-width PX` | `960` | GIF conversion width when `--format gif` |
| `--outdir PATH` | `.` | Output directory (created if absent) |
| `-n` / `--name NAME` | *(stem of input file)* | Base name for output artifacts |
| `--cfg-animate` | off | Render a CFG traversal animation (requires `--dot-cfg`; auto-derives trace if `--import-trace` is not given) |
| `--dot-cfg PATH` | -- | Path to a `.dot` file from `opt -passes=dot-cfg` for CFG layout |
| `--import-cfg-edges PATH` | -- | Import CFG edges from a JSON file instead of extracting from IR |
| `--export-cfg-edges PATH` | -- | Export extracted CFG edges to a JSON file |
| `--import-analysis-metadata PATH` | -- | Import domtree/loop analysis metadata from a JSON file |
| `--export-analysis-metadata PATH` | -- | Export analysis metadata to a JSON file |
| `--import-trace PATH` | -- | Import a runtime path trace from a JSON file for overlay visualization |
| `--export-trace PATH` | -- | Export the trace overlay to a JSON file |
| `-y` / `--yes` | off | Skip confirmation prompts (e.g. auto-derive trace) |
| `--color-scheme {dark,light}` | `dark` | Animation color scheme: `dark` (black background) or `light` (white background) |
| `--quality {l,m,h,p,k}` | *(Manim default: `h`)* | Render quality: `l`=480p/15fps, `m`=720p/30fps, `h`=1080p/60fps, `p`=1440p/60fps, `k`=4K/60fps |
| `--disable-caching` | off | Disable Manim's partial-movie cache (useful when iterating on scenes) |

## Animation Modes

- `basic` -- stack-only layout; arriving cells flash the accent color then settle to white (`StackRenderer` basic mode)
- `rich` -- two-column layout with full IR source on the left and a moving accent-color cursor; stack on the right (`StackRenderer` rich mode)
- `rich-ssa` -- three-column layout (IR Source | SSA Values | Stack) showing binop/compare/load results alongside the rich spotlight view (`StackRenderer` rich-ssa mode)

## Color Schemes

- `dark` (default) -- black background; yellow flash/cursor; green/blue CFG node/edge accents
- `light` -- white background; orange flash/cursor; adjusted CFG node/edge colors for legibility on white

## GIF Output Notes

- `--format gif` renders MP4 first, then converts to GIF with `ffmpeg`.
- This avoids Manim's high-memory GIF combine path and is safer under WSL memory pressure.
- If `ffmpeg` is unavailable, the CLI prints a warning and leaves the MP4 output intact.

## Exit Codes

- `0` -- success
- `1` -- input file not found

## Files

| File | Purpose |
|---|---|
| `main.py` | Argument parsing and dispatch (`main()`) |
| `__main__.py` | `python -m llvmanim.cli` entrypoint |
