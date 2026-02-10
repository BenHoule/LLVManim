# LLVManim
_We should try to keep this updated as we go along._
---
Currently just a very basic example file - double.c
### Makefile info:
- `make` -> double.ll IR file
  - `clang -O0 -fno-strict-aliasing -fno-inline -fno-discard-value-names -S -emit-llvm double.c -o double.ll`
  - Flags help keep IR output slightly more readable
  - `-fno-inline` prevents getelementpointer from being passed as an argument (helpful for parsing)
- `make call-graph` -> callgraph.svg
  - `opt -passes=dot-callgraph -disable-output double.ll && dot -Tsvg double.ll.callgraph.dot -o callgraph.svg`
  - .ll -> .dot -> .svg
- `make cfg-main` -> .main.svg
  - `opt -passes=dot-cfg -disable-output double.ll -cfg-func-name=main && dot -Tsvg .main.dot -o main.svg`
  - CFG is per-function, only main has any control flow.

### Dependencies
- [LLVM](https://llvm.org/) - `sudo apt install llvm-18 clang-18`
- [Manim (Community Edition)](https://docs.manim.community/en/stable/installation/uv.html)
  - Follow the install guide with uv
	- Not sure if we want to stick with CE or use the [3b1b version](https://3b1b.github.io/manim/getting_started/installation.html). The 3b1b version is pretty nice and I like the interactivity features, but community edition is _supposed_ to be more stable.
- LLVM bindings - (Exact library tbd)


### Usage
View scenes in example_scenes.py with `manim -pql example_scenes.py SquareToCircle` and `manim --renderer=opengl -p example_scenes.py InteractiveDevelopment`.

InteractiveDevelopment lets you watch animations as you build them using the shell that comes up when you run it.

For manimgl, use `manimgl manimgl_scenes.py SquareToCircle` and `manimgl manimgl_scenes.py InteractiveDevelopment`. Using this version lets you zoom in and interact with the scene in different ways. Honestly it just kind of seems significantly better overall, really thinking about switching off the CE.
