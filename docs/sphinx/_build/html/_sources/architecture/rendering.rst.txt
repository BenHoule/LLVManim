Rendering Architecture
======================

This page explains how the render layer turns a
:class:`~llvmanim.transform.models.SceneGraph` into animated Manim frames.


CommandDrivenScene — the executor pattern
-----------------------------------------

.. figure:: /_static/01d1_animation_renderers.svg
   :align: center
   :alt: Animation renderer diagram

:class:`~llvmanim.render.command_driven_scene.CommandDrivenScene` is the
abstract base class for all LLVManim scenes.  It inherits from Manim's
:class:`manim.Scene` and implements a simple **handler registry** pattern:

1. The subclass calls ``_register_handler(action_kind, handler_fn)`` for
   each ``ActionKind`` it knows how to render.
2. Manim calls ``construct()`` to start the scene.
3. ``construct`` calls ``_setup_scene()`` and ``_setup_chrome()`` (both
   hooks that subclasses override), then iterates
   ``graph.commands``.
4. For each :class:`~llvmanim.transform.models.AnimationCommand`, ``_dispatch``
   looks up the registered handler and calls it.  Unknown action kinds are
   silently skipped.

This design means that new action kinds can be added without modifying the
base class — the subclass simply registers an additional handler.

Speed scaling
~~~~~~~~~~~~~

All run-time durations are multiplied by ``1 / speed`` via the ``_rt(base)``
helper.  Setting ``--speed 2.0`` halves every animation duration; ``--speed
0.5`` doubles them.

StackRenderer
-------------

.. figure:: /_static/01d1_animation_renderers.svg
   :align: center
   :alt: Stack renderer modes

:class:`~llvmanim.render.stack_renderer.StackRenderer` extends
``CommandDrivenScene`` and handles seven action kinds:

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Action
     - What the handler does
   * - ``push_stack_frame``
     - Creates a new frame header ``Rectangle`` + ``Text`` and slides it in
       from above.  Each frame gets a colour from a rotating palette.
   * - ``pop_stack_frame``
     - Fades out the top frame (and any SSA rows owned by it in rich-ssa
       mode), then reclaims the vertical space.
   * - ``create_stack_slot``
     - Appends a new slot ``Rectangle`` + label ``Text`` inside the active
       frame, scrolling existing content down.
   * - ``animate_memory_read``
     - Flashes a brief highlight on the target slot (``FadeIn`` + ``FadeOut``
       of a coloured overlay).
   * - ``animate_memory_write``
     - Same as read, but with a write-colour overlay.
   * - ``animate_binop``
     - In rich-ssa mode: pushes a new SSA row to the centre panel showing
       the result name, operands, and the operation in the appropriate
       colour from :data:`~llvmanim.render.ssa_formatting.OP_COLORS`.
   * - ``animate_compare``
     - Same as ``animate_binop`` for comparison operations.

IR panel (rich and rich-ssa modes)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When ``ir_mode`` is ``"rich"`` or ``"rich-ssa"``, ``StackRenderer``:

1. Reads ``stream.display_lines[function_name]`` to get cleaned IR source
   lines (populated by the ingest layer — no file re-read).
2. Creates a ``VGroup`` of ``Text`` objects, one per line.
3. A ``SurroundingRectangle`` cursor advances to the ``Text`` object
   corresponding to the current instruction's ``index_in_function``.
4. On function call, the IR panel ``FadeTransform`` animates to the callee's IR.
5. On function return, it ``FadeTransform`` animates back to the caller's IR.

SSA panel (rich-ssa mode only)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The SSA panel is a vertical stack of ``VGroup`` rows.  Each row shows::

   %result_name  ←  operand1  OP  operand2

Rows are colour-coded by operation type (see
:mod:`~llvmanim.render.ssa_formatting`).  When a frame is popped, all SSA
rows belonging to that frame fade out and their vertical space is reclaimed
by smoothly translating the rows below upward.

CFGRenderer
-----------

.. figure:: /_static/01d2_cfg_renderer.svg
   :align: center
   :alt: CFG renderer diagram

:class:`~llvmanim.render.cfg_renderer.CFGRenderer` handles three action kinds:

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Action
     - What the handler does
   * - ``enter_block``
     - Animates the block's fill from its resting colour to the "active"
       colour using ``FadeIn`` of an overlay, then brightens the text.
   * - ``exit_block``
     - Transitions the block from "active" to "visited" colour.
   * - ``traverse_edge``
     - Draws a moving ``Triangle`` arrowhead along the edge spline from
       source to target.

Coordinate mapping
~~~~~~~~~~~~~~~~~~

Graphviz DOT coordinates use a different scale and origin than Manim's
scene coordinates.  :class:`~llvmanim.render.cfg_animation_scene._CoordMapper`
normalises DOT bounding-box coordinates to Manim's ``[-7, 7] × [-4, 4]``
world space, with a configurable margin.

Building mobjects
~~~~~~~~~~~~~~~~~

* ``_build_block_mob(node, x, y, w, h)`` — creates a ``VGroup`` containing
  a ``Rectangle`` background and a ``Text`` label.  The fill colour is
  determined by the block's ``animation_hint``.
* ``_build_edge_mob(edge, spline_pts, label)`` — creates a ``VGroup``
  containing a ``CubicBezier`` path and an optional ``Text`` label at the
  midpoint.  The edge is rendered in the "resting" colour initially.

Export helpers
--------------

.. figure:: /_static/01d3_export.svg
   :align: center
   :alt: Export helpers diagram

The render layer contains two export modules that do **not** require Manim:

``json_export``
~~~~~~~~~~~~~~~

:func:`~llvmanim.render.json_export.export_scene_graph_json` serialises a
:class:`~llvmanim.transform.models.SceneGraph` to JSON.  It recursively
converts every dataclass field to a plain dict/list, handling the
``IREvent | None`` union in ``AnimationCommand.event`` gracefully.

``graphviz_export``
~~~~~~~~~~~~~~~~~~~~

* :func:`~llvmanim.render.graphviz_export.export_cfg_dot` writes a
  Graphviz DOT file.  Node IDs containing ``::`` are sanitised to
  ``__`` (Graphviz-safe).  When a
  :class:`~llvmanim.transform.models.TraceOverlay` is present, visited
  elements are highlighted and unvisited ones are dimmed.
* :func:`~llvmanim.render.graphviz_export.export_cfg_png` calls the
  Graphviz Python package's ``render()`` method to produce a PNG.

SSA formatting
--------------

:mod:`~llvmanim.render.ssa_formatting` is a shared module used by
``StackRenderer`` in rich-ssa mode.  It provides:

* :data:`~llvmanim.render.ssa_formatting.OP_COLORS` — a dict mapping binary
  opcode names to Manim colour objects.
* :func:`~llvmanim.render.ssa_formatting.format_display_value` — formats an
  SSA result for the value panel (e.g. ``"%mul = 2 × %a"``).
* :func:`~llvmanim.render.ssa_formatting.extract_ssa_name` — extracts the
  ``%name`` from an instruction text string.

The module contains a deliberately simple, singleton swap-point
(``display_value``) that will be replaced when numeric runtime values are
added in a future milestone.
