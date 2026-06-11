API Reference
=============

The LLVManim API is organised into five packages.  The dependency hierarchy is:

.. code-block:: text

   cli  →  render  →  transform  →  ingest
                  ↘              ↗

Package dependency graph
-------------------------

.. graphviz:: ../../architecture/generated/pydeps_internal.dot

.. toctree::
   :maxdepth: 2

   ingest
   transform
   render
   cli
   util
