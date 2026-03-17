### Makefile info:
`make` -> double.ll IR file
```bash
 clang -O0 -fno-strict-aliasing -fno-inline -fno-discard-value-names -S -emit-llvm double.c -o double.ll
```
- Flags help keep IR output slightly more readable
- `-fno-inline` prevents getelementpointer from being passed as an argument (helpful for parsing)

`make call-graph` -> callgraph.svg
```bash
opt -passes=dot-callgraph -disable-output double.ll && dot -Tsvg double.ll.callgraph.dot -o callgraph.svg
```
- .ll -> .dot -> .svg

`make cfg-main` -> .main.svg
```bash
opt -passes=dot-cfg -disable-output double.ll -cfg-func-name=main && dot -Tsvg .main.dot -o main.svg
```
- CFG is per-function, only main has any control flow.
