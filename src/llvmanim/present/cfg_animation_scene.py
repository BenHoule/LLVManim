"""CFG traversal animation scene for Manim Community Edition.

Builds a CFG visualization from a :class:`SceneGraph` and optionally a
:class:`DotLayout` for accurate node positioning and edge routing.  If no
DOT layout is provided, nodes are arranged in a simple top-down flow.

When a :class:`TraceOverlay` is present on the scene graph, the scene
animates the runtime execution path stepping through blocks one at a time.

Public API
----------
CFGAnimationScene  — Manim ``Scene`` subclass for CFG traversal animation.
"""

from __future__ import annotations

import numpy as np
from manim import (
    BOLD,
    DOWN,
    GREY_D,
    UP,
    WHITE,
    CubicBezier,
    DashedVMobject,
    FadeIn,
    RoundedRectangle,
    Scene,
    Text,
    Triangle,
    VGroup,
)

from llvmanim.ingest.dot_layout import DotEdgeLayout, DotLayout, DotNodeLayout
from llvmanim.transform.models import SceneGraph, SceneNode, TraceOverlay

# ── Colours ────────────────────────────────────────────────────────────────────
_UNVISITED_FILL = "#555555"
_UNVISITED_TEXT = "#999999"
_ACTIVE_FILL = "#2ecc71"
_VISITED_FILL = "#d4edda"
_VISITED_TEXT = "#333333"
_EDGE_DORMANT = "#666666"
_EDGE_TRAVERSED = "#0056b3"
_EDGE_ACTIVE = "#f1c40f"


# ── Coordinate mapping ────────────────────────────────────────────────────────

class _CoordMapper:
    """Map Graphviz point coordinates to Manim world coordinates.

    Graphviz uses points (1/72 inch) with y=0 at bottom.
    Manim uses a coordinate system roughly -7..+7 x, -4..+4 y with y=0 center.
    """

    def __init__(self, bb: tuple[float, float, float, float]) -> None:
        x0, y0, x1, y1 = bb
        self._gv_w = max(x1 - x0, 1.0)
        self._gv_h = max(y1 - y0, 1.0)
        self._gv_cx = (x0 + x1) / 2
        self._gv_cy = (y0 + y1) / 2

        self._mn_w = 12.0
        self._mn_h = 6.5
        self._mn_cy = -0.3

        self._scale = min(self._mn_w / self._gv_w, self._mn_h / self._gv_h)

    def point(self, gv_x: float, gv_y: float) -> np.ndarray:
        """Convert a Graphviz (x, y) to Manim [x, y, 0]."""
        mx = (gv_x - self._gv_cx) * self._scale
        my = (gv_y - self._gv_cy) * self._scale + self._mn_cy
        return np.array([mx, my, 0.0])

    def size(self, gv_w: float, gv_h: float) -> tuple[float, float]:
        """Convert Graphviz width/height (points) to Manim dimensions."""
        return gv_w * self._scale, gv_h * self._scale


# ── Block summary extraction ──────────────────────────────────────────────────

def _block_summary(node: SceneNode) -> str:
    """Build a short text summary from a scene node's block data."""
    parts: list[str] = []
    props = node.properties
    events = props.get("events", [])
    terminator_opcode = props.get("terminator_opcode")

    for event in events:
        if event.kind == "call" and "@llvm." not in event.text:
            import re

            m = re.search(r"@(\w+)", event.text)
            if m:
                parts.append(f"call @{m.group(1)}")

    if terminator_opcode == "br" and events:
        term = events[-1]
        import re

        m = re.match(r".*?(br i1 %\w+)", term.text)
        if m:
            parts.append(m.group(1))
        else:
            parts.append(f"br {events[-1].opcode}")
    elif terminator_opcode == "ret":
        parts.append("ret")

    return "\n".join(parts) if parts else ""


# ── Mobject builders ──────────────────────────────────────────────────────────

def _build_block_mob(
    node: SceneNode,
    node_layout: DotNodeLayout,
    mapper: _CoordMapper,
) -> VGroup:
    """Create a labeled rounded rectangle for one CFG block."""
    mn_w, mn_h = mapper.size(node_layout.width, node_layout.height)
    mn_w = max(mn_w, 1.5)
    mn_h = max(mn_h, 0.8)

    rect = RoundedRectangle(
        width=mn_w,
        height=mn_h,
        corner_radius=0.12,
        fill_color=_UNVISITED_FILL,
        fill_opacity=0.9,
        stroke_color=GREY_D,
        stroke_width=2,
    )

    title = Text(
        node.label,
        font="Monospace",
        font_size=20,
        weight=BOLD,
        color=_UNVISITED_TEXT,
    )

    summary = _block_summary(node)
    if summary:
        detail = Text(
            summary,
            font="Monospace",
            font_size=12,
            color=_UNVISITED_TEXT,
        )
        title.next_to(rect.get_top(), DOWN, buff=0.12)
        detail.next_to(title, DOWN, buff=0.08)
        if detail.width > mn_w - 0.3:
            detail.scale((mn_w - 0.3) / detail.width)
        group = VGroup(rect, title, detail)
    else:
        title.move_to(rect)
        group = VGroup(rect, title)

    center = mapper.point(node_layout.center_x, node_layout.center_y)
    group.move_to(center)
    return group


def _build_edge_mob(
    edge_layout: DotEdgeLayout,
    mapper: _CoordMapper,
) -> VGroup:
    """Create a bezier curve edge with arrowhead and optional T/F label.

    Edges start dashed (dormant) and transition to solid during traversal.
    """
    points = edge_layout.spline_points
    if len(points) < 2:
        return VGroup()

    mn_points = [mapper.point(x, y) for x, y in points]

    if len(mn_points) >= 4:
        bezier = CubicBezier(
            mn_points[0], mn_points[1], mn_points[2], mn_points[3],
        )
        for i in range(4, len(mn_points) - 2, 3):
            if i + 2 < len(mn_points):
                end_idx = min(i + 3, len(mn_points) - 1)
                seg = CubicBezier(
                    mn_points[i], mn_points[i + 1], mn_points[i + 2], mn_points[end_idx],
                )
                bezier.append_points(seg.points)
    else:
        bezier = CubicBezier(
            mn_points[0],
            mn_points[0] * 0.67 + mn_points[-1] * 0.33,
            mn_points[0] * 0.33 + mn_points[-1] * 0.67,
            mn_points[-1],
        )

    bezier.set_color(_EDGE_DORMANT)
    bezier.set_stroke(width=2)

    arrow_tip = Triangle(fill_opacity=1, fill_color=_EDGE_DORMANT, stroke_width=0)
    arrow_tip.scale(0.08)
    end_pt = bezier.point_from_proportion(1.0)
    near_end = bezier.point_from_proportion(0.92)
    direction = end_pt - near_end
    angle = float(np.arctan2(direction[1], direction[0]))
    arrow_tip.rotate(angle - np.pi / 2)
    arrow_tip.move_to(end_pt)

    dashed_path = DashedVMobject(bezier, num_dashes=20)
    group = VGroup(dashed_path, arrow_tip)

    # Store references for traversal animation
    group.solid_curve = bezier  # type: ignore[attr-defined]
    group.arrow_tip = arrow_tip  # type: ignore[attr-defined]
    group.is_dashed = True  # type: ignore[attr-defined]

    if edge_layout.label:
        lbl = Text(
            edge_layout.label,
            font="Monospace",
            font_size=16,
            weight=BOLD,
            color=_EDGE_DORMANT,
        )
        label_pt = bezier.point_from_proportion(0.25)
        lbl.move_to(label_pt)
        tangent = bezier.point_from_proportion(0.3) - bezier.point_from_proportion(0.2)
        perp = np.array([-tangent[1], tangent[0], 0])
        norm = float(np.linalg.norm(perp))
        if norm > 0:
            lbl.shift(perp / norm * 0.22)
        group.add(lbl)
        group.edge_label = lbl  # type: ignore[attr-defined]

    return group


# ── Scene ──────────────────────────────────────────────────────────────────────

class CFGAnimationScene(Scene):
    """Animate a step-by-step CFG traversal using Graphviz-computed layout.

    Parameters
    ----------
    graph:
        The CFG scene graph to visualize.
    layout:
        Graphviz-computed layout with node positions and edge splines.
    speed:
        Animation speed multiplier (higher = faster).
    title:
        Title text shown at the top of the animation.
    """

    def __init__(
        self,
        graph: SceneGraph,
        layout: DotLayout,
        speed: float = 1.0,
        title: str = "CFG Traversal",
        **kwargs: object,
    ) -> None:
        super().__init__(**kwargs)  # type: ignore[arg-type]
        self._graph = graph
        self._layout = layout
        self._speed = max(speed, 0.1)
        self._title = title

        self._block_mobs: dict[str, VGroup] = {}
        self._edge_groups: dict[tuple[str, str], VGroup] = {}
        self._visited: set[str] = set()
        self._traversed: set[tuple[str, str]] = set()

        # Build node-id → SceneNode lookup
        self._node_lookup: dict[str, SceneNode] = {}
        for node in graph.nodes:
            self._node_lookup[node.id] = node
            self._node_lookup[node.label] = node

    def construct(self) -> None:
        mapper = _CoordMapper(self._layout.bounding_box)

        self._draw_title()
        self._draw_graph(mapper)
        self.wait(0.5 / self._speed)

        overlay = self._graph.overlay
        if overlay and overlay.entry_order:
            self._animate_traversal(overlay)

        self.wait(2.0 / self._speed)

    def _draw_title(self) -> None:
        title = Text(self._title, font_size=28, weight=BOLD)
        title.to_edge(UP, buff=0.3)
        self.play(FadeIn(title, shift=DOWN * 0.2), run_time=0.5 / self._speed)

    def _draw_graph(self, mapper: _CoordMapper) -> None:
        """Build and fade in all block nodes and edge curves."""
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

        self.play(
            *[FadeIn(mob, scale=0.9) for mob in self._block_mobs.values()],
            run_time=0.8 / self._speed,
        )
        self.play(
            *[FadeIn(g) for g in self._edge_groups.values()],
            run_time=0.6 / self._speed,
        )

    def _activate_block(self, block_name: str) -> None:
        """Highlight a block as currently executing."""
        mob = self._block_mobs.get(block_name)
        if mob is None:
            return
        rect = mob[0]
        text_mobs = list(mob[1:])

        anims = [
            rect.animate.set_fill(color=_ACTIVE_FILL, opacity=0.95)
            .set_stroke(color=WHITE, width=3),
        ]
        for t in text_mobs:
            anims.append(t.animate.set_color(WHITE))
        self.play(*anims, run_time=0.35 / self._speed)

    def _settle_block(self, block_name: str) -> None:
        """Transition from active to visited styling."""
        mob = self._block_mobs.get(block_name)
        if mob is None:
            return
        rect = mob[0]
        text_mobs = list(mob[1:])

        anims = [
            rect.animate.set_fill(color=_VISITED_FILL, opacity=0.9)
            .set_stroke(color=GREY_D, width=2),
        ]
        for t in text_mobs:
            anims.append(t.animate.set_color(_VISITED_TEXT))
        self.play(*anims, run_time=0.25 / self._speed)

    def _traverse_edge(self, src: str, dst: str) -> None:
        """Flash an edge yellow then settle it to bold blue."""
        key = (src, dst)
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
                run_time=0.2 / self._speed,
            )
        else:
            curve = group[0]
            tip_mob: Triangle = group.arrow_tip  # type: ignore[attr-defined]
            self.play(
                curve.animate.set_color(_EDGE_ACTIVE).set_stroke(width=3.5),
                tip_mob.animate.set_fill(color=_EDGE_ACTIVE),
                run_time=0.2 / self._speed,
            )

        curve = group[0]
        settle_tip: Triangle = group.arrow_tip  # type: ignore[attr-defined]
        self.play(
            curve.animate.set_color(_EDGE_TRAVERSED).set_stroke(width=3),
            settle_tip.animate.set_fill(color=_EDGE_TRAVERSED),
            run_time=0.15 / self._speed,
        )

        if hasattr(group, "edge_label"):
            group.edge_label.set_color(_EDGE_TRAVERSED)  # type: ignore[attr-defined]
        self._traversed.add(key)

    def _resolve_block_name(self, entry: str) -> str:
        """Resolve an entry_order entry to a block name.

        entry_order may use bare names like ``entry`` or qualified IDs like
        ``main::entry``.  We normalize to the bare block name for mobject lookup.
        """
        if "::" in entry:
            return entry.split("::", 1)[1]
        return entry

    def _animate_traversal(self, overlay: TraceOverlay) -> None:
        """Step through the entry_order, highlighting blocks and edges."""
        prev_block: str | None = None

        for i, raw_entry in enumerate(overlay.entry_order):
            block_name = self._resolve_block_name(raw_entry)

            if prev_block is not None:
                self._traverse_edge(prev_block, block_name)

            if prev_block is not None and prev_block != block_name:
                self._settle_block(prev_block)

            self._activate_block(block_name)
            self._visited.add(block_name)

            if i == 0:
                self.wait(0.6 / self._speed)
            else:
                self.wait(0.3 / self._speed)

            prev_block = block_name

        if prev_block:
            self._settle_block(prev_block)
