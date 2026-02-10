clang -O0 -fno-strict-aliasing -fno-inline -fno-discard-value-names -S -emit-llvm double.c -o double.ll
opt -passes='print<postdomtree>' -disable-output double.ll
opt -passes=dot-callgraph -disable-output double.ll
dot -Tsvg double.ll.callgraph.dot -o callgraph.svg
