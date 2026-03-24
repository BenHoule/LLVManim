"""Transformation layer from IR events to scene plans."""

from llvmanim.transform.scene import (  # noqa: F401
    build_scene_graph,
    build_stack_scene_graph,
)
from llvmanim.transform.trace import (  # noqa: F401
    RichTraceStep,
    TraceStep,
    build_execution_trace,
)
