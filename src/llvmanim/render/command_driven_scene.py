"""Base class for command-driven Manim scenes.

A ``CommandDrivenScene`` receives a :class:`SceneGraph` and iterates over
its ``commands`` list, dispatching each :class:`AnimationCommand` to a
registered handler function.  Subclasses register handlers via
``_register_handler`` and implement ``_setup_scene`` and ``_setup_chrome``
hooks to create the initial visual layout.
"""

from __future__ import annotations

from collections.abc import Callable

from manim import BOLD, DOWN, LEFT, RIGHT, UP, Line, Scene, Text

from llvmanim.render.colors import DARK, ColorScheme
from llvmanim.transform.models import ActionKind, AnimationCommand, SceneGraph


class CommandDrivenScene(Scene):
    """Base scene that dispatches AnimationCommands to registered handlers.

    Parameters
    ----------
    graph:
        The scene graph to visualize (nodes, edges, and commands).
    speed:
        Animation speed multiplier (higher = faster).
    title:
        Optional title text shown at the top of the animation.
    """

    def __init__(
        self,
        graph: SceneGraph,
        speed: float = 1.0,
        title: str = "",
        scheme: ColorScheme | None = None,
        **kwargs: object,
    ) -> None:
        super().__init__(**kwargs)  # type: ignore[arg-type]
        self._graph = graph
        self._speed = max(speed, 0.01)
        self._title = title
        self._scheme = scheme if scheme is not None else DARK
        self._handlers: dict[ActionKind, Callable[[AnimationCommand], None]] = {}

    def _register_handler(
        self, action: ActionKind, handler: Callable[[AnimationCommand], None]
    ) -> None:
        """Register a handler function for the given action kind."""
        self._handlers[action] = handler

    def _rt(self, base: float) -> float:
        """Return a run_time scaled by the inverse of the speed multiplier."""
        return base / self._speed

    def _setup_scene(self) -> None:
        """Create initial Mobjects from graph nodes and edges.  Override in subclasses."""

    def _setup_chrome(self) -> None:
        """Add title bar, column labels, dividers, etc."""
        if self._title:
            title = Text(self._title, font_size=30, weight=BOLD, color=self._scheme.title_color)
            title.to_edge(UP, buff=0.28)
            self.add(title)
            rule = Line(
                title.get_bottom() + DOWN * 0.12 + LEFT * 7.1,
                title.get_bottom() + DOWN * 0.12 + RIGHT * 7.1,
                color=self._scheme.rule_color,
                stroke_width=1,
            )
            self.add(rule)

    def _dispatch(self, cmd: AnimationCommand) -> None:
        """Dispatch a single animation command to its registered handler."""
        handler = self._handlers.get(cmd.action)
        if handler is not None:
            handler(cmd)

    def construct(self) -> None:
        self._setup_scene()
        self._setup_chrome()

        for cmd in self._graph.commands:
            self._dispatch(cmd)

        self.wait(1.0)
