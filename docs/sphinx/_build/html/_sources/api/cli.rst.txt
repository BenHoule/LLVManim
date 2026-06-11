llvmanim.cli
============

The CLI layer is the top-level orchestrator.  It parses command-line
arguments and dispatches to the ingest, transform, and render layers.


llvmanim.cli (package)
-----------------------

.. automodule:: llvmanim.cli
   :members:
   :undoc-members:

llvmanim.cli.main
-----------------

Contains the ``main()`` function and all private helpers used by the CLI.

.. automodule:: llvmanim.cli.main
   :members:
   :undoc-members:

Entrypoints
-----------

LLVManim can be invoked in three ways:

.. code-block:: bash

   # 1. As an installed command (defined in [project.scripts]):
   llvmanim my.ll --json

   # 2. As a Python module:
   python -m llvmanim my.ll --json

   # 3. As the CLI sub-package:
   python -m llvmanim.cli my.ll --json

All three routes call the same :func:`llvmanim.cli.main.main` function.
