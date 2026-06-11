llvmanim.ingest
===============

The ingest layer is responsible for reading LLVM IR from disk and converting
it into LLVManim's typed data structures.  It also provides I/O helpers for
supplemental files (CFG edges, traces, analysis metadata) and parses
Graphviz DOT layout files.

**Public API:**

.. code-block:: python

   from llvmanim.ingest import parse_ir_to_events, parse_module_to_events


llvmanim.ingest (package)
--------------------------

.. automodule:: llvmanim.ingest
   :members:
   :undoc-members:

llvmanim.ingest.llvm_events
----------------------------

Core IR parsing.  Uses ``llvmlite.binding`` to parse LLVM IR text into a
:class:`~llvmanim.transform.models.ProgramEventStream`.

.. automodule:: llvmanim.ingest.llvm_events
   :members:
   :undoc-members:
   :private-members: _kind_from_opcode

llvmanim.ingest.display_lines
-------------------------------

Builds display-ready IR source lines for the IR panel in rich and rich-ssa
modes.

.. automodule:: llvmanim.ingest.display_lines
   :members:
   :undoc-members:

llvmanim.ingest.cfg_edge_io
----------------------------

Import / export of CFG edge lists as JSON.

.. automodule:: llvmanim.ingest.cfg_edge_io
   :members:
   :undoc-members:

llvmanim.ingest.trace_io
-------------------------

Import / export of runtime trace overlays as JSON.

.. automodule:: llvmanim.ingest.trace_io
   :members:
   :undoc-members:

llvmanim.ingest.analysis_metadata_io
--------------------------------------

Import / export of per-block analysis metadata (dominator tree, loop
structure) as JSON.

.. automodule:: llvmanim.ingest.analysis_metadata_io
   :members:
   :undoc-members:

llvmanim.ingest.dot_layout
---------------------------

Parses a Graphviz DOT file (produced by ``opt -passes=dot-cfg``) and
returns a :class:`~llvmanim.ingest.dot_layout.DotLayout` with node
positions, dimensions, and edge spline control points.

.. automodule:: llvmanim.ingest.dot_layout
   :members:
   :undoc-members:
