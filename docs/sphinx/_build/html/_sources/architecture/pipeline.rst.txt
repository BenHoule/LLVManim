Pipeline: IR to Animation
==========================

This page traces a single ``.ll`` file through every transformation step
from raw text to a rendered video frame.


Step 1 — Parse IR text (Ingest layer)
--------------------------------------

Entry point: :func:`llvmanim.ingest.parse_module_to_events`

.. code-block:: python

   from llvmanim.ingest import parse_module_to_events
   stream = parse_module_to_events("double.ll")

Internally, :func:`~llvmanim.ingest.llvm_events.parse_ir_to_events` does
the following:

1. Calls ``llvmlite.binding.parse_assembly(ir_text)`` to build an
   in-memory module object.
2. Calls ``module.verify()`` to ensure the IR is well-formed.
3. Iterates ``module.functions → blocks → instructions``.
4. For each instruction, determines the *opcode*, classifies it into an
   :data:`~llvmanim.transform.models.EventKind` via ``_kind_from_opcode``,
   and constructs an :class:`~llvmanim.transform.models.IREvent`.
5. Extracts **CFG edges** from terminator instructions:
   ``br``, ``switch``, ``invoke``, ``indirectbr``, ``callbr``.  Conditional
   ``br`` instructions produce two edges labelled ``"T"`` and ``"F"``.
6. Calls :func:`~llvmanim.ingest.display_lines.build_display_lines` on the
   raw IR text to produce a ``dict[function_name, list[str]]`` of cleaned
   source lines for the IR panel.

Opcode → EventKind classification
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Opcode(s)
     - Classified as
   * - ``alloca``
     - ``alloca``
   * - ``load``
     - ``load``
   * - ``store``
     - ``store``
   * - ``call``
     - ``call``
   * - ``ret``
     - ``ret``
   * - ``br``
     - ``br``
   * - ``add``, ``sub``, ``mul``, ``sdiv``, ``udiv``, ``srem``, ``urem``,
       ``shl``, ``lshr``, ``ashr``, ``and``, ``or``, ``xor``,
       ``fadd``, ``fsub``, ``fmul``, ``fdiv``, ``frem``
     - ``binop``
   * - ``icmp``, ``fcmp``
     - ``compare``
   * - everything else
     - ``other``

Output: ``ProgramEventStream``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

After Step 1 you have::

   ProgramEventStream(
       source_path = "double.ll",
       events      = [IREvent(function_name="double", block_name="entry",
                               opcode="alloca", kind="alloca", ...), ...],
       cfg_edges   = [CFGEdge(source="double::entry",
                               target="double::exit", kind="control_flow"), ...],
       display_lines = {"double": ["%a.addr = alloca i32, align 4", ...]},
   )

Step 2 — Build the scene graph (Transform layer)
-------------------------------------------------

Entry point: :func:`llvmanim.transform.scene.build_scene_graph`

.. code-block:: python

   from llvmanim.transform.scene import build_scene_graph
   graph = build_scene_graph(stream)

The transform layer performs five sub-steps:

2a. Group events into blocks
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``_group_blocks`` iterates ``stream.events`` and groups them by
``(function_name, block_name)`` into :class:`~llvmanim.transform.models.CFGBlock`
objects.  Each block records its ``terminator_opcode`` (from its last event)
and its ``memory_ops`` (all ``alloca`` / ``load`` / ``store`` events).

2b. Build scene edges
~~~~~~~~~~~~~~~~~~~~~

The ``stream.cfg_edges`` list (populated by the ingest layer) is converted
into :class:`~llvmanim.transform.models.SceneEdge` objects.

2c. Assign block roles
~~~~~~~~~~~~~~~~~~~~~~~

``_assign_roles`` computes in-degree and out-degree for each block from the
edge list, then assigns a :data:`~llvmanim.transform.models.BlockRole`:

* ``entry`` — in-degree 0
* ``exit`` — terminates with ``ret``
* ``branch`` — out-degree ≥ 2
* ``merge`` — in-degree ≥ 2
* ``linear`` — everything else

2d. Apply analysis metadata (optional)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If ``--import-analysis-metadata`` was provided, ``_apply_analysis_metadata``
copies ``idom``, ``dom_depth``, ``is_loop_header``, ``loop_depth``,
``loop_id``, and ``is_backedge_target`` onto each matching block.

2e. Build animation commands
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``_build_overlay_commands`` (for CFG mode) or the stack command builder
generates an ordered list of :class:`~llvmanim.transform.models.AnimationCommand`
objects.  These commands *are* the animation timeline — they encode
*what* to render, *on which node*, and *with what parameters*.

Output: ``SceneGraph``
~~~~~~~~~~~~~~~~~~~~~~

After Step 2::

   SceneGraph(
       nodes    = [SceneNode(id="double::entry", kind="cfg_block",
                              properties={role: "entry", ...}), ...],
       edges    = [SceneEdge(source="double::entry",
                              target="double::exit", label=""), ...],
       commands = [AnimationCommand(action="enter_block",
                                    target="double::entry"), ...],
       overlay  = None,
   )

Step 3 — Derive / import trace (optional, CFG mode)
-----------------------------------------------------

Entry point: :func:`llvmanim.transform.trace.derive_cfg_trace`

If ``--cfg-animate`` is used without ``--import-trace``, the CLI calls:

.. code-block:: python

   from llvmanim.transform.trace import derive_cfg_trace
   overlay = derive_cfg_trace(graph, function="double")
   graph.overlay = overlay

The tracer:

1. Finds the entry block (``SceneNode`` with ``role == "entry"``).
2. Performs a forward walk.
3. At each conditional branch, prefers the edge labelled ``"T"``.
4. Limits loop unrolling to ``max_loop_iterations`` (default 7) to prevent
   infinite loops.
5. Stops when a ``ret`` block is reached or no outgoing edges exist.

The resulting :class:`~llvmanim.transform.models.TraceOverlay` is attached to
``graph.overlay`` and later used by the renderer to determine block entry order.

Step 4 — Render (Render layer)
-------------------------------

Entry point: :class:`~llvmanim.render.stack_renderer.StackRenderer` or
:class:`~llvmanim.render.cfg_renderer.CFGRenderer`

For **stack animations**, the CLI instantiates ``StackRenderer`` and
calls Manim's ``render()`` method.  Internally:

1. ``_setup_scene`` creates Manim mobjects for each stack node.
2. ``construct`` (Manim's main entry point) iterates the ``commands`` list.
3. Each command is dispatched to a registered handler (see
   :doc:`rendering` for handler details).
4. Manim records each handler's animations as frames.

For **CFG animations**, ``CFGRenderer``:

1. Calls :func:`~llvmanim.ingest.dot_layout.compute_dot_layout` on the
   ``--dot-cfg`` file to get ``(x, y)`` positions for each block.
2. Uses :class:`~llvmanim.render.cfg_animation_scene._CoordMapper` to map
   DOT coordinates to Manim scene coordinates.
3. Creates block and edge mobjects via ``_build_block_mob`` and
   ``_build_edge_mob``.
4. Iterates ``graph.overlay.entry_order`` and dispatches ``enter_block``,
   ``traverse_edge``, and ``exit_block`` commands.

Step 5 — Encode output
-----------------------

After Manim finishes, the CLI post-processes the output:

* **MP4** — written directly by Manim into
  ``<outdir>/1080p60/<RendererClass>.mp4``.
* **GIF** — ``_convert_mp4_to_gif`` runs two ffmpeg passes (palette
  generation + palette application) to produce a dithered GIF.
* **JSON** — ``export_scene_graph_json`` serialises the ``SceneGraph``
  immediately after Step 2 (no rendering required).
* **DOT/PNG** — ``export_cfg_dot`` and ``export_cfg_png`` run after
  Step 2 (no rendering required).
