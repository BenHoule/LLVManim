Animation Modes
===============

LLVManim offers four distinct animation modes, each targeting a different
visualisation need.  Choose the one that matches your audience and goal.


Stack animation modes (``--animate``)
--------------------------------------

All three stack modes are triggered by ``--animate``.  The IR display mode
(``--ir-mode``) selects which variant is rendered.

basic (default)
~~~~~~~~~~~~~~~

**Trigger:** ``uv run llvmanim my.ll --animate``

The simplest mode.  Renders a single call-stack column:

* Each function call pushes a labelled frame onto the stack.
* Each ``alloca`` instruction creates a new slot inside the active frame.
* ``load`` / ``store`` flash an animation on the relevant memory cell.
* ``binop`` and ``compare`` animate on the associated slot.
* A bright yellow badge flashes on the active cell as each instruction
  executes.
* Function returns pop the frame off the stack.

**Best for:** quickly communicating call-stack behaviour to newcomers who do
not need to see the IR source.

rich
~~~~

**Trigger:** ``uv run llvmanim my.ll --animate --ir-mode rich``

Two-column layout:

* **Left column** — the IR source code for the active function, with a
  moving yellow spotlight cursor that tracks the current instruction.
* **Right column** — the same call-stack view as ``basic``.

The IR source is drawn from
:func:`~llvmanim.ingest.display_lines.build_display_lines`, which strips
comments and normalises whitespace.

**Best for:** teaching compiler courses or explaining generated code.

rich-ssa
~~~~~~~~~

**Trigger:** ``uv run llvmanim my.ll --animate --ir-mode rich-ssa``

Three-column layout:

* **Left column** — IR source with spotlight cursor (same as ``rich``).
* **Centre column** — SSA values panel.  As each instruction executes, its
  result is pushed onto the panel as a ``%name = value`` entry styled with
  operation-specific colours (see
  :mod:`~llvmanim.render.ssa_formatting`).
* **Right column** — call stack.

When a function returns, the SSA panel entries for that frame fade out and
the vertical space is reclaimed smoothly.

**Best for:** explaining SSA form, data-flow, or the effect of individual
optimisation passes.

CFG animation mode (``--cfg-animate``)
---------------------------------------

**Trigger:** ``uv run llvmanim my.ll --cfg-animate --dot-cfg .my.dot``

Renders the Control-Flow Graph and animates a traversal path through it:

1. The CFG is laid out using positions from the ``--dot-cfg`` file (produced
   by ``opt -passes=dot-cfg``).
2. Blocks are drawn as labelled rectangles; edges are drawn as directed
   arrows with T/F labels on conditional branches.
3. The traversal steps through the trace one entry at a time:

   - **enter_block** — the target block brightens/highlights.
   - **traverse_edge** — the edge connecting the last and current block
     animates.
   - **exit_block** — the block dims back to its resting colour.

Trace sources
~~~~~~~~~~~~~

The traversal order comes from a :class:`~llvmanim.transform.models.TraceOverlay`.
There are three ways to supply one:

1. **Auto-derived** (default) — LLVManim calls
   :func:`~llvmanim.transform.trace.derive_cfg_trace`, which walks the CFG
   from the entry block, always preferring the true (T) branch at
   conditionals and unrolling loops up to seven iterations.  You will be
   asked to confirm before this happens (use ``-y`` to skip).

2. **Imported from JSON** — ``--import-trace path/to/trace.json``.  Use this
   to replay a trace captured from a real execution.

3. **Previously exported** — combine ``--export-trace`` on a first run and
   ``--import-trace`` on subsequent runs to keep the trace stable.

Speed and output format
-----------------------

Both ``--animate`` and ``--cfg-animate`` respect:

* ``--speed MULTIPLIER`` — scale the duration of every animation step.
* ``--format {mp4,gif}`` — output format.
* ``--gif-fps FPS`` / ``--gif-width PX`` — GIF parameters.
* ``--preview`` — open the video after rendering.

Example comparison
------------------

.. code-block:: bash

   # Same IR, three different perspectives:
   uv run llvmanim double.ll --animate                        # basic
   uv run llvmanim double.ll --animate --ir-mode rich         # rich
   uv run llvmanim double.ll --animate --ir-mode rich-ssa     # rich-ssa

   # Then the CFG:
   opt -passes=dot-cfg -disable-output double.ll
   uv run llvmanim double.ll --cfg-animate --dot-cfg .double.dot -y
