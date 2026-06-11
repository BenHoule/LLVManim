Installation
============


System requirements
-------------------

* **Python 3.12 or later** — LLVManim uses modern syntax (match statements,
  ``slots=True`` dataclasses, ``|`` union types).
* **uv** — the fast Python package manager used by this project.  Install it
  from https://docs.astral.sh/uv/getting-started/installation/.
* **Linux** (strongly recommended) — Manim CE and its dependencies are most
  reliable on Linux.  WSL2 on Windows works.  macOS is untested.

LLVM toolchain
~~~~~~~~~~~~~~

LLVManim uses `llvmlite`_ (a Python binding to a bundled LLVM) for IR
parsing.  You do **not** need to install LLVM yourself for the ingest and
transform layers.

However, to *compile C source files* with the ``--C`` flag, or to run
``opt -passes=dot-cfg`` to produce a ``.dot`` file for ``--cfg-animate``,
you do need the LLVM toolchain binaries:

.. code-block:: bash

   # Ubuntu / Debian
   sudo apt install llvm clang

   # Or install a specific version (recommended for reproducibility):
   sudo apt install llvm-18 clang-18

On Linux, LLVManim searches ``/usr/lib/llvm-*/bin`` automatically (latest
installed version first).  Override with:

.. code-block:: bash

   export LLVM_BIN_DIR=/usr/lib/llvm-18/bin
   # or disable the automatic search:
   export NO_LLVM_DEFAULT_SEARCH=1

.. _llvmlite: https://llvmlite.readthedocs.io/

Graphviz
~~~~~~~~

Required for ``--draw`` (DOT→PNG rendering) and for the DOT layout needed by
``--cfg-animate``:

.. code-block:: bash

   sudo apt install graphviz

Override the ``dot`` binary path with:

.. code-block:: bash

   export DOT=/usr/bin/dot

Cairo and Pango
~~~~~~~~~~~~~~~

Manim CE requires Cairo and Pango for text rendering:

.. code-block:: bash

   sudo apt install libcairo2-dev libpango1.0-dev pkg-config

ffmpeg
~~~~~~

Required for video encoding (MP4) and GIF conversion:

.. code-block:: bash

   sudo apt install ffmpeg

Override the binary path:

.. code-block:: bash

   export FFMPEG=/usr/bin/ffmpeg

Clang (optional)
~~~~~~~~~~~~~~~~

Only needed if you use the ``--C`` flag to compile C source files:

.. code-block:: bash

   export CLANG=/usr/bin/clang-18

Installing LLVManim
--------------------

Clone and sync
~~~~~~~~~~~~~~

.. code-block:: bash

   git clone https://github.com/BenHoule/LLVManim
   cd LLVManim
   uv sync --dev

This creates a ``.venv`` and installs all runtime and development
dependencies, including Manim CE, manimgl, llvmlite, graphviz, pytest, ruff,
and pyright.

Install docs dependencies
~~~~~~~~~~~~~~~~~~~~~~~~~

Documentation is an optional dependency group:

.. code-block:: bash

   uv sync --group docs

Build and verify
~~~~~~~~~~~~~~~~

Run the full quality check to make sure everything is working:

.. code-block:: bash

   ./scripts/quality-check.sh

This runs ruff, pyright, pytest with coverage, and fails if coverage drops
below 80 %.

Environment variables reference
---------------------------------

All variables are optional.  When unset, LLVManim uses automatic discovery.

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Variable
     - Effect
   * - ``LLVM_BIN_DIR``
     - Override the LLVM binary directory (containing ``clang``, ``opt``, …)
   * - ``NO_LLVM_DEFAULT_SEARCH``
     - Set to ``1`` to disable the automatic ``/usr/lib/llvm-*/bin`` search on Linux
   * - ``CLANG``
     - Full path to the ``clang`` binary
   * - ``OPT``
     - Full path to the ``opt`` (LLVM pass manager) binary
   * - ``DOT``
     - Full path to the Graphviz ``dot`` binary
   * - ``FFMPEG``
     - Full path to the ``ffmpeg`` binary
