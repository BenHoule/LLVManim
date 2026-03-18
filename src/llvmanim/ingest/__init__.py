"""Ingestion layer for LLVM IR and metadata."""

from llvmanim.ingest.llvm_events import parse_ir_to_events, parse_module_to_events

__all__ = ["parse_ir_to_events", "parse_module_to_events"]
