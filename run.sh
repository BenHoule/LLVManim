clang -O0 -fno-strict-aliasing -fno-inline -fno-discard-value-names -S -emit-llvm double.c -o double.ll
opt -passes='print<postdomtree>' -disable-output double.ll
