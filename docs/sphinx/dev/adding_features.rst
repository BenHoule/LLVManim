Adding New Features
===================

This page explains how to extend LLVManim by adding a new
:data:`~llvmanim.transform.models.EventKind`, a new
:class:`~llvmanim.transform.models.AnimationCommand` action, or a new CLI
flag.  Each section identifies exactly which files to touch and in what order.


Adding a new EventKind
-----------------------

*Example: add a ``phi`` kind for phi-node instructions.*

1. **models.py** — extend the ``EventKind`` type alias:

   .. code-block:: python

      EventKind = Literal[
          "alloca", "load", "store", "binop", "compare",
          "call", "ret", "br", "other",
          "phi",   # ← new
      ]

2. **llvm_events.py** — teach ``_kind_from_opcode`` to classify the opcode:

   .. code-block:: python

      _PHI_OPCODES: frozenset[str] = frozenset({"phi"})

      def _kind_from_opcode(opcode: str | None) -> EventKind:
          ...
          if opcode in _PHI_OPCODES:
              return "phi"
          ...

3. **tests/ingest/test_llvm_events.py** — add a test asserting that a
   ``phi`` instruction is classified as ``"phi"``.

4. **(Optional) transform/scene.py** — if the new kind needs special scene
   treatment, update ``_build_overlay_commands`` or the stack command builder.

5. **(Optional) render/stack_renderer.py** — if the new kind needs a visual
   handler, register one in ``_register_stack_handlers``.

Adding a new ActionKind
------------------------

*Example: add a ``highlight_phi`` action.*

1. **models.py** — add the new literal to ``ActionKind``:

   .. code-block:: python

      ActionKind = Literal[
          ...,
          "highlight_phi",   # ← new
      ]

2. **transform/scene.py** — emit ``AnimationCommand(action="highlight_phi",
   ...)`` when building commands.

3. **render/stack_renderer.py** or **render/cfg_renderer.py** — register a
   handler:

   .. code-block:: python

      self._register_handler("highlight_phi", self._handle_highlight_phi)

      def _handle_highlight_phi(self, cmd: AnimationCommand) -> None:
          # ... Manim animations here ...

4. **tests/render/test_stack_renderer.py** — add a test for the new handler.

Adding a new CLI flag
----------------------

1. **cli/main.py** — add the ``parser.add_argument`` call in ``main()``:

   .. code-block:: python

      parser.add_argument(
          "--my-flag",
          action="store_true",
          help="Short description of the flag.",
      )

2. **cli/main.py** — use ``args.my_flag`` in the dispatch logic.

3. **tests/cli/test_main.py** — add tests for the new flag (both that it
   parses correctly and that it produces the expected side-effect).

4. **docs/sphinx/user_guide/cli_reference.rst** — document the new flag
   with an ``.. option::`` directive.

Adding a new export format
---------------------------

*Example: add a ``--mermaid`` flag that exports a Mermaid diagram.*

1. Create ``src/llvmanim/render/mermaid_export.py`` with the export function.
2. Export it from ``src/llvmanim/render/__init__.py``.
3. Add a ``--mermaid`` flag to ``cli/main.py`` and call the new function.
4. Add a ``tests/render/test_mermaid_export.py`` contract test.
5. Document the new output format in
   ``docs/sphinx/user_guide/output_formats.rst``.

Updating the documentation
----------------------------

After any change, rebuild the docs to verify no Sphinx warnings:

.. code-block:: bash

   cd docs/sphinx && uv run --group docs make html

Run ``make linkcheck`` to catch broken cross-references.
