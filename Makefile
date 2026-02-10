CC = clang
CFLAGS = -O0 -fno-strict-aliasing -fno-inline -fno-discard-value-names
SRCS = double.c
OBJS = $(SRCS:.c=.ll)

all: $(OBJS)

%.ll: %.c
	$(CC) $(CFLAGS) -S -emit-llvm $< -o $@

call-graph: $(OBJS)
	opt -passes=dot-callgraph -disable-output double.ll
	dot -Tsvg double.ll.callgraph.dot -o callgraph.svg

cfg-main: $(OBJS)
	opt -passes=dot-cfg -disable-output double.ll
	dot -Tsvg .main.dot -o main.svg

clean:
	rm -f $(OBJS) double.ll.callgraph.dot callgraph.svg double.ll.cfg.dot cfg.svg
