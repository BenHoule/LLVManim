Data Model
==========

This page documents every dataclass and type alias in LLVManim, with
field-level explanations.  All core models live in
:mod:`llvmanim.transform.models`.


Type aliases
------------

EventKind
~~~~~~~~~

.. code-block:: python

   EventKind = Literal[
       "alloca", "load", "store", "binop", "compare",
       "call", "ret", "br", "other"
   ]

Classifies a single LLVM IR instruction.  See :doc:`pipeline` for the full
opcode → kind mapping table.

BlockRole
~~~~~~~~~

.. code-block:: python

   BlockRole = Literal["entry", "linear", "branch", "merge", "exit"]

Assigned to each basic block based on its in- and out-degrees.  Controls
the animation hint and visual styling.

ActionKind
~~~~~~~~~~

.. code-block:: python

   ActionKind = Literal[
       "create_stack_slot",
       "animate_memory_read",
       "animate_memory_write",
       "animate_binop",
       "animate_compare",
       "push_stack_frame",
       "pop_stack_frame",
       "highlight_branch",
       "signal_stack_underflow",
       "enter_block",
       "exit_block",
       "traverse_edge",
   ]

The action type of an :class:`AnimationCommand`.  The render layer maps each
``ActionKind`` to a Manim animation handler.

Ingest-layer models
-------------------

IREvent
~~~~~~~

Represents one normalised LLVM IR instruction.

.. list-table::
   :header-rows: 1
   :widths: 25 15 60

   * - Field
     - Type
     - Description
   * - ``function_name``
     - ``str``
     - Name of the enclosing function.
   * - ``block_name``
     - ``str``
     - Name of the enclosing basic block (e.g. ``"entry"``, ``"while.cond"``).
   * - ``opcode``
     - ``str``
     - Raw LLVM opcode string (e.g. ``"alloca"``, ``"add"``).
   * - ``text``
     - ``str``
     - Full instruction text as it appears in the IR (display-cleaned).
   * - ``kind``
     - :data:`EventKind`
     - Classified instruction kind.
   * - ``index_in_function``
     - ``int``
     - Zero-based position of this instruction within its enclosing function.
   * - ``debug_line``
     - ``int | None``
     - Source line number from DWARF debug info, or ``None`` if absent.
   * - ``operands``
     - ``list[str]``
     - Operand value names extracted by llvmlite (best-effort).

ProgramEventStream
~~~~~~~~~~~~~~~~~~

The primary output of the ingest layer.

.. list-table::
   :header-rows: 1
   :widths: 25 25 50

   * - Field
     - Type
     - Description
   * - ``source_path``
     - ``str``
     - Absolute or relative path to the ``.ll`` file.
   * - ``events``
     - ``list[IREvent]``
     - All instructions, in order of appearance in the IR.
   * - ``cfg_edges``
     - ``list[CFGEdge]``
     - Control-flow edges extracted from terminator instructions.
   * - ``display_lines``
     - ``dict[str, list[str]]``
     - Map of function name → cleaned IR source lines for the IR panel.

CFGEdge
~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 25 15 60

   * - Field
     - Type
     - Description
   * - ``source``
     - ``str``
     - Internal block ID of the source block (``"function::block"``).
   * - ``target``
     - ``str``
     - Internal block ID of the target block.
   * - ``kind``
     - ``str``
     - Always ``"control_flow"`` for IR-derived edges.
   * - ``label``
     - ``str``
     - ``"T"`` or ``"F"`` for conditional branch edges; empty otherwise.

Transform-layer models
----------------------

CFGBlock
~~~~~~~~

Represents a basic block after grouping and role assignment.

.. list-table::
   :header-rows: 1
   :widths: 25 20 55

   * - Field
     - Type
     - Description
   * - ``id``
     - ``str``
     - Unique identifier: ``"<function_name>::<block_name>"``.
   * - ``name``
     - ``str``
     - Raw block label from the IR.
   * - ``function_name``
     - ``str``
     - Enclosing function name.
   * - ``events``
     - ``list[IREvent]``
     - All instructions in this block, in source order.
   * - ``terminator_opcode``
     - ``str | None``
     - Opcode of the last instruction (``"br"``, ``"ret"``, etc.).
   * - ``role``
     - :data:`BlockRole`
     - Assigned role.
   * - ``indegree``
     - ``int``
     - Number of incoming CFG edges.
   * - ``outdegree``
     - ``int``
     - Number of outgoing CFG edges.
   * - ``memory_ops``
     - ``list[IREvent]``
     - Subset of ``events`` where ``kind in {"alloca", "load", "store"}``.
   * - ``idom``
     - ``str | None``
     - Immediate dominator block ID (from analysis metadata).
   * - ``dom_depth``
     - ``int``
     - Depth in the dominator tree.
   * - ``is_loop_header``
     - ``bool``
     - True if this block is a loop header.
   * - ``loop_depth``
     - ``int``
     - Nesting depth in the loop forest.
   * - ``loop_id``
     - ``str | None``
     - Identifier of the containing loop, if any.
   * - ``is_backedge_target``
     - ``bool``
     - True if any incoming edge is a back-edge.

SceneNode
~~~~~~~~~

A vertex in the :class:`SceneGraph`.

.. list-table::
   :header-rows: 1
   :widths: 25 20 55

   * - Field
     - Type
     - Description
   * - ``id``
     - ``str``
     - Unique identifier (same as ``CFGBlock.id`` for cfg_block nodes).
   * - ``label``
     - ``str``
     - Human-readable display label.
   * - ``kind``
     - ``str``
     - ``"cfg_block"``, ``"stack_frame"``, or ``"stack_slot"``.
   * - ``properties``
     - ``dict[str, Any]``
     - Kind-specific metadata (block_name, function_name, role, events, …).
   * - ``animation_hint``
     - ``str``
     - Hint string used by renderers to choose entry animation style
       (e.g. ``"fade_in_and_focus"``, ``"pulse_loop_header"``).

SceneEdge
~~~~~~~~~

An edge in the :class:`SceneGraph`.

.. list-table::
   :header-rows: 1
   :widths: 25 20 55

   * - Field
     - Type
     - Description
   * - ``source``
     - ``str``
     - Source node ID.
   * - ``target``
     - ``str``
     - Target node ID.
   * - ``label``
     - ``str``
     - ``"T"``, ``"F"``, or empty.
   * - ``kind``
     - ``str``
     - Edge type (``"control_flow"`` or ``"call"``).
   * - ``properties``
     - ``dict[str, Any]``
     - Extra edge metadata.

AnimationCommand
~~~~~~~~~~~~~~~~

A single step in the animation timeline.

.. list-table::
   :header-rows: 1
   :widths: 25 20 55

   * - Field
     - Type
     - Description
   * - ``action``
     - :data:`ActionKind`
     - The type of visual change to perform.
   * - ``target``
     - ``str``
     - ID of the node or edge this command applies to.
       For edge commands, format is ``"source_id::target_id"``.
   * - ``event``
     - ``IREvent | None``
     - The originating IR instruction, when applicable.
   * - ``params``
     - ``dict[str, Any]``
     - Action-specific parameters (e.g. ``{"operands": ["%a", "2"]}``,
       ``{"endpoints": ("src", "dst")}``).

SceneGraph
~~~~~~~~~~

The central data structure passed between the transform and render layers.

.. list-table::
   :header-rows: 1
   :widths: 25 20 55

   * - Field
     - Type
     - Description
   * - ``nodes``
     - ``list[SceneNode]``
     - All graph nodes.
   * - ``edges``
     - ``list[SceneEdge]``
     - All graph edges.
   * - ``commands``
     - ``list[AnimationCommand]``
     - Ordered animation timeline.
   * - ``overlay``
     - ``TraceOverlay | None``
     - Optional runtime trace overlay.

TraceOverlay
~~~~~~~~~~~~

Records the execution path for CFG traversal animations.

.. list-table::
   :header-rows: 1
   :widths: 25 20 55

   * - Field
     - Type
     - Description
   * - ``visited_nodes``
     - ``list[str]``
     - Block IDs visited, in traversal order (may contain repeats for loops).
   * - ``traversed_edges``
     - ``list[tuple[str, str]]``
     - ``(source_id, target_id)`` pairs, in traversal order.
   * - ``entry_order``
     - ``list[str]``
     - Block IDs in entry order (deduplicated first-visit sequence).
   * - ``termination_reason``
     - ``str``
     - Why the trace ended (``"ret"``, ``"loop_limit"``, ``"no_successors"``).

BlockMetadata
~~~~~~~~~~~~~

Optional per-block analysis metadata loaded from ``--import-analysis-metadata``.

.. list-table::
   :header-rows: 1
   :widths: 25 20 55

   * - Field
     - Type
     - Description
   * - ``idom``
     - ``str | None``
     - Immediate dominator block ID.
   * - ``dom_depth``
     - ``int``
     - Depth in the dominator tree (0 = root).
   * - ``is_loop_header``
     - ``bool``
     - True if this block is a loop header.
   * - ``loop_depth``
     - ``int``
     - Nesting depth in the loop forest (0 = not in a loop).
   * - ``loop_id``
     - ``str | None``
     - Identifier of the enclosing natural loop.
   * - ``is_backedge_target``
     - ``bool``
     - True if this block is the target of a back-edge.
