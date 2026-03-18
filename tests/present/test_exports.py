from pathlib import Path

from llvmanim.ingest import parse_ir_to_events
from llvmanim.present import export_cfg_dot, export_scene_graph_json
from llvmanim.transform.scene import build_scene_graph


def _build_graph():
    stream = parse_ir_to_events("""
        define void @f(ptr %p) {
        entry:
          %x = alloca i32
          %cond = icmp eq i32 1, 1
          br i1 %cond, label %yes, label %no
        yes:
          ret void
        no:
          ret void
        }
    """)
    return build_scene_graph(stream)


def test_export_scene_graph_json(tmp_path: Path) -> None:
    graph = _build_graph()
    output = tmp_path / "scene_graph.json"

    export_scene_graph_json(graph, output)

    assert output.exists()
    text = output.read_text(encoding="utf-8")
    assert "f::entry" in text
    assert "f::yes" in text
    assert "f::no" in text


def test_export_cfg_dot(tmp_path: Path) -> None:
    graph = _build_graph()
    output = tmp_path / "cfg.dot"

    export_cfg_dot(graph, output)

    assert output.exists()
    text = output.read_text(encoding="utf-8")
    assert '"f::entry" -> "f::yes"' in text
    assert '"f::entry" -> "f::no"' in text
