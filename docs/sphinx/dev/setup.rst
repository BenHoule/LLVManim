Developer Setup
================

This page walks through setting up a full development environment from a
fresh clone.


Prerequisites
-------------

See :doc:`../getting_started/installation` for the full system-dependency
list (Python 3.12+, uv, Cairo/Pango, LLVM, Graphviz, ffmpeg).

Clone and install
-----------------

.. code-block:: bash

   git clone https://github.com/BenHoule/LLVManim
   cd LLVManim

   # Install all runtime + development dependencies
   uv sync --dev

   # Optionally add the docs group
   uv sync --dev --group docs

This creates ``.venv/`` with all packages installed in editable mode.
``llvmanim`` is importable immediately without a pip install step.

Running the quality-check script
---------------------------------

.. code-block:: bash

   ./scripts/quality-check.sh

The script runs four checks in order:

1. **Ruff** — fast linter (E, F, I, B, UP, SIM, C90 rule sets).
2. **Pyright** — strict type checking in standard mode.
3. **Import Linter** — enforces layer-boundary contracts (see
   :doc:`../architecture/import_layers`).
4. **pytest** — full test suite with coverage report.

Each step prints ``OK <check> passed`` on success.  The script exits non-zero
on the first failure.

Running individual tools
------------------------

.. code-block:: bash

   # Ruff check only
   uv run ruff check src tests

   # Ruff auto-fix
   uv run ruff check --fix src tests

   # Pyright
   uv run pyright

   # Import linter
   uv run lint-imports

   # Tests (see testing.rst for filtering options)
   uv run pytest

Building the docs
-----------------

.. code-block:: bash

   cd docs/sphinx
   uv run --group docs make html

   # Open locally:
   xdg-open _build/html/index.html

   # Check for broken cross-references:
   uv run --group docs make linkcheck

IDE configuration
-----------------

The ``pyrightconfig.json`` at the project root configures Pyright for VS
Code.  The ``src/`` directory is on the extra-paths list so that
``import llvmanim`` resolves without installation.

.. code-block:: json

   {
     "include": ["src", "tests"],
     "extraPaths": ["src"],
     "pythonVersion": "3.12",
     "typeCheckingMode": "standard"
   }

Project layout recap
---------------------

.. code-block:: text

   src/llvmanim/          ← package source
     cli/                 ← argument parsing & orchestration
     ingest/              ← IR parsing & supplemental I/O
     transform/           ← scene graph construction
     render/              ← Manim scenes & export helpers
     util/                ← external-tool discovery

   tests/                 ← test suite (mirrors src layout)
     conftest.py          ← shared fixtures & marker registration

   docs/
     architecture/        ← DrawIO diagrams & generated pydeps graphs
     sphinx/              ← this Sphinx documentation source

   scripts/               ← quality-check.sh, SVG export helpers
   sandbox/               ← prototype scenes (not part of the package)
   proposal_3-15-26/      ← IEEE proposal LaTeX (not part of the package)
