Metrics and Charts
==================

The ``docs/metrics/`` directory contains two Python scripts that generate
static charts from hardcoded data.  Run them from the project root:

.. code-block:: bash

   uv run python docs/metrics/generate_metrics.py
   uv run python docs/metrics/generate_perf_metrics.py

The scripts require ``matplotlib`` (not in the main dependency groups; install
with ``uv pip install matplotlib`` or add to a ``metrics`` group).


generate_metrics.py
-------------------

Produces static analysis charts saved to ``docs/metrics/*.png``:

* **Coverage by module** — horizontal bar chart showing statement coverage %
  per module, colour-coded by layer (cli / ingest / transform / render).
* **Test count by category** — bar chart of test counts by marker
  (unit / integration / contract / e2e).
* **Lines of code by layer** — pie or bar chart showing source LOC
  distribution.
* **Coverage vs. file size** — scatter plot correlating module size (SLOC)
  with coverage %, surfacing under-tested large files.

The data in the script is manually updated after each test run.  Automate
it by piping ``pytest --cov=llvmanim --cov-report=json`` output into a
coverage-data script.

generate_perf_metrics.py
------------------------

Produces performance-scaling charts:

* **Parse time vs. IR size** — wall-clock time for ``parse_module_to_events``
  on IR files of increasing size.
* **Scene graph build time** — wall-clock time for ``build_scene_graph`` as
  a function of block count.
* **Trace derivation time** — wall-clock time for ``derive_cfg_trace`` as a
  function of node/edge count.
* **Memory usage** — peak RSS during a full CLI invocation.

Regenerating metrics
---------------------

After adding new modules or significantly changing coverage:

1. Run the full test suite with JSON coverage:

   .. code-block:: bash

      uv run pytest --cov=llvmanim --cov-report=json

2. Update the ``COVERAGE_DATA`` table in ``generate_metrics.py`` from
   ``coverage.json``.

3. Regenerate:

   .. code-block:: bash

      uv run python docs/metrics/generate_metrics.py

4. Commit the updated ``.png`` files.
