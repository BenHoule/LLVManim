"""CFG traversal animation renderer driven by a SceneGraph's command list.

``CFGRenderer`` is a :class:`CommandDrivenScene` subclass that registers
handlers for ``enter_block``, ``exit_block``, and ``traverse_edge`` actions.
It replaces ``CFGAnimationScene`` in the unified pipeline.
"""

from __future__ import annotations

from manim import (
    GREY_D,
    WHITE,
    CubicBezier,
    FadeIn,
    Triangle,
    VGroup,
)

from llvmanim.ingest.dot_layout import DotLayout
from llvmanim.render.cfg_animation_scene import (
    _ACTIVE_FILL,
    _EDGE_ACTIVE,
    _EDGE_TRAVERSED,
    _VISITED_FILL,
    _VISITED_TEXT,
    _build_block_mob,
    _build_edge_mob,
    _CoordMapper,
)
from llvmanim.render.command_driven_scene import CommandDrivenScene
from llvmanim.transform.models import AnimationCommand, SceneGraph, SceneNode


class CFGRenderer(CommandDrivenScene):
    """Command-driven CFG traversal animation scene.

    Parameters
    ----------
    graph:
        A SceneGraph produced by ``build_scene_graph()`` (with commands
        populated via ``_build_overlay_commands``).
    layout:
        Graphviz-computed layout with node positions and edge splines.
    speed:
        Animation speed multiplier.
    title:
        Title text shown at the top.
    """

    def __init__(
        self,
        graph: SceneGraph,
        layout: DotLayout,
        speed: float = 1.0,
        title: str = "CFG Traversal",
        **kwargs: object,
    ) -> None:
        super().__init__(graph, speed=speed, title=title, **kwargs)
        self._layout = layout

        self._block_mobs: dict[str, VGroup] = {}
        self._edge_groups: dict[tuple[str, str], VGroup] = {}
        self._visited: set[str] = set()
        self._traversed: set[tuple[str, str]] = set()

        self._node_lookup: dict[str, SceneNode] = {}
        for node in graph.nodes:
            self._node_lookup[node.id] = node
            self._node_lookup[node.label] = node

        self._register_handler("enter_block", self._handle_enter_block)
        self._register_handler("exit_block", self._handle_exit_block)
        self._register_handler("traverse_edge", self._handle_traverse_edge)

    # ── Setup ───────────────────────────────────────────────────────────────

    def _setup_scene(self) -> None:
        mapper = _CoordMapper(self._layout.bounding_box)

        for node in self._graph.nodes:
            block_name = node.label
            node_layout = self._layout.nodes.get(block_name)
            if node_layout is None:
                continue
            mob = _build_block_mob(node, node_layout, mapper)
            self._block_mobs[block_name] = mob

        for edge_layout in self._layout.edges:
            group = _build_edge_mob(edge_layout, mapper)
            self._edge_groups[(edge_layout.source, edge_layout.target)] = group

        block_anims = [FadeIn(mob, scale=0.9) for mob in self._block_mobs.values()]
        if block_anims:
            self.play(*block_anims, run_time=self._rt(0.8))

        edge_anims = [FadeIn(g) for g in self._edge_groups.values()]
        if edge_anims:
            self.play(*edge_anims, run_time=self._rt(0.6))

    # ── Handlers ────────────────────────────────────────────────────────────

    def _resolve_block_name(self, target: str) -> str:
        """Resolve a command target to a bare block name for mobject lookup."""
        if "::" in target:
            return target.split("::", 1)[1]
        return target

    def _handle_enter_block(self, cmd: AnimationCommand) -> None:
        block_name = self._resolve_block_name(cmd.target)
        mob = self._block_mobs.get(block_name)
        if mob is None:
            return
        rect = mob[0]
        text_mobs = list(mob[1:])

        anims = [
            rect.animate.set_fill(color=_ACTIVE_FILL, opacity=0.95).set_stroke(
                color=WHITE, width=3
            ),
        ]
        for t in text_mobs:
            anims.append(t.animate.set_color(WHITE))
        self.play(*anims, run_time=self._rt(0.35))
        self._visited.add(block_name)

    def _handle_exit_block(self, cmd: AnimationCommand) -> None:
        block_name = self._resolve_block_name(cmd.target)
        mob = self._block_mobs.get(block_name)
        if mob is None:
            return
        rect = mob[0]
        text_mobs = list(mob[1:])

        anims = [
            rect.animate.set_fill(color=_VISITED_FILL, opacity=0.9).set_stroke(
                color=GREY_D, width=2
            ),
        ]
        for t in text_mobs:
            anims.append(t.animate.set_color(_VISITED_TEXT))
        self.play(*anims, run_time=self._rt(0.25))

    def _handle_traverse_edge(self, cmd: AnimationCommand) -> None:
        src = cmd.params.get("source", "")
        dst = cmd.params.get("target", "")
        src_name = self._resolve_block_name(src)
        dst_name = self._resolve_block_name(dst)
        key = (src_name, dst_name)
        group = self._edge_groups.get(key)
        if group is None:
            return

        if getattr(group, "is_dashed", False) and key not in self._traversed:
            dashed_mob = group[0]
            solid: CubicBezier = group.solid_curve  # type: ignore[attr-defined]
            solid.set_color(_EDGE_ACTIVE).set_stroke(width=3.5)
            tip: Triangle = group.arrow_tip  # type: ignore[attr-defined]
            tip.set_fill(color=_EDGE_ACTIVE)

            self.remove(dashed_mob)
            group.submobjects[0] = solid  # type: ignore[index]
            self.add(solid)
            group.is_dashed = False  # type: ignore[attr-defined]

            self.play(
                solid.animate.set_color(_EDGE_ACTIVE).set_stroke(width=3.5),
                run_time=self._rt(0.2),
            )
        else:
            curve = group[0]
            tip_mob: Triangle = group.arrow_tip  # type: ignore[attr-defined]
            self.play(
                curve.animate.set_color(_EDGE_ACTIVE).set_stroke(width=3.5),
                tip_mob.animate.set_fill(color=_EDGE_ACTIVE),
                run_time=self._rt(0.2),
            )

        curve = group[0]
        settle_tip: Triangle = group.arrow_tip  # type: ignore[attr-defined]
        self.play(
            curve.animate.set_color(_EDGE_TRAVERSED).set_stroke(width=3),
            settle_tip.animate.set_fill(color=_EDGE_TRAVERSED),
            run_time=self._rt(0.15),
        )

        if hasattr(group, "edge_label"):
            group.edge_label.set_color(_EDGE_TRAVERSED)  # type: ignore[attr-defined]
        self._traversed.add(key)
