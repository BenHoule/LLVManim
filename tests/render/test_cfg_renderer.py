"""Unit tests for CFGRenderer: constructor plumbing and pure helper methods."""

from __future__ import annotations

from llvmanim.ingest.dot_layout import DotLayout, DotNodeLayout
from llvmanim.render.cfg_renderer import CFGRenderer
from llvmanim.render.colors import DARK, LIGHT
from llvmanim.render.command_driven_scene import CommandDrivenScene
from llvmanim.transform.models import SceneGraph, SceneNode


def _minimal_layout() -> DotLayout:
    return DotLayout(
        nodes={
            "entry": DotNodeLayout(name="entry", center_x=100, center_y=100, width=100, height=60),
        },
        edges=[],
        bounding_box=(0, 0, 200, 200),
    )


def _minimal_graph() -> SceneGraph:
    return SceneGraph(
        nodes=[
            SceneNode(id="f::entry", label="entry", kind="cfg_block"),
        ],
        edges=[],
    )


class TestCFGRendererInit:
    def test_is_command_driven_scene(self) -> None:
        renderer = CFGRenderer(_minimal_graph(), _minimal_layout())
        assert isinstance(renderer, CommandDrivenScene)

    def test_registers_expected_handlers(self) -> None:
        renderer = CFGRenderer(_minimal_graph(), _minimal_layout())
        expected = {"enter_block", "exit_block", "traverse_edge"}
        assert expected.issubset(set(renderer._handlers.keys()))

    def test_node_lookup_by_id_and_label(self) -> None:
        renderer = CFGRenderer(_minimal_graph(), _minimal_layout())
        assert "f::entry" in renderer._node_lookup
        assert "entry" in renderer._node_lookup

    def test_speed_is_stored(self) -> None:
        renderer = CFGRenderer(_minimal_graph(), _minimal_layout(), speed=2.5)
        assert renderer._speed == 2.5

    def test_defaults_to_dark_scheme(self) -> None:
        renderer = CFGRenderer(_minimal_graph(), _minimal_layout())
        assert renderer._scheme is DARK

    def test_accepts_light_scheme(self) -> None:
        renderer = CFGRenderer(_minimal_graph(), _minimal_layout(), scheme=LIGHT)
        assert renderer._scheme is LIGHT

    def test_explicit_dark_scheme(self) -> None:
        renderer = CFGRenderer(_minimal_graph(), _minimal_layout(), scheme=DARK)
        assert renderer._scheme is DARK


class TestResolveBlockName:
    def test_strips_function_prefix(self) -> None:
        renderer = CFGRenderer(_minimal_graph(), _minimal_layout())
        assert renderer._resolve_block_name("f::entry") == "entry"

    def test_returns_bare_name_unchanged(self) -> None:
        renderer = CFGRenderer(_minimal_graph(), _minimal_layout())
        assert renderer._resolve_block_name("entry") == "entry"

    def test_handles_double_colon_in_block_name(self) -> None:
        renderer = CFGRenderer(_minimal_graph(), _minimal_layout())
        assert renderer._resolve_block_name("ns::cls::method") == "cls::method"
