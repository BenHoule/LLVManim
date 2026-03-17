# LLVM demo build targets: Compile C source → LLVM IR, render call graphs and control flow.
# Not part of Python package infrastructure; maintained for example/education purposes.
# Use this for LLVM IR visualization demos, not for testing the llvmanim package itself.
# For that, use: uv run pytest -q

CC = clang
CFLAGS = -O0 -fno-strict-aliasing -fno-inline -fno-discard-value-names
SRCS = double.c
OBJS = $(SRCS:.c=.ll)

all: $(OBJS)

%.ll: %.c
# clang -O0 -fno-strict-aliasing -fno-inline -fno-discard-value-names -S -emit-llvm double.c -o double.ll
	$(CC) $(CFLAGS) -S -emit-llvm $< -o $@

call-graph: $(OBJS)
	opt -passes=dot-callgraph -disable-output double.ll
	dot -Tsvg double.ll.callgraph.dot -o callgraph.svg

cfg-main: $(OBJS)
	opt -passes=dot-cfg -disable-output double.ll -cfg-func-name=main
	dot -Tsvg .main.dot -o main.svg

clean:
	rm -f $(OBJS) double.ll.callgraph.dot callgraph.svg .main.dot main.svg
