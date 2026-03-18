# Graphviz Sandbox

This folder is a standalone LLVM/Graphviz sandbox for generating IR and graph outputs from `double.c`. It is not part of the Python package runtime.

## Prerequisites

- `clang`
- LLVM `opt`
- Graphviz `dot`

On Ubuntu, this is typically:

```bash
sudo apt install clang llvm graphviz
```

## Make Targets

### `make`

Compiles `double.c` to LLVM IR (`double.ll`):

```bash
clang -O0 -fno-strict-aliasing -fno-inline -fno-discard-value-names -S -emit-llvm double.c -o double.ll
```

Why these flags:

- Keep emitted IR easier to read
- Reduce inlining so call/CFG structure stays visible

### `make call-graph`

Generates an LLVM call graph and renders it to SVG:

```bash
opt -passes=dot-callgraph -disable-output double.ll
dot -Tsvg double.ll.callgraph.dot -o callgraph.svg
```

Outputs:

- `double.ll.callgraph.dot`
- `callgraph.svg`

### `make cfg-main`

Generates function-level CFG for `main` and renders it to SVG:

```bash
opt -passes=dot-cfg -disable-output double.ll -cfg-func-name=main
dot -Tsvg .main.dot -o main.svg
```

Outputs:

- `.main.dot`
- `main.svg`

### `make clean`

Removes generated `.ll`, `.dot`, and `.svg` files for this sandbox.
