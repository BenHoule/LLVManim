"""Color scheme definitions for LLVManim scenes.

Two built-in schemes are provided:

  DARK  — Black background (Manim default).  All current hardcoded colors
          belong to this scheme.
  LIGHT — White background with inverted chrome colors for readability.

Pass a :data:`ColorScheme` instance to :class:`~llvmanim.render.cfg_renderer.CFGRenderer`
or :class:`~llvmanim.render.stack_renderer.StackRenderer` via the ``scheme`` keyword
argument to switch the visual theme.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from manim import BLACK, GREY_B, GREY_D, ORANGE, WHITE, YELLOW


@dataclass(frozen=True)
class ColorScheme:
    """Holds all theme-specific colors for a single LLVManim scene."""

    # -- Canvas --------------------------------------------------------------
    background: str  # hex string passed to manim_config.background_color

    # -- Chrome (title bar, divider lines, column labels) --------------------
    title_color: Any  # ManimColor accepted by Manim Text
    rule_color: Any  # horizontal rule beneath the title
    label_color: Any  # column header labels ("IR Source", "Stack …")
    divider_color: Any  # vertical divider lines between columns

    # -- Canvas text (text that sits directly on the background) -------------
    ir_text_color: Any  # IR source panel lines

    # -- Animation accents ---------------------------------------------------
    flash_color: Any  # badge flash on incoming stack / SSA elements
    cursor_color: Any  # SurroundingRectangle IR cursor

    # -- Stack block text ----------------------------------------------------
    stack_text_color: Any  # resting text color in frame headers and slot cells
    # -- CFG block states ----------------------------------------------------
    cfg_unvisited_fill: str
    cfg_unvisited_text: str
    cfg_active_fill: str
    cfg_active_text: Any
    cfg_active_stroke: Any
    cfg_visited_fill: str
    cfg_visited_text: str
    cfg_visited_stroke: Any

    # -- CFG edges -----------------------------------------------------------
    cfg_edge_dormant: str
    cfg_edge_traversed: str
    cfg_edge_active: str


# -- Built-in schemes --------------------------------------------------------

DARK = ColorScheme(
    background="#000000",
    title_color=WHITE,
    rule_color=GREY_D,
    label_color=GREY_B,
    divider_color=GREY_D,
    ir_text_color=WHITE,
    flash_color=YELLOW,
    cursor_color=YELLOW,
    stack_text_color=WHITE,
    cfg_unvisited_fill="#555555",
    cfg_unvisited_text="#999999",
    cfg_active_fill="#2ecc71",
    cfg_active_text=WHITE,
    cfg_active_stroke=WHITE,
    cfg_visited_fill="#d4edda",
    cfg_visited_text="#333333",
    cfg_visited_stroke=GREY_D,
    cfg_edge_dormant="#666666",
    cfg_edge_traversed="#0056b3",
    cfg_edge_active="#f1c40f",
)

LIGHT = ColorScheme(
    background="#ffffff",
    title_color=BLACK,
    rule_color="#aaaaaa",
    label_color="#555555",
    divider_color="#aaaaaa",
    ir_text_color=BLACK,
    flash_color=ORANGE,
    cursor_color=ORANGE,
    stack_text_color=BLACK,
    cfg_unvisited_fill="#d0d0d0",
    cfg_unvisited_text="#333333",
    cfg_active_fill="#27ae60",
    cfg_active_text=WHITE,
    cfg_active_stroke="#27ae60",
    cfg_visited_fill="#a9dfbf",
    cfg_visited_text="#1a1a1a",
    cfg_visited_stroke="#aaaaaa",
    cfg_edge_dormant="#888888",
    cfg_edge_traversed="#1a6cb3",
    cfg_edge_active="#e67e22",
)

SCHEMES: dict[str, ColorScheme] = {
    "dark": DARK,
    "light": LIGHT,
}
