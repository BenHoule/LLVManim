Working with LLVM IR
====================

This page explains how to produce ``.ll`` files that work well with
LLVManim, and how to use the optional ``opt`` pass outputs to enrich the
animations.


Compiling C to IR
-----------------

The recommended compilation flags preserve variable names and debug
information, which makes the resulting IR far more readable:

.. code-block:: bash

   clang \
     -g \                            # debug info (line numbers)
     -O0 \                           # no optimisations — keeps the IR literal
     -fno-strict-aliasing \          # avoids some optimizer assumptions
     -fno-inline \                   # prevents function bodies from disappearing
     -fno-discard-value-names \      # preserves %a, %b names instead of %0, %1
     -S -emit-llvm \                 # output LLVM IR text
     my_program.c -o my_program.ll

The helper script in the repository root does exactly this for ``double.c``:

.. code-block:: bash

   ./run.sh   # produces double.ll

Automatic compilation
~~~~~~~~~~~~~~~~~~~~~

The ``--C`` flag tells LLVManim to compile the C source file itself:

.. code-block:: bash

   uv run llvmanim my_program.c --C --animate

Internally this runs ``clang`` with ``-g -O2 -fno-strict-aliasing
-fno-inline -fno-discard-value-names -S -emit-llvm``.

Producing DOT layout files with ``opt``
----------------------------------------

CFG animation requires a ``.dot`` layout file produced by the LLVM
``opt`` pass manager.  The pass is ``dot-cfg``:

.. code-block:: bash

   opt -passes=dot-cfg -disable-output my_file.ll

This writes one ``.dot`` file per function.  For a function named ``main``,
the file is ``.main.dot`` (note the leading dot, because ``opt`` prefixes
the function name with ``.``).

.. code-block:: bash

   # Pass the file explicitly:
   uv run llvmanim my_file.ll --cfg-animate --dot-cfg .main.dot -y

LLVManim infers the function name from the DOT file stem:

* ``.main.dot`` → function ``main``
* ``.double.dot`` → function ``double``

Obtaining dominator-tree and loop metadata
-------------------------------------------

The ``print<postdomtree>`` pass prints post-dominator tree information to
stderr.  LLVManim can ingest this data to enrich scene nodes with fields
like ``idom``, ``dom_depth``, ``is_loop_header``, and ``loop_depth``.

.. code-block:: bash

   # Print post-dominator tree info (goes to stderr)
   opt -passes='print<postdomtree>' -disable-output my_file.ll 2>postdom.txt

Currently the metadata must be converted to LLVManim's JSON format manually
or via a custom script; the ``--import-analysis-metadata`` flag then loads it.
Export the format from an existing scene graph with:

.. code-block:: bash

   uv run llvmanim my_file.ll --export-analysis-metadata meta.json

Round-tripping CFG edges
------------------------

You can export and re-import CFG edges to override the automatically
extracted topology:

.. code-block:: bash

   # Export
   uv run llvmanim my.ll --export-cfg-edges edges.json

   # Edit edges.json to correct any parsing errors ...

   # Re-import
   uv run llvmanim my.ll --import-cfg-edges edges.json --json --draw

This is useful when the IR contains constructs that LLVManim's edge extractor
does not yet handle (e.g. ``indirectbr`` with computed targets).

Runtime trace files
--------------------

A *trace* is a JSON file that encodes the sequence of basic blocks visited
during an actual execution.  You can produce it from an instrumented binary
(e.g. via LLVM coverage) and feed it to ``--cfg-animate`` to replay the
real path rather than a statically derived one.

See :doc:`output_formats` for the trace JSON schema.

Checking tool discovery
------------------------

LLVManim finds external tools (``clang``, ``opt``, ``dot``, ``ffmpeg``) via
:mod:`~llvmanim.util.tools`.  To see which binaries it will use:

.. code-block:: python

   from llvmanim.util import tools
   print(tools.llvm_bin_dir())
   print(tools.clang())
   print(tools.opt())
   print(tools.dot())
   print(tools.ffmpeg())

Or use environment variables to override (see :doc:`cli_reference`).
