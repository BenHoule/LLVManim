.. LLVManim documentation master file

LLVManim
========

**LLVManim** is an LLVM IR visualization tool.  It parses LLVM textual IR
(``.ll`` files), derives control-flow graphs and event streams, and produces
animated visualizations using `Manim Community Edition`_.  Whether you want
to step through a call stack, watch a CFG traversal, or just export a
machine-readable scene graph, LLVManim has you covered.

.. _Manim Community Edition: https://docs.manim.community/

.. code-block:: bash

   # Install and run in three commands
   git clone https://github.com/BenHoule/LLVManim && cd LLVManim
   uv sync --group docs --dev
   uv run llvmanim double.ll --json --draw

.. admonition:: New to LLVM IR?

   Start with :doc:`getting_started/concepts` for a plain-English introduction
   to IR, SSA form, and control-flow graphs before diving into the tool.

.. toctree::
   :maxdepth: 2
   :caption: Getting Started

   getting_started/concepts
   getting_started/installation
   getting_started/quickstart

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   user_guide/cli_reference
   user_guide/animation_modes
   user_guide/output_formats
   user_guide/working_with_ir

.. toctree::
   :maxdepth: 2
   :caption: Architecture

   architecture/overview
   architecture/pipeline
   architecture/data_model
   architecture/rendering
   architecture/import_layers

.. toctree::
   :maxdepth: 3
   :caption: API Reference

   api/index

.. toctree::
   :maxdepth: 2
   :caption: Developer Guide

   dev/setup
   dev/testing
   dev/adding_features
   dev/metrics

.. toctree::
   :maxdepth: 1
   :caption: About

   changelog

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
