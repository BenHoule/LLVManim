"""CFG animation helpers: coordinate mapping, block/edge mobject builders.

These helpers are used by :class:`llvmanim.render.cfg_renderer.CFGRenderer`
to build Manim mobjects from :class:`SceneNode` / :class:`DotLayout` data.
"""

from __future__ import annotations

import numpy as np
from manim import (
    BOLD,
    DOWN,
    CubicBezier,
    DashedVMobject,
    RoundedRectangle,
    Text,
    Triangle,
    VGroup,
)

from llvmanim.ingest.dot_layout import DotEdgeLayout, DotNodeLayout
from llvmanim.render.colors import DARK, ColorScheme
from llvmanim.transform.models import SceneNode

# -- Coordinate mapping --------------------------------------------------------


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


# -- Block summary extraction --------------------------------------------------


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


# -- Mobject builders ----------------------------------------------------------


def _build_block_mob(
    node: SceneNode,
    node_layout: DotNodeLayout,
    mapper: _CoordMapper,
    scheme: ColorScheme | None = None,
) -> VGroup:
    """Create a labeled rounded rectangle for one CFG block."""
    s = scheme if scheme is not None else DARK
    mn_w, mn_h = mapper.size(node_layout.width, node_layout.height)
    mn_w = max(mn_w, 1.5)
    mn_h = max(mn_h, 0.8)

    rect = RoundedRectangle(
        width=mn_w,
        height=mn_h,
        corner_radius=0.12,
        fill_color=s.cfg_unvisited_fill,
        fill_opacity=0.9,
        stroke_color=s.cfg_visited_stroke,
        stroke_width=2,
    )

    title = Text(
        node.label,
        font="Monospace",
        font_size=20,
        weight=BOLD,
        color=s.cfg_unvisited_text,
    )

    summary = _block_summary(node)
    if summary:
        detail = Text(
            summary,
            font="Monospace",
            font_size=12,
            color=s.cfg_unvisited_text,
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
    scheme: ColorScheme | None = None,
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
            mn_points[0],
            mn_points[1],
            mn_points[2],
            mn_points[3],
        )
        for i in range(4, len(mn_points) - 2, 3):
            if i + 2 < len(mn_points):
                end_idx = min(i + 3, len(mn_points) - 1)
                seg = CubicBezier(
                    mn_points[i],
                    mn_points[i + 1],
                    mn_points[i + 2],
                    mn_points[end_idx],
                )
                bezier.append_points(seg.points)
    else:
        bezier = CubicBezier(
            mn_points[0],
            mn_points[0] * 0.67 + mn_points[-1] * 0.33,
            mn_points[0] * 0.33 + mn_points[-1] * 0.67,
            mn_points[-1],
        )

    s = scheme if scheme is not None else DARK
    bezier.set_color(s.cfg_edge_dormant)
    bezier.set_stroke(width=2)

    arrow_tip = Triangle(fill_opacity=1, fill_color=s.cfg_edge_dormant, stroke_width=0)
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
            color=s.cfg_edge_dormant,
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
