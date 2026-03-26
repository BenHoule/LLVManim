#!/usr/bin/env bash
# Export every page from the architecture .drawio files to individual SVGs.
# Usage:  ./scripts/export-architecture-svgs.sh
#
# Requires draw.io CLI (drawio / draw.io) on PATH or set DRAWIO= env var.
# On Linux without FUSE you can point at an extracted AppImage, e.g.:
#   DRAWIO=/tmp/squashfs-root/drawio ./scripts/export-architecture-svgs.sh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ARCH="$REPO_ROOT/docs/architecture"

# ------------------------------------------------------------------
# Locate draw.io CLI
# ------------------------------------------------------------------
if [[ -z "${DRAWIO:-}" ]]; then
    for candidate in drawio draw.io; do
        if command -v "$candidate" &>/dev/null; then
            DRAWIO="$candidate"
            break
        fi
    done
fi
if [[ -z "${DRAWIO:-}" ]]; then
    echo "ERROR: draw.io CLI not found. Install it or set DRAWIO=/path/to/drawio" >&2
    exit 1
fi

# ------------------------------------------------------------------
# export_page <drawio_file> <page_index> <output_svg>
# ------------------------------------------------------------------
export_page() {
    local src="$1" idx="$2" out="$3"
    echo "  p${idx} → ${out#"$ARCH"/}"
    "$DRAWIO" --no-sandbox --export --format svg \
        --page-index "$idx" --output "$out" "$src" 2>&1 \
        | grep -v "ERROR:viz_main" || true
}

OK=0; FAIL=0

# ==================================================================
# Section 01 — Architecture Overview  (14 pages)
# ==================================================================
SRC="$ARCH/01_architecture_overview/01_architecture_overview.drawio"
echo "=== 01 Architecture Overview ==="
export_page "$SRC"  0 "$ARCH/01_architecture_overview/01_architecture_overview.svg"
export_page "$SRC"  1 "$ARCH/01_architecture_overview/01a_cli_layer.svg"
export_page "$SRC"  2 "$ARCH/01_architecture_overview/01b_ingest_layer/01b_ingest_layer.svg"
export_page "$SRC"  3 "$ARCH/01_architecture_overview/01b_ingest_layer/01b1_ir_parsing.svg"
export_page "$SRC"  4 "$ARCH/01_architecture_overview/01b_ingest_layer/01b2_dot_layout.svg"
export_page "$SRC"  5 "$ARCH/01_architecture_overview/01b_ingest_layer/01b3_supplemental_io.svg"
export_page "$SRC"  6 "$ARCH/01_architecture_overview/01c_transform_layer/01c_transform_layer.svg"
export_page "$SRC"  7 "$ARCH/01_architecture_overview/01d_render_layer/01d_render_layer.svg"
export_page "$SRC"  8 "$ARCH/01_architecture_overview/01d_render_layer/01d1_animation_renderers.svg"
export_page "$SRC"  8 "$ARCH/01_architecture_overview/01d_render_layer/01d1_animation_renderers/01d1_animation_renderers.svg"
export_page "$SRC"  9 "$ARCH/01_architecture_overview/01d_render_layer/01d1_animation_renderers/01d1a_shared_runtime.svg"
export_page "$SRC" 10 "$ARCH/01_architecture_overview/01d_render_layer/01d1_animation_renderers/01d1b_stack_renderer_path.svg"
export_page "$SRC" 11 "$ARCH/01_architecture_overview/01d_render_layer/01d1_animation_renderers/01d1c_cfg_renderer_path.svg"
export_page "$SRC" 12 "$ARCH/01_architecture_overview/01d_render_layer/01d2_cfg_renderer.svg"
export_page "$SRC" 13 "$ARCH/01_architecture_overview/01d_render_layer/01d3_export.svg"

# ==================================================================
# Section 02 — Stack Animation Flow  (3 pages)
# ==================================================================
SRC="$ARCH/02_stack_animation_flow/02_stack_animation_flow.drawio"
echo "=== 02 Stack Animation Flow ==="
export_page "$SRC" 0 "$ARCH/02_stack_animation_flow/02_stack_animation_flow.svg"
export_page "$SRC" 1 "$ARCH/02_stack_animation_flow/02a_ir_mode_branch.svg"
export_page "$SRC" 2 "$ARCH/02_stack_animation_flow/02b_stack_render.svg"

# ==================================================================
# Section 03 — CFG Animation Flow  (4 pages)
# ==================================================================
SRC="$ARCH/03_cfg_animation_flow/03_cfg_animation_flow.drawio"
echo "=== 03 CFG Animation Flow ==="
export_page "$SRC" 0 "$ARCH/03_cfg_animation_flow/03_cfg_animation_flow.svg"
export_page "$SRC" 1 "$ARCH/03_cfg_animation_flow/03a_trace_source.svg"
export_page "$SRC" 2 "$ARCH/03_cfg_animation_flow/03b_cfg_ingest.svg"
export_page "$SRC" 3 "$ARCH/03_cfg_animation_flow/03c_cfg_render_pipeline.svg"

# ==================================================================
# Section 04 — Data Model  (5 pages)
# ==================================================================
SRC="$ARCH/04_data_model/04_data_model.drawio"
echo "=== 04 Data Model ==="
export_page "$SRC" 0 "$ARCH/04_data_model/04_data_model.svg"
export_page "$SRC" 1 "$ARCH/04_data_model/04a_literal_types.svg"
export_page "$SRC" 2 "$ARCH/04_data_model/04b_ingest_types.svg"
export_page "$SRC" 3 "$ARCH/04_data_model/04c_transform_types.svg"
export_page "$SRC" 4 "$ARCH/04_data_model/04d_render_types.svg"

# ==================================================================
# Section 05 — CLI Dispatch  (7 pages)
# ==================================================================
SRC="$ARCH/05_cli_dispatch/05_cli_dispatch.drawio"
echo "=== 05 CLI Dispatch ==="
export_page "$SRC" 0 "$ARCH/05_cli_dispatch/05_cli_dispatch.svg"
export_page "$SRC" 1 "$ARCH/05_cli_dispatch/05a_shared_pipeline.svg"
export_page "$SRC" 2 "$ARCH/05_cli_dispatch/05b_json_output.svg"
export_page "$SRC" 3 "$ARCH/05_cli_dispatch/05c_draw_output.svg"
export_page "$SRC" 4 "$ARCH/05_cli_dispatch/05d_animate_output.svg"
export_page "$SRC" 5 "$ARCH/05_cli_dispatch/05e_cfg_animate_output.svg"
export_page "$SRC" 6 "$ARCH/05_cli_dispatch/05f_export_output.svg"

echo ""
echo "Done — $(find "$ARCH" -name '*.svg' | wc -l) SVGs exported."
