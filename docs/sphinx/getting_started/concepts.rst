Key Concepts
============

This page provides the background knowledge you need to use LLVManim
effectively.  If you already know LLVM IR, SSA form, and Manim, feel free to
skip straight to :doc:`installation`.


What is LLVM?
-------------

LLVM is a collection of modular compiler and toolchain components, most
commonly known as the backbone of the ``clang`` C/C++ compiler.  At its core
LLVM defines an **intermediate representation** (IR) — a typed, low-level
assembly-like language that every frontend (C, C++, Rust, Swift, …) compiles
*to*, and that LLVM's optimisers and backends consume.

Because IR is the common currency of all LLVM-based compilers, being able to
read and understand it is a powerful skill for anyone who works with compiled
languages.

What is LLVM IR?
----------------

LLVM IR is a static single-assignment (SSA) language that looks like a
typed, infinite-register assembly.  Here is a short example::

   define i32 @add(i32 %a, i32 %b) {
   entry:
     %result = add i32 %a, %b
     ret i32 %result
   }

Key features:

* **Typed** — every value has an explicit type (``i32``, ``i64``, ``float``,
  ``ptr``, …).
* **Functions** — a module contains one or more ``define`` blocks.
* **Basic blocks** — each function is split into *basic blocks* (labelled
  sections).  A basic block is a straight-line sequence of instructions that
  ends with a *terminator* (``br``, ``ret``, ``switch``, …).
* **Infinite virtual registers** — temporary values are named ``%name`` and
  each one is defined exactly once (SSA form, see below).
* **Memory via alloca / load / store** — instead of registers with
  side-effects, IR uses explicit heap-like stack slots (``alloca``) and
  explicit memory operations (``load``, ``store``).

Event kinds in LLVManim
~~~~~~~~~~~~~~~~~~~~~~~

LLVManim classifies every IR instruction into one of nine *event kinds*:

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Kind
     - Description
   * - ``alloca``
     - Stack slot allocation (``%x = alloca i32``)
   * - ``load``
     - Memory read (``%v = load i32, ptr %x``)
   * - ``store``
     - Memory write (``store i32 %v, ptr %x``)
   * - ``binop``
     - Binary arithmetic/logic (``add``, ``sub``, ``mul``, ``and``, ``or``, …)
   * - ``compare``
     - Comparison (``icmp``, ``fcmp``)
   * - ``call``
     - Function call
   * - ``ret``
     - Return
   * - ``br``
     - Branch (conditional or unconditional)
   * - ``other``
     - Everything else (``phi``, ``getelementptr``, ``bitcast``, …)

What is SSA form?
-----------------

*Static Single Assignment* (SSA) is a property of the IR where every virtual
register is **assigned exactly once**.  A ``phi`` node merges values from
different predecessor blocks::

   ; Before SSA:   x = 0;  if (cond) { x = 1; }  use(x);
   ; In SSA:
   entry:
     br i1 %cond, label %then, label %merge
   then:
     br label %merge
   merge:
     %x.2 = phi i32 [ 0, %entry ], [ 1, %then ]
     ...

Why does it matter?  SSA makes data-flow explicit, which is why compilers
love it for optimisations.  LLVManim's ``rich-ssa`` rendering mode shows a
live SSA value panel as the animation runs, making it easy to see exactly
which value feeds each computation.

What is a Control-Flow Graph (CFG)?
------------------------------------

A **control-flow graph** represents the possible execution paths through a
function.  Each *node* in the CFG is a basic block; each *edge* is a
possible jump.  Edges that come from conditional branches (``br i1 %c,
label %true, label %false``) are labelled **T** (true) or **F** (false).

LLVManim builds a CFG from every function in an IR file and can animate a
traversal of it — lighting up each block as it is "entered" and each edge as
it is "crossed" — using the ``--cfg-animate`` flag.

Block roles
~~~~~~~~~~~

LLVManim assigns a *role* to each basic block to help the renderer style it:

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Role
     - Assignment rule
   * - ``entry``
     - The first block in the function (in-degree 0)
   * - ``exit``
     - Ends with ``ret`` (out-degree 0)
   * - ``branch``
     - Out-degree ≥ 2 (multiple successors)
   * - ``merge``
     - In-degree ≥ 2 (multiple predecessors)
   * - ``linear``
     - Everything else (single predecessor, single successor)

What is Manim?
--------------

`Manim Community Edition`_ (Manim CE) is a Python animation library designed
for mathematical and technical visualisations.  It produces high-quality
MP4/GIF videos from a Python scene description.

LLVManim uses Manim CE as its rendering backend.  You write (or generate)
a :class:`~llvmanim.render.command_driven_scene.CommandDrivenScene`, populate
it with :class:`~llvmanim.transform.models.AnimationCommand` objects, and
Manim handles the frame generation, compositing, and encoding.

.. _Manim Community Edition: https://docs.manim.community/

Why visualize LLVM IR?
----------------------

* **Teaching** — stepping through IR is the clearest way to explain what a
  compiler actually produces and why.
* **Debugging** — watching a CFG traversal or call-stack animation can reveal
  incorrect optimisations or unexpected code paths instantly.
* **Research** — generated videos are a reproducible artefact that can be
  included in papers and presentations.

LLVManim provides three levels of visualization:

1. **Stack animation** (``--animate``) — shows the call stack growing and
   shrinking as each function call/return happens.
2. **Rich stack animation** (``--ir-mode rich``) — adds an IR source panel
   with a moving cursor that tracks execution.
3. **CFG animation** (``--cfg-animate``) — renders the control-flow graph and
   animates a traversal path through it.
