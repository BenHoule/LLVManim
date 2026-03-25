#!/usr/bin/env bash
# Render all DOT architecture diagrams to PDF.
#
# Hand-authored diagrams live in numbered subdirectories, each with its own
# dots/ folder and render.sh script:
#   01_architecture_overview/dots/render.sh
#   02_stack_animation_flow/dots/render.sh
#   03_cfg_animation_flow/dots/render.sh
#   04_data_model/dots/render.sh
#   05_cli_dispatch/dots/render.sh
#
# Auto-generated sources: docs/architecture/generated/*.dot  (via pyreverse + pydeps)
#
# Usage (from repo root or docs/architecture/):
#   ./docs/architecture/render.sh [--regen]
#
# Pass --regen to re-run pyreverse and pydeps before rendering.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
GEN_DIR="$SCRIPT_DIR/generated"

# ── Optional: regenerate auto-generated diagrams ────────────────────────────
if [[ "${1:-}" == "--regen" ]]; then
    echo "==> Regenerating via pyreverse …"
    mkdir -p "$GEN_DIR"
    (cd "$REPO_ROOT" && uv run pyreverse src/llvmanim -o dot -d "$GEN_DIR" --project llvmanim)

    echo "==> Regenerating via pydeps (full) …"
    (cd "$REPO_ROOT" && uv run pydeps src/llvmanim --noshow --max-bacon=4 \
        --rankdir TB --cluster -T dot -o "$GEN_DIR/pydeps_llvmanim.dot")

    echo "==> Regenerating via pydeps (internal only) …"
    (cd "$REPO_ROOT" && uv run pydeps src/llvmanim --noshow --max-bacon=2 \
        --rankdir TB --cluster --only llvmanim \
        -T dot -o "$GEN_DIR/pydeps_internal.dot")
fi

# ── Render hand-authored diagrams (delegate to each subdirectory) ────────────
shopt -s nullglob
subdirs=("$SCRIPT_DIR"/0[0-9]*_*/dots/render.sh)
if [[ ${#subdirs[@]} -eq 0 ]]; then
    echo "No subdirectory render scripts found." >&2
    exit 1
fi

for script in "${subdirs[@]}"; do
    name="$(basename "$(dirname "$(dirname "$script")")")"
    echo "==> Rendering ${name} …"
    bash "$script"
done

# ── Render auto-generated diagrams ───────────────────────────────────────────
gen_dots=("$GEN_DIR"/*.dot)
if [[ ${#gen_dots[@]} -gt 0 ]]; then
    echo "==> Rendering generated diagrams …"
    for src in "${gen_dots[@]}"; do
        base="$(basename "$src" .dot)"
        dot -Tpdf "$src" -o "$GEN_DIR/${base}.pdf"
        echo "  OK: generated/${base}.pdf"
    done
fi
