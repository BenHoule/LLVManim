llvmanim.util
=============

The util package provides external-tool discovery helpers.


llvmanim.util.tools
--------------------

Finds the command-line tools needed by LLVManim on the user's machine,
while allowing environment-variable overrides.

All public functions are ``@cache``-decorated so each binary is located
at most once per process.

**Discovery order:**

1. Check the relevant environment variable (e.g. ``FFMPEG``, ``DOT``,
   ``CLANG``, ``OPT``).
2. Check ``LLVM_BIN_DIR`` (for LLVM-family tools).
3. On Linux (unless ``NO_LLVM_DEFAULT_SEARCH=1`` is set), search
   ``/usr/lib/llvm*/bin`` sorted by version number descending.
4. Fall back to ``shutil.which`` (``$PATH``).

.. automodule:: llvmanim.util.tools
   :members:
   :undoc-members:

Quick reference
~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 30 30 40

   * - Function
     - Env override
     - Purpose
   * - :func:`~llvmanim.util.tools.llvm_bin_dir`
     - ``LLVM_BIN_DIR``
     - Returns the LLVM binary directory as a ``Path``.
   * - :func:`~llvmanim.util.tools.llvm_tool`
     - ``<TOOLNAME>``
     - Returns the path to a named LLVM binary.
   * - :func:`~llvmanim.util.tools.find_tool`
     - ``<TOOLNAME>``
     - Generic tool lookup (non-LLVM).
   * - :func:`~llvmanim.util.tools.ffmpeg`
     - ``FFMPEG``
     - Returns the ``ffmpeg`` binary path.
   * - :func:`~llvmanim.util.tools.dot`
     - ``DOT``
     - Returns the Graphviz ``dot`` binary path.
   * - :func:`~llvmanim.util.tools.clang`
     - ``CLANG``
     - Returns the ``clang`` binary path.
   * - :func:`~llvmanim.util.tools.opt`
     - ``OPT``
     - Returns the LLVM ``opt`` binary path.
