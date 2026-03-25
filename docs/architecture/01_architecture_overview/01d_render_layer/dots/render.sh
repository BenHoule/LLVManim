#!/usr/bin/env bash
# Render all DOT files in this directory to PDF in the parent directory.
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
OUTDIR="$(dirname "$DIR")"

for f in "$DIR"/*.dot; do
    base="$(basename "$f" .dot)"
    out="$OUTDIR/${base}.pdf"
    if dot -Tpdf "$f" -o "$out" 2>&1; then
        echo "  OK: ${base}.pdf"
    else
        echo "  FAILED: $f" >&2
    fi
done

shopt -s nullglob
subdirs=("$OUTDIR"/0[0-9]*_*/dots/render.sh)
for script in "${subdirs[@]}"; do
    name="$(basename "$(dirname "$(dirname "$script")")")"
    echo "  ==> Rendering ${name} …"
    bash "$script"
done
