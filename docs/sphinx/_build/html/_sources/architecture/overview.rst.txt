Architecture Overview
=====================

LLVManim is structured as four strictly layered subsystems.  Each layer has
a single, well-defined responsibility, and the import boundaries are enforced
by `import-linter`_.  No layer may import from a layer above it.

.. _import-linter: https://import-linter.readthedocs.io/

.. figure:: /_static/logo.svg
   :align: center
   :alt: LLVManim four-layer architecture overview

   Four-layer architecture: CLI → Render → Transform → Ingest


The four layers
---------------

.. list-table::
   :header-rows: 1
   :widths: 20 25 55

   * - Layer
     - Package
     - Responsibility
   * - **CLI**
     - ``llvmanim.cli``
     - Argument parsing, user interaction, orchestration.
       Calls into all lower layers.  The only layer that may import from all others.
   * - **Render**
     - ``llvmanim.render``
     - Manim scene construction, animation execution, JSON/DOT export.
       Imports from ``transform`` and ``ingest``.
   * - **Transform**
     - ``llvmanim.transform``
     - Scene graph construction, block role assignment, trace derivation.
       Imports from ``ingest`` only.
   * - **Ingest**
     - ``llvmanim.ingest``
     - IR parsing, CFG edge extraction, supplemental I/O.
       Imports from nothing in the project.

CLI layer
~~~~~~~~~

.. figure:: /_static/01a_cli_layer.svg
   :align: center
   :alt: CLI layer diagram

The CLI layer is a thin orchestration shell.  :func:`~llvmanim.cli.main.main`
parses ``argparse`` flags, calls ``parse_module_to_events``, then
``build_scene_graph``, then hands off to the appropriate renderer or exporter.
It is the only layer permitted to know about all the others.

Ingest layer
~~~~~~~~~~~~

.. figure:: /_static/01b_ingest_layer.svg
   :align: center
   :alt: Ingest layer diagram

The ingest layer is responsible for:

* Parsing LLVM IR text into a typed :class:`~llvmanim.transform.models.ProgramEventStream`.
* Extracting control-flow edges from terminator instructions.
* Providing supplemental I/O for CFG edges, traces, and analysis metadata.
* Building display-ready IR lines for the render layer.
* Parsing Graphviz DOT layout files for CFG positioning.

It has **no knowledge of scenes, animations, or CLI flags**.

Transform layer
~~~~~~~~~~~~~~~

.. figure:: /_static/01c_transform_layer.svg
   :align: center
   :alt: Transform layer diagram

The transform layer converts a flat ``ProgramEventStream`` into a structured
:class:`~llvmanim.transform.models.SceneGraph`:

* Groups IR events into :class:`~llvmanim.transform.models.CFGBlock` objects.
* Assigns :data:`~llvmanim.transform.models.BlockRole` to each block based on
  graph topology (in-degree, out-degree, terminator).
* Builds ``SceneNode`` / ``SceneEdge`` objects.
* Generates an ordered list of :class:`~llvmanim.transform.models.AnimationCommand`
  objects — the animation timeline.
* Derives static execution traces for CFG traversal.

It has **no knowledge of Manim, rendering, or CLI**.

Render layer
~~~~~~~~~~~~

.. figure:: /_static/01d_render_layer.svg
   :align: center
   :alt: Render layer diagram

The render layer contains all Manim-facing code:

* :class:`~llvmanim.render.command_driven_scene.CommandDrivenScene` — the
  abstract base class for all scenes.  It iterates the ``commands`` list and
  dispatches each :class:`~llvmanim.transform.models.AnimationCommand` to a
  registered handler.
* :class:`~llvmanim.render.stack_renderer.StackRenderer` — the stack
  animation renderer (basic / rich / rich-ssa modes).
* :class:`~llvmanim.render.cfg_renderer.CFGRenderer` — the CFG traversal
  renderer.
* Export helpers: :func:`~llvmanim.render.json_export.export_scene_graph_json`,
  :func:`~llvmanim.render.graphviz_export.export_cfg_dot`, and
  :func:`~llvmanim.render.graphviz_export.export_cfg_png`.

Data flow summary
-----------------

::

   LLVM IR text (.ll file)
         │
         ▼  llvmanim.ingest.parse_module_to_events()
   ProgramEventStream
     ├── events: list[IREvent]
     ├── cfg_edges: list[CFGEdge]
     └── display_lines: dict[str, list[str]]
         │
         ▼  llvmanim.transform.scene.build_scene_graph()
   SceneGraph
     ├── nodes: list[SceneNode]
     ├── edges: list[SceneEdge]
     ├── commands: list[AnimationCommand]
     └── overlay: TraceOverlay | None
         │
         ├──▶  json_export  →  scene_graph.json
         ├──▶  graphviz_export  →  cfg.dot / cfg.png
         └──▶  StackRenderer / CFGRenderer  →  video (MP4 / GIF)

See :doc:`pipeline` for the complete step-by-step data-flow description, and
:doc:`data_model` for field-by-field documentation of every dataclass.
