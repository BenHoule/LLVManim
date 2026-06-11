Quickstart
==========

This tutorial takes you from zero to your first LLVManim output in five
steps.  It uses the ``double.ll`` file that ships with the repository — a
small compiled C function that doubles an integer.


Prerequisites
-------------

Complete :doc:`installation` first.  You need:

* A working ``uv sync --dev`` environment.
* At minimum, Graphviz (``dot``) for the no-Manim path.

Step 1: Inspect the input
--------------------------

Open ``double.ll`` in the project root.  It looks like this (abridged)::

   ; ModuleID = 'double.c'
   source_filename = "double.c"
   target datalayout = "e-m:e-p270:32:32-..."
   target triple = "x86_64-pc-linux-gnu"

   ; Function Attrs: noinline nounwind optnone uwtable
   define dso_local i32 @double(i32 noundef %a) #0 {
   entry:
     %a.addr = alloca i32, align 4
     store i32 %a, ptr %a.addr, align 4
     %0 = load i32, ptr %a.addr, align 4
     %mul = mul nsw i32 %0, 2
     ret i32 %mul
   }

This single-block function allocates a stack slot for the argument, loads it,
multiplies by 2, and returns.

Step 2: Export a scene-graph JSON  (no Manim needed)
-----------------------------------------------------

.. code-block:: bash

   uv run llvmanim double.ll --json --outdir llvmanim_out

This produces ``llvmanim_out/double_scene_graph.json`` — a machine-readable
description of all the nodes, edges, and animation commands for the scene.
Open it to see the full data model.

Step 3: Draw the CFG  (Graphviz)
---------------------------------

.. code-block:: bash

   uv run llvmanim double.ll --draw --outdir llvmanim_out

This writes ``llvmanim_out/double_cfg.dot`` and
``llvmanim_out/double_cfg.png``.  Open the PNG to see the control-flow graph
with T/F labels on conditional branches.

Step 4: Render a stack animation  (Manim required)
---------------------------------------------------

.. code-block:: bash

   uv run llvmanim double.ll --animate --outdir llvmanim_out

Manim generates an MP4 in ``llvmanim_out/1080p60/``.

**Rich mode** — adds a side-by-side IR source panel with a moving cursor:

.. code-block:: bash

   uv run llvmanim double.ll --animate --ir-mode rich --outdir llvmanim_out

**Rich-SSA mode** — adds a third column showing live SSA values:

.. code-block:: bash

   uv run llvmanim double.ll --animate --ir-mode rich-ssa --outdir llvmanim_out

Step 5: Animate a CFG traversal
---------------------------------

First, generate a DOT layout file using ``opt``:

.. code-block:: bash

   opt -passes=dot-cfg -disable-output double.ll
   # Produces .double.dot (note the leading dot)

Then run the CFG animation:

.. code-block:: bash

   uv run llvmanim double.ll --cfg-animate --dot-cfg .double.dot --outdir llvmanim_out

LLVManim auto-derives the execution trace (starting from ``main``, preferring
the true branch at each conditional) and animates the traversal.

Tip: preview mode
~~~~~~~~~~~~~~~~~

Add ``--preview`` to any ``--animate`` or ``--cfg-animate`` command to have
the video open automatically in your default viewer after rendering.

.. code-block:: bash

   uv run llvmanim double.ll --animate --preview

Next steps
----------

* Read :doc:`../user_guide/cli_reference` for every available flag.
* Read :doc:`../user_guide/animation_modes` to understand the three stack
  modes and the CFG mode in depth.
* Read :doc:`../architecture/pipeline` for a detailed walkthrough of how
  LLVManim transforms raw IR text into an animated video.

Using your own C file
----------------------

Compile your own C source to IR with the ``--C`` flag:

.. code-block:: bash

   uv run llvmanim my_program.c --C --animate --outdir out/

Or compile manually for full control over optimisation flags:

.. code-block:: bash

   clang -g -O0 -fno-inline -fno-discard-value-names -S -emit-llvm my_program.c -o my_program.ll
   uv run llvmanim my_program.ll --json --draw --cfg-animate ...
