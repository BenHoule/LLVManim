llvmanim.transform
==================

The transform layer converts a flat
:class:`~llvmanim.transform.models.ProgramEventStream` from the ingest layer
into a structured :class:`~llvmanim.transform.models.SceneGraph` with an
ordered animation timeline.


llvmanim.transform (package)
-----------------------------

.. automodule:: llvmanim.transform
   :members:
   :undoc-members:

llvmanim.transform.models
--------------------------

All core data models.  Both the ingest and render layers import from here.

.. automodule:: llvmanim.transform.models
   :members:
   :undoc-members:
   :special-members: __init__

llvmanim.transform.scene
-------------------------

Scene graph construction: groups IR events into blocks, assigns roles,
builds edges, and generates the animation command timeline.

.. automodule:: llvmanim.transform.scene
   :members:
   :undoc-members:

llvmanim.transform.trace
-------------------------

Static CFG-trace derivation: walks the graph from the entry block, always
taking the true branch, and returns a
:class:`~llvmanim.transform.models.TraceOverlay`.

.. automodule:: llvmanim.transform.trace
   :members:
   :undoc-members:
