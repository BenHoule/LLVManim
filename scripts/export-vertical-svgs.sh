#!/usr/bin/env bash
# Export every page from the Vertical .drawio file to individual SVGs.
# Usage:  ./scripts/export-vertical-svgs.sh
#
# Set DRAWIO= env var if draw.io CLI isn't on PATH, e.g.:
#   DRAWIO=/tmp/squashfs-root/drawio ./scripts/export-vertical-svgs.sh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VERT="$REPO_ROOT/docs/architecture/01_architecture_overview/Vertical"
SRC="$VERT/01_architecture_overview.drawio"

if [[ -z "${DRAWIO:-}" ]]; then
    for candidate in drawio draw.io; do
        if command -v "$candidate" &>/dev/null; then
            DRAWIO="$candidate"
            break
        fi
    done
fi
if [[ -z "${DRAWIO:-}" ]]; then
    echo "ERROR: draw.io CLI not found. Set DRAWIO=/path/to/drawio" >&2
    exit 1
fi

export_page() {
    local idx="$1" out="$2"
    echo "  p${idx} → ${out#"$VERT"/}"
    "$DRAWIO" --no-sandbox --export --format svg \
        --page-index "$idx" --output "$out" "$SRC" 2>&1 \
        | grep -v "ERROR:viz_main" || true
}

echo "=== Vertical — 01 Architecture Overview ==="
export_page  0 "$VERT/01_architecture_overview.svg"
export_page  1 "$VERT/01a_cli_layer.svg"
export_page  2 "$VERT/01b_ingest_layer/01b_ingest_layer.svg"
export_page  3 "$VERT/01b_ingest_layer/01b1_ir_parsing.svg"
export_page  4 "$VERT/01b_ingest_layer/01b2_dot_layout.svg"
export_page  5 "$VERT/01b_ingest_layer/01b3_supplemental_io.svg"
export_page  6 "$VERT/01c_transform_layer/01c_transform_layer.svg"
export_page  7 "$VERT/01d_render_layer/01d_render_layer.svg"
export_page  8 "$VERT/01d_render_layer/01d1_animation_renderers.svg"
export_page  8 "$VERT/01d_render_layer/01d1_animation_renderers/01d1_animation_renderers.svg"
export_page  9 "$VERT/01d_render_layer/01d1_animation_renderers/01d1a_shared_runtime.svg"
export_page 10 "$VERT/01d_render_layer/01d1_animation_renderers/01d1b_stack_renderer_path.svg"
export_page 11 "$VERT/01d_render_layer/01d1_animation_renderers/01d1c_cfg_renderer_path.svg"
export_page 12 "$VERT/01d_render_layer/01d2_cfg_renderer.svg"
export_page 13 "$VERT/01d_render_layer/01d3_export.svg"

echo ""
echo "Done — $(find "$VERT" -name '*.svg' | wc -l) SVGs exported."
