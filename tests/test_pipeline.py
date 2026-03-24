"""Tests for the full pipeline from EventStreams to scene graph."""

from llvmanim.ingest.llvm_events import parse_ir_to_events
from llvmanim.transform.scene import build_scene_graph

# ---------------------------------------------------------------------------
# CFG pipeline (block-level graph, edges, roles)
# ---------------------------------------------------------------------------


def test_cfg_pipeline_produces_blocks_and_edges(all_kinds_ir: str) -> None:
    """CFG pipeline: IR → SceneGraph has correct block count and edges."""
    stream = parse_ir_to_events(all_kinds_ir, source_path="<test_ir>")
    graph = build_scene_graph(stream)
    # IR has 3 basic blocks: entry, yes, no
    assert len(graph.nodes) == 3, "Expected 3 CFG blocks (entry, yes, no)"
    # entry branches to both yes and no
    assert len(graph.edges) == 2, "Expected 2 CFG edges from the conditional branch"
