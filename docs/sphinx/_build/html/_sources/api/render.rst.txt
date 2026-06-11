llvmanim.render
===============

The render layer contains all Manim-facing code.  It takes a
:class:`~llvmanim.transform.models.SceneGraph` from the transform layer and
produces an animated video, or exports it to JSON / DOT / PNG.

.. admonition:: Manim dependency

   All classes in this layer import from ``manim``.  When building the docs,
   ``manim`` and ``manimgl`` are mocked out via ``autodoc_mock_imports``.


llvmanim.render (package)
--------------------------

Public API re-exports:
:class:`~llvmanim.render.stack_renderer.StackRenderer`,
:class:`~llvmanim.render.cfg_renderer.CFGRenderer`,
:class:`~llvmanim.render.command_driven_scene.CommandDrivenScene`,
:func:`~llvmanim.render.json_export.export_scene_graph_json`,
:func:`~llvmanim.render.graphviz_export.export_cfg_dot`,
:func:`~llvmanim.render.graphviz_export.export_cfg_png`.

.. automodule:: llvmanim.render
   :members:
   :undoc-members:

llvmanim.render.command_driven_scene
-------------------------------------

Abstract base class for all LLVManim Manim scenes.  Implements the handler
registry and animation dispatch loop.

.. automodule:: llvmanim.render.command_driven_scene
   :members:
   :undoc-members:

llvmanim.render.stack_renderer
--------------------------------

Stack animation renderer.  Handles push/pop frames, slot creation, memory
animations, and the optional IR panel / SSA panel in rich modes.

.. automodule:: llvmanim.render.stack_renderer
   :members:
   :undoc-members:

llvmanim.render.cfg_renderer
-----------------------------

CFG traversal renderer.  Positions nodes from a DOT layout file and animates
an execution path through the graph.

.. automodule:: llvmanim.render.cfg_renderer
   :members:
   :undoc-members:

llvmanim.render.cfg_animation_scene
-------------------------------------

Low-level helpers used by :class:`~llvmanim.render.cfg_renderer.CFGRenderer`:
coordinate mapping, block mobject builder, edge mobject builder.

.. automodule:: llvmanim.render.cfg_animation_scene
   :members:
   :undoc-members:

llvmanim.render.ssa_formatting
--------------------------------

SSA value formatting for the rich-ssa bridge panel.
:func:`~llvmanim.render.ssa_formatting.format_display_value` is the single
swap-point for future numeric runtime values.

.. automodule:: llvmanim.render.ssa_formatting
   :members:
   :undoc-members:

llvmanim.render.json_export
----------------------------

Serialise a :class:`~llvmanim.transform.models.SceneGraph` to a JSON file.

.. automodule:: llvmanim.render.json_export
   :members:
   :undoc-members:

llvmanim.render.graphviz_export
---------------------------------

Export the CFG as a Graphviz DOT file and render it to PNG.

.. automodule:: llvmanim.render.graphviz_export
   :members:
   :undoc-members:
