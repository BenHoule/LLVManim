Output Formats
==============

LLVManim produces several kinds of output.  This page documents the schema
and content of each.


Scene-graph JSON (``--json``)
------------------------------

**File:** ``<outdir>/<name>_scene_graph.json``

The JSON file is a serialised :class:`~llvmanim.transform.models.SceneGraph`.
It is the canonical machine-readable representation of everything LLVManim
knows about the IR — topology, events, animation timeline, and optional
runtime trace.

Top-level structure
~~~~~~~~~~~~~~~~~~~

.. code-block:: json

   {
     "nodes": [ ... ],
     "edges": [ ... ],
     "commands": [ ... ],
     "overlay": null
   }

nodes
^^^^^

Each element represents a :class:`~llvmanim.transform.models.SceneNode`:

.. code-block:: json

   {
     "id": "main::entry",
     "label": "entry",
     "kind": "cfg_block",
     "animation_hint": "",
     "block": {
       "id": "main::entry",
       "name": "entry",
       "function_name": "main",
       "terminator_opcode": "ret",
       "indegree": 0,
       "outdegree": 0,
       "role": "entry",
       "events": [ ... ]
     }
   }

``kind`` values:

* ``cfg_block`` — a basic block from the IR.
* ``stack_frame`` — a function call frame (stack mode).
* ``stack_slot`` — a memory slot inside a frame (stack mode).

Each ``event`` inside ``block.events`` is a serialised
:class:`~llvmanim.transform.models.IREvent`:

.. code-block:: json

   {
     "function_name": "main",
     "block_name": "entry",
     "opcode": "alloca",
     "text": "%a.addr = alloca i32, align 4",
     "kind": "alloca",
     "index_in_function": 0,
     "debug_line": 3,
     "operands": []
   }

edges
^^^^^

Each element is a serialised :class:`~llvmanim.transform.models.SceneEdge`:

.. code-block:: json

   {
     "source": "main::entry",
     "target": "main::merge",
     "label": "T",
     "kind": "control_flow"
   }

``label`` is ``"T"`` or ``"F"`` for conditional branches; empty for
unconditional branches and call edges.

commands
^^^^^^^^

An ordered list of :class:`~llvmanim.transform.models.AnimationCommand`
objects — the animation timeline.  Each command has an ``action`` (one of
the ``ActionKind`` literals), a ``target`` node/edge ID, an optional
``event``, and an ``params`` dict:

.. code-block:: json

   {
     "action": "animate_binop",
     "target": "main::entry",
     "event": { ... },
     "params": { "operands": ["%a", "2"], "result": "%mul" }
   }

Full list of ``action`` values:

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Action
     - Meaning
   * - ``create_stack_slot``
     - Create a new memory slot in the active frame.
   * - ``animate_memory_read``
     - Flash a read animation on a memory cell.
   * - ``animate_memory_write``
     - Flash a write animation on a memory cell.
   * - ``animate_binop``
     - Animate a binary operation on a slot.
   * - ``animate_compare``
     - Animate a comparison operation.
   * - ``push_stack_frame``
     - Push a new call frame.
   * - ``pop_stack_frame``
     - Pop the top call frame.
   * - ``highlight_branch``
     - Highlight the taken branch edge.
   * - ``signal_stack_underflow``
     - Signal an unexpected underflow condition.
   * - ``enter_block``
     - Highlight a CFG block as "entered".
   * - ``exit_block``
     - Dim a CFG block back to resting state.
   * - ``traverse_edge``
     - Animate traversal along a CFG edge.

overlay (optional)
^^^^^^^^^^^^^^^^^^

Null unless a trace was imported or auto-derived.  See
:class:`~llvmanim.transform.models.TraceOverlay` for the schema.

DOT and PNG (``--draw``)
-------------------------

**Files:**

* ``<outdir>/cfg_<name>.dot`` — a Graphviz DOT file.
* ``<outdir>/cfg_<name>.png`` — a rendered PNG (if Graphviz Python package
  is installed).

The DOT file encodes the CFG with:

* Node labels showing block ID, role, terminator, and memory ops.
* Directed edges with ``T`` / ``F`` labels on conditional branches.
* Orthogonal edge routing (``splines=ortho``).
* When a :class:`~llvmanim.transform.models.TraceOverlay` is present:
  visited nodes and edges are coloured distinctly; unvisited elements are
  dimmed.

Render to PNG manually
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   dot -Tpng cfg_double.dot -o cfg_double.png

CFG edge JSON
~~~~~~~~~~~~~

.. code-block:: bash

   uv run llvmanim my.ll --export-cfg-edges edges.json

Each element:

.. code-block:: json

   {
     "source": "main::entry",
     "target": "main::then",
     "kind": "control_flow",
     "label": "T",
     "source_file": "my.ll"
   }

Trace JSON
~~~~~~~~~~

.. code-block:: bash

   uv run llvmanim my.ll --cfg-animate --dot-cfg .my.dot --export-trace trace.json -y

.. code-block:: json

   {
     "visited_nodes": ["main::entry", "main::then", "main::merge"],
     "traversed_edges": [["main::entry", "main::then"], ["main::then", "main::merge"]],
     "entry_order": ["main::entry", "main::then", "main::merge"],
     "termination_reason": "ret",
     "source_file": "my.ll"
   }

Analysis metadata JSON
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   uv run llvmanim my.ll --export-analysis-metadata meta.json

.. code-block:: json

   {
     "main::entry": {
       "idom": null,
       "dom_depth": 0,
       "is_loop_header": false,
       "loop_depth": 0,
       "loop_id": null,
       "is_backedge_target": false
     }
   }

Video output
------------

All video output lands in ``<outdir>/`` when using ``--format gif`` or in
``<outdir>/1080p60/`` when using Manim's default MP4 path.

MP4
~~~

Manim CE renders at 1080p 60 fps by default.  The file is named after
the renderer class (e.g. ``StackRenderer.mp4``).

GIF
~~~

When ``--format gif``, LLVManim first renders the MP4 and then converts
it with a two-pass ffmpeg palette workflow:

1. **Pass 1** — generate a palette from the video frames
   (``palettegen=stats_mode=diff``).
2. **Pass 2** — apply the palette with dithering
   (``paletteuse=dither=sierra2_4a``).

This approach keeps memory usage much lower than compositing frames
in-process and produces high-quality dithered output.

The GIF is written to ``<outdir>/<name>.gif``.  Control its size with
``--gif-fps`` and ``--gif-width``.
