# LLVManim
_We should try to keep this updated as we go along._
---
## QuickStart Guide:
Install dependencies:
```bash
uv sync --dev
```
Run quality checks:
```bash
./scripts/quality-check.sh
```
Run tests:
```bash
uv run pytest -q
```
Run CLI:
```bash
uv run llvmanim
```
---
## Dependencies
- [LLVM](https://llvm.org/) - `sudo apt install llvm-18 clang-18`
- Linux system packages required by Manim/ManimGL Python deps:
	- `sudo apt install pkg-config libcairo2-dev libpango1.0-dev`
- [Manim (Community Edition)](https://docs.manim.community/en/stable/installation/uv.html)
  - Follow the install guide with uv
  - Not sure if we want to stick with CE or use the [3b1b version](https://3b1b.github.io/manim/getting_started/installation.html). The 3b1b version is pretty nice and I like the interactivity features, but community edition is _supposed_ to be more stable (doesn't feel like it tbh).
- LLVM bindings - (Exact library tbd)
---
## Using Manim CE
View example [Community Edition scenes](sandbox/manim_CE/example_scenes.py) with
```bash
uv run manim -pql sandbox/manim_CE/example_scenes.py SquareToCircle
```
or
```bash
uv run manim --renderer=opengl -p sandbox/manim_CE/example_scenes.py InteractiveDevelopment
```

InteractiveDevelopment lets you watch animations as you build them using the shell that comes up when you run it, but is vaguely broken on the community edition.

## Using ManimGL
View example [Standard Edition scenes](sandbox/manim/manimgl_scenes.py) with
```bash
uv run manimgl sandbox/manim/manimgl_scenes.py SquareToCircle
```
or
```bash
uv run manimgl sandbox/manim/manimgl_scenes.py InteractiveDevelopment
```
This version lets you zoom in and interact with the scene in different ways. Honestly it just kind of seems significantly better overall, really thinking about using it over the CE.

## Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                         CLI (cli/)                          │
│  llvmanim demo.c --mode=trace --output=demo.mp4             │
│                                                             │
│  • Parse flags (mode, speed, palette, output, interactive)  │
│  • Optionally invoke clang to produce .ll from .c/.cpp      │
└────────────────────────────┬────────────────────────────────┘
                             │ source_path (.ll or .c)
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                      Ingest (ingest/)                       │
│                                                             │
│  parse_ir_to_events(ir_text) → ProgramEventStream           │
│                                                             │
│  • llvmlite: parse module, walk functions/blocks/instrs     │
│  • Classify each instruction into EventKind                 │
│  • (optional) XRay: attach timing data to events            │
└────────────────────────────┬────────────────────────────────┘
                             │ ProgramEventStream
                             │ (list[IREvent], each with
                             │  function, block, opcode, kind,
                             │  operands, debug_line, index)
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                   Transform (transform/)                    │
│                                                             │
│  build_scene_graph(stream, mode) → SceneGraph               │
│                                                             │
│  • One SceneNode per meaningful event                       │
│  • alloca  → StackFrameNode (create variable slot)          │
│  • load    → MemReadNode  (arrow from memory → register)    │
│  • store   → MemWriteNode (arrow from register → memory)    │
│  • call    → CallNode     (push new stack frame)            │
│  • ret     → ReturnNode   (pop stack frame)                 │
│  • br      → BranchNode   (highlight CFG edge)              │
│  • other   → skipped / warning                              │
│                                                             │
│  • Assigns layout positions, colors from palette config     │
│  • Assigns timing offsets (uniform or XRay-driven)          │
└────────────────────────────┬────────────────────────────────┘
                             │ SceneGraph
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                    Present (present/)                       │
│                                                             │
│  render(scene_graph, config) → output file / preview        │
│                                                             │
│  • Translate SceneGraph → Manim Scene subclass              │
│  • Each SceneNode → Mobject + animation command             │
│  • Invoke Manim renderer → MP4 / GIF / interactive GL       │
└─────────────────────────────────────────────────────────────┘
```
