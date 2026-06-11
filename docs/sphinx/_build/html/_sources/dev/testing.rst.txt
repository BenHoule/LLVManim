Testing
=======

LLVManim uses pytest with a four-tier marker taxonomy.  This page explains
the taxonomy, the shared fixtures, and how to run subsets of the test suite.


Marker taxonomy
---------------

.. list-table::
   :header-rows: 1
   :widths: 20 25 55

   * - Marker
     - Auto-applied to path
     - Meaning
   * - ``unit``
     - ``tests/ingest/``, ``tests/transform/``
     - Fast, deterministic tests with no external dependencies.  No
       Manim, no disk I/O beyond test-data files.
   * - ``integration``
     - ``tests/render/``, ``tests/cli/``, ``tests/test_pipeline.py``
     - Tests that span multiple layers (e.g. ingest + transform, or
       render + transform).
   * - ``contract``
     - ``tests/render/test_exports.py``
     - Tests asserting the external interface contract of JSON / DOT
       export (schema stability).
   * - ``e2e``
     - ``tests/test_entrypoints.py``
     - End-to-end CLI execution tests.

Markers are applied automatically by path in ``conftest.py::pytest_collection_modifyitems``;
you do not need to add ``@pytest.mark.*`` to individual test functions.

Running tests
-------------

.. code-block:: bash

   # All tests
   uv run pytest

   # Only unit tests (fast, no Manim)
   uv run pytest -m unit

   # Only integration tests
   uv run pytest -m integration

   # Only contract tests
   uv run pytest -m contract

   # Only e2e tests
   uv run pytest -m e2e

   # Specific file
   uv run pytest tests/ingest/test_llvm_events.py

   # Specific test by keyword
   uv run pytest -k "test_parse_ir"

   # With coverage report
   uv run pytest --cov=llvmanim --cov-report=term-missing

Coverage threshold
~~~~~~~~~~~~~~~~~~

The project enforces 80 % line coverage.  ``pyproject.toml``:

.. code-block:: toml

   [tool.coverage.report]
   fail_under = 80

Shared fixtures (conftest.py)
------------------------------

All fixtures are defined in ``tests/conftest.py`` and available in every
test file without importing.

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Fixture
     - Description
   * - ``all_kinds_ir``
     - IR string with one instruction of every supported ``EventKind``:
       ``alloca``, ``store``, ``load``, ``binop`` (``add``), ``compare``
       (``icmp``), ``call``, ``br``, ``ret``, plus an ``other`` (``zext``).
   * - ``double_ll_path``
     - ``Path("tests/ingest/testdata/double.ll")`` — the canonical real IR
       test file.
   * - ``double_ll_text``
     - Contents of ``double_ll_path`` as a string.
   * - ``minimal_stream``
     - Pre-parsed ``ProgramEventStream`` from a minimal one-block function
       (``ret i32 0``).
   * - ``branch_stream``
     - Pre-parsed ``ProgramEventStream`` from a two-branch function
       (``entry`` → ``yes`` / ``no``).
   * - ``branch_graph``
     - Pre-built ``SceneGraph`` from ``branch_stream``: 3 nodes, 2 edges.

Test-data files
---------------

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - File
     - Contents
   * - ``tests/ingest/testdata/double.ll``
     - Complete IR for a C function that doubles an integer.  Compiled
       with ``-g -O0 -fno-discard-value-names``.  Used by file-based
       fixture tests.

Test file index
---------------

.. list-table::
   :header-rows: 1
   :widths: 45 55

   * - File
     - What it tests
   * - ``tests/ingest/test_llvm_events.py``
     - ``parse_ir_to_events``, opcode classification, CFG edge extraction
   * - ``tests/ingest/test_display_lines.py``
     - ``build_display_lines``, ``clean_ir_line``
   * - ``tests/ingest/test_cfg_edge_io.py``
     - CFG edge JSON round-trip
   * - ``tests/ingest/test_trace_io.py``
     - Trace JSON round-trip
   * - ``tests/ingest/test_analysis_metadata_io.py``
     - Analysis metadata JSON round-trip
   * - ``tests/ingest/test_dot_layout.py``
     - DOT layout parsing
   * - ``tests/transform/test_scene_graph.py``
     - ``build_scene_graph``, block role assignment
   * - ``tests/transform/test_trace.py``
     - ``derive_cfg_trace``, loop unrolling
   * - ``tests/render/test_command_driven_scene.py``
     - Handler registration, dispatch, speed scaling
   * - ``tests/render/test_stack_renderer.py``
     - Stack animation (push/pop/slot/memory)
   * - ``tests/render/test_cfg_renderer.py``
     - CFG animation (enter/exit/traverse)
   * - ``tests/render/test_cfg_animation_scene.py``
     - ``_CoordMapper``, ``_build_block_mob``, ``_build_edge_mob``
   * - ``tests/render/test_ssa_formatting.py``
     - ``format_display_value``, ``extract_ssa_name``, ``OP_COLORS``
   * - ``tests/render/test_rich_stack_scene_helpers.py``
     - Rich mode IR panel helpers
   * - ``tests/render/test_rich_stack_scene_ssa.py``
     - SSA panel row creation and cleanup
   * - ``tests/render/test_exports.py``
     - JSON and DOT export schema (contract marker)
   * - ``tests/cli/test_main.py``
     - Argument parsing, all CLI flags, dispatch routing
   * - ``tests/cli/test_main_import_fallback.py``
     - Graceful behaviour when ``manim`` is not installed
   * - ``tests/test_pipeline.py``
     - Full ingest → transform pipeline
   * - ``tests/test_entrypoints.py``
     - ``python -m llvmanim`` exits 0 with ``--help``
