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
