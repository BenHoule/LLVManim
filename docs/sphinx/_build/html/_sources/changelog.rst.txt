Changelog
=========

All notable changes are tracked here in reverse-chronological order.

0.0.1 (2026-06-10)
-------------------

* Initial release of the unified pipeline.
* Four-layer architecture: ``ingest`` → ``transform`` → ``render`` → ``cli``.
* Three stack animation modes: ``basic``, ``rich``, ``rich-ssa``.
* CFG traversal animation via ``--cfg-animate``.
* JSON, DOT, and PNG export.
* MP4 and GIF output; palette-based GIF workflow via ffmpeg.
* Full pytest suite with ``unit``, ``integration``, ``contract``, and ``e2e`` markers.

Completed milestones
~~~~~~~~~~~~~~~~~~~~

* **Milestone 1** – ``binop`` / ``compare`` event kinds.
* **Milestone 2** – SSA bridge panel.
* **Milestone 3** – Call-stack architecture improvements.
* **Milestone 4** – CFG animation productization.
