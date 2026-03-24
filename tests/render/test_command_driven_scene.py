"""Tests for the CommandDrivenScene base and its renderers."""

from __future__ import annotations

from llvmanim.render.cfg_renderer import CFGRenderer
from llvmanim.render.command_driven_scene import CommandDrivenScene
from llvmanim.render.stack_renderer import StackRenderer
from llvmanim.transform.models import AnimationCommand, SceneGraph, SceneNode

# ── CommandDrivenScene ───────────────────────────────────────────


def test_command_driven_scene_is_manim_scene() -> None:
    from manim import Scene

    graph = SceneGraph()
    scene = CommandDrivenScene(graph)
    assert isinstance(scene, Scene)


def test_command_driven_scene_registers_and_dispatches() -> None:
    graph = SceneGraph(
        commands=[
            AnimationCommand(action="push_stack_frame", target="frame::main#1"),
        ]
    )
    scene = CommandDrivenScene(graph)
    called_with: list[AnimationCommand] = []
    scene._register_handler("push_stack_frame", called_with.append)
    scene._dispatch(graph.commands[0])
    assert len(called_with) == 1
    assert called_with[0].action == "push_stack_frame"


def test_command_driven_scene_ignores_unregistered_actions() -> None:
    graph = SceneGraph(
        commands=[
            AnimationCommand(action="enter_block", target="f::entry"),
        ]
    )
    scene = CommandDrivenScene(graph)
    scene._dispatch(graph.commands[0])  # should not raise


def test_command_driven_scene_speed_clamped() -> None:
    graph = SceneGraph()
    scene = CommandDrivenScene(graph, speed=0.0)
    assert scene._speed >= 0.01
    assert scene._rt(1.0) > 0


# ── StackRenderer ────────────────────────────────────────────────


def test_stack_renderer_is_command_driven_scene() -> None:
    graph = SceneGraph()
    renderer = StackRenderer(graph)
    assert isinstance(renderer, CommandDrivenScene)


def test_setup_chrome_adds_title_and_rule() -> None:
    graph = SceneGraph()
    scene = CommandDrivenScene(graph, title="Test Title")
    scene._setup_chrome()
    # Title and rule should be added as mobjects
    assert len(scene.mobjects) == 2


def test_setup_chrome_noop_without_title() -> None:
    graph = SceneGraph()
    scene = CommandDrivenScene(graph, title="")
    scene._setup_chrome()
    assert len(scene.mobjects) == 0


def test_stack_renderer_registers_expected_handlers() -> None:
    graph = SceneGraph()
    renderer = StackRenderer(graph)
    expected = {"push_stack_frame", "pop_stack_frame", "create_stack_slot", "highlight_branch"}
    assert expected.issubset(set(renderer._handlers.keys()))


def test_stack_renderer_rich_mode_registers_stack_handlers() -> None:
    graph = SceneGraph()
    renderer = StackRenderer(graph, ir_mode="rich")
    expected = {"push_stack_frame", "pop_stack_frame", "create_stack_slot", "highlight_branch"}
    assert expected.issubset(set(renderer._handlers.keys()))


def test_stack_renderer_rich_ssa_registers_all_handlers() -> None:
    graph = SceneGraph()
    renderer = StackRenderer(graph, ir_mode="rich-ssa")
    expected = {
        "push_stack_frame", "pop_stack_frame", "create_stack_slot",
        "highlight_branch", "animate_binop", "animate_compare", "animate_memory_read",
    }
    assert expected.issubset(set(renderer._handlers.keys()))


def test_stack_renderer_stores_graph() -> None:
    node = SceneNode(id="frame::main#1", label="main", kind="stack_frame")
    graph = SceneGraph(nodes=[node])
    renderer = StackRenderer(graph)
    assert renderer._graph is graph


# ── CFGRenderer ──────────────────────────────────────────────────


def test_cfg_renderer_is_command_driven_scene() -> None:
    from llvmanim.ingest.dot_layout import DotLayout

    graph = SceneGraph()
    layout = DotLayout(bounding_box=(0, 0, 400, 300))
    renderer = CFGRenderer(graph, layout)
    assert isinstance(renderer, CommandDrivenScene)


def test_cfg_renderer_registers_expected_handlers() -> None:
    from llvmanim.ingest.dot_layout import DotLayout

    graph = SceneGraph()
    layout = DotLayout(bounding_box=(0, 0, 400, 300))
    renderer = CFGRenderer(graph, layout)
    expected = {"enter_block", "exit_block", "traverse_edge"}
    assert expected.issubset(set(renderer._handlers.keys()))


def test_cfg_renderer_builds_node_lookup() -> None:
    from llvmanim.ingest.dot_layout import DotLayout

    node = SceneNode(
        id="f::entry",
        label="entry",
        kind="cfg_block",
        properties={"role": "entry"},
    )
    graph = SceneGraph(nodes=[node])
    layout = DotLayout(bounding_box=(0, 0, 400, 300))
    renderer = CFGRenderer(graph, layout)
    assert renderer._node_lookup["f::entry"] is node
    assert renderer._node_lookup["entry"] is node


def test_cfg_renderer_resolve_block_name_qualified() -> None:
    from llvmanim.ingest.dot_layout import DotLayout

    graph = SceneGraph()
    layout = DotLayout(bounding_box=(0, 0, 400, 300))
    renderer = CFGRenderer(graph, layout)
    assert renderer._resolve_block_name("main::entry") == "entry"
    assert renderer._resolve_block_name("entry") == "entry"
