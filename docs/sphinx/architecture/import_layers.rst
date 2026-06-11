Import Layer Boundaries
=======================

LLVManim enforces strict layer separation using `import-linter`_.  The rules
are declared in ``.importlinter`` at the project root and checked by
``lint-imports`` (run as part of ``scripts/quality-check.sh``).

.. _import-linter: https://import-linter.readthedocs.io/


The rules
---------

Three contracts are enforced:

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Contract
     - Rule
   * - ``ingest_does_not_depend_on_render``
     - ``llvmanim.ingest`` must not import anything from ``llvmanim.render``
   * - ``transform_does_not_depend_on_render``
     - ``llvmanim.transform`` must not import from ``llvmanim.render``
   * - ``core_does_not_depend_on_cli``
     - ``llvmanim.ingest``, ``llvmanim.transform``, and ``llvmanim.render``
       must not import from ``llvmanim.cli``

These rules are deliberately **one-directional** to allow the diagram below:

Allowed import graph
--------------------

::

   llvmanim.cli
     ├── imports llvmanim.ingest      ✓
     ├── imports llvmanim.transform   ✓
     └── imports llvmanim.render      ✓

   llvmanim.render
     ├── imports llvmanim.transform   ✓
     └── imports llvmanim.ingest      ✓

   llvmanim.transform
     └── imports llvmanim.ingest      ✓  (models only — via transform.models)

   llvmanim.ingest
     └── (no project imports)         ✓

.. note::

   ``llvmanim.transform.models`` is shared upward: both the ingest and
   render layers import from it.  This is intentional — it is the canonical
   data model.  The import-linter contracts permit this because ``models.py``
   lives in ``transform``, and ``ingest`` *does* import from ``transform``
   (for the dataclass definitions).

Why these boundaries?
---------------------

Testability
~~~~~~~~~~~

The ingest and transform layers have **no Manim dependency**.  Their unit
tests run without a display server, a Cairo installation, or ffmpeg.  This
makes the test suite fast and portable.

Build isolation
~~~~~~~~~~~~~~~

The docs and CI lint jobs can build and check the ``ingest`` and ``transform``
layers without installing Manim CE (which has heavy system requirements).
``autodoc_mock_imports`` in ``conf.py`` mocks out ``manim`` and ``manimgl``
for exactly this reason.

Replaceability
~~~~~~~~~~~~~~

Because the render layer is a leaf, it can be swapped for a different
backend (e.g. a web-based SVG renderer) without touching any other layer.

Checking the contracts
-----------------------

.. code-block:: bash

   uv run lint-imports

Or as part of the full quality check:

.. code-block:: bash

   ./scripts/quality-check.sh

A contract violation produces output like::

   BROKEN: Ingest layer must not depend on render layer
   ────────────────────────────────────────────────────
   llvmanim.ingest.llvm_events imports llvmanim.render.json_export
   (via direct import on line 12)
