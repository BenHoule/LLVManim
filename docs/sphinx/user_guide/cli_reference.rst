CLI Reference
=============

All LLVManim functionality is accessed through a single command:

.. code-block:: bash

   uv run llvmanim [INPUT] [FLAGS...]
   # or, if installed system-wide:
   llvmanim [INPUT] [FLAGS...]


Positional argument
-------------------

.. option:: INPUT

   Path to an LLVM IR file (``.ll``).

   *Default:* ``tests/ingest/testdata/double.ll`` (useful for quick
   experiments without specifying a file).

Core output flags
-----------------

.. option:: --json

   Export the scene graph to ``<outdir>/<name>_scene_graph.json``.

   The JSON file contains every node, edge, and animation command derived
   from the IR.  Useful for debugging or piping into other tools.  Does
   not require Manim.

.. option:: --draw

   Export the CFG as a Graphviz DOT file and render it to PNG.

   Writes ``<outdir>/cfg_<name>.dot`` and ``<outdir>/cfg_<name>.png``.
   Requires the Graphviz Python package (``graphviz``) and the ``dot``
   binary.  Does not require Manim.

Animation flags
---------------

.. option:: --animate

   Render a stack animation video using Manim CE.

   The video is written into ``<outdir>/1080p60/`` as an MP4 (or GIF if
   ``--format gif``).

.. option:: --preview

   Render the animation **and** open the result in your default video
   viewer.  Implies ``--animate``.

.. option:: --cfg-animate

   Render a CFG traversal animation.  Requires ``--dot-cfg``.

   If no ``--import-trace`` is provided, LLVManim auto-derives a static
   trace and asks for confirmation (use ``-y`` to skip).

IR display mode
---------------

.. option:: --ir-mode {basic,rich,rich-ssa}

   Controls what the stack animation renders.

   :``basic``: Stack-only.  A yellow badge flashes on the active stack cell.
               This is the default and the fastest to render.
   :``rich``:  Two-column layout — IR source on the left with a moving
               yellow cursor, call stack on the right.
   :``rich-ssa``: Three-column layout — IR source | SSA values panel |
                  call stack.  The SSA panel shows live value assignments
                  as each instruction is animated.

   *Default:* ``basic``

   See :doc:`animation_modes` for screenshots and detailed explanations.

Animation control
-----------------

.. option:: --speed MULTIPLIER

   Scale the animation speed.  ``2.0`` renders twice as fast; ``0.5``
   renders at half speed.

   *Default:* ``1.0``

Output format and paths
-----------------------

.. option:: --outdir PATH

   Directory for all output artifacts.  Created if it does not exist.

   *Default:* ``.`` (current working directory)

.. option:: --format {mp4,gif}

   Animation output format.

   :``mp4``: Standard MP4 via Manim's built-in encoder. **(default)**
   :``gif``: Convert the MP4 to a GIF via a palette-based ffmpeg workflow
             that keeps memory usage low.

.. option:: --gif-fps FPS

   Frame rate used when ``--format gif``.

   *Default:* ``12``

.. option:: --gif-width PX

   Width in pixels of the output GIF.

   *Default:* ``960``

.. option:: -n NAME, --name NAME

   Base name for all output files.  Affects the stem of JSON, DOT, PNG,
   and video files.

   *Default:* stem of the input file (e.g. ``double`` for ``double.ll``).

CFG animation options
---------------------

.. option:: --dot-cfg PATH

   Path to a ``.dot`` layout file produced by::

     opt -passes=dot-cfg -disable-output my_file.ll

   This file provides the node positions and edge routing used by the
   CFG animation.  Required when ``--cfg-animate`` is used.

Trace import / export
----------------------

A *trace* is a JSON file that records the sequence of blocks visited and
edges traversed during an execution.  You can import traces produced by a
real runtime or export the auto-derived static trace for later re-use.

.. option:: --import-trace PATH

   Load a trace from a JSON file and use it as the execution path for
   ``--cfg-animate``.

.. option:: --export-trace PATH

   Export the current trace overlay to a JSON file.

CFG edge import / export
-------------------------

.. option:: --import-cfg-edges PATH

   Replace the CFG edges extracted from the IR with edges loaded from a
   JSON file.  Useful when opt-derived edges are incorrect or when testing
   with custom topologies.

.. option:: --export-cfg-edges PATH

   Export the CFG edges extracted from the IR to a JSON file.

Analysis metadata import / export
-----------------------------------

Analysis metadata captures dominator-tree and loop information computed
by LLVM opt passes (``print<postdomtree>``).  It enriches scene nodes with
``idom``, ``dom_depth``, ``is_loop_header``, etc.

.. option:: --import-analysis-metadata PATH

   Load analysis metadata from a JSON file.

.. option:: --export-analysis-metadata PATH

   Export the analysis metadata derived from the scene graph to a JSON file.

Miscellaneous flags
-------------------

.. option:: -y, --yes

   Skip interactive confirmation prompts (e.g. when auto-deriving a CFG
   trace).

.. option:: -c, --C

   Treat INPUT as a C source file.  LLVManim calls ``clang`` automatically
   to compile it to IR before processing:

   .. code-block:: bash

      uv run llvmanim my_program.c --C --animate

   Compilation uses: ``-g -O2 -fno-strict-aliasing -fno-inline
   -fno-discard-value-names -S -emit-llvm``.

Environment variables
---------------------

All environment variables are optional.  When unset, LLVManim falls back
to automatic discovery using ``$PATH`` and (on Linux) version-sorted
``/usr/lib/llvm-*/bin/`` directories.

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Variable
     - Effect
   * - ``LLVM_BIN_DIR``
     - Explicit path to the directory containing LLVM binaries
       (``clang``, ``opt``, …)
   * - ``NO_LLVM_DEFAULT_SEARCH``
     - Set to ``1`` to disable Linux-specific ``/usr/lib/llvm-*/bin``
       auto-discovery
   * - ``CLANG``
     - Full path to the ``clang`` binary
   * - ``OPT``
     - Full path to the ``opt`` binary
   * - ``DOT``
     - Full path to the Graphviz ``dot`` binary
   * - ``FFMPEG``
     - Full path to the ``ffmpeg`` binary

Common invocation patterns
---------------------------

.. code-block:: bash

   # Quick scan: what does this IR produce?
   uv run llvmanim my.ll --json

   # Full static export — no Manim needed
   uv run llvmanim my.ll --json --draw --export-cfg-edges edges.json

   # Basic stack animation, watch it immediately
   uv run llvmanim my.ll --animate --preview

   # Rich-SSA animation, GIF, 2× speed
   uv run llvmanim my.ll --animate --ir-mode rich-ssa --format gif --speed 2.0

   # CFG traversal with auto-derived trace, skip confirmation
   uv run llvmanim my.ll --cfg-animate --dot-cfg .my.dot -y

   # Compile C directly and animate
   uv run llvmanim my_program.c --C --animate --ir-mode rich

   # Use a custom trace from a profiler
   uv run llvmanim my.ll --cfg-animate --dot-cfg .my.dot --import-trace trace.json
