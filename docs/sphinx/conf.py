"""Sphinx configuration for LLVManim documentation."""

from __future__ import annotations

import sys
from pathlib import Path

# -- Path setup ---------------------------------------------------------------
# Add the project src/ directory so that autodoc can import the package
# without it being installed.  Heavy rendering dependencies (manim, manimgl,
# llvmlite) are mocked out below so the build never needs them installed.
sys.path.insert(0, str(Path(__file__).parents[2] / "src"))

# -- Project information -------------------------------------------------------
project = "LLVManim"
copyright = "2026, Ben Houle"
author = "Ben Houle"
release = "0.0.1"

# -- General configuration ----------------------------------------------------
extensions = [
    "sphinx.ext.autodoc",          # API docs from docstrings
    "sphinx.ext.napoleon",         # Google-style / NumPy-style docstrings
    "sphinx.ext.viewcode",         # [source] links on every autodoc page
    "sphinx.ext.intersphinx",      # Cross-links to Python / Manim docs
    "sphinx.ext.graphviz",         # Render .dot graphs inline
    "myst_parser",                 # Parse included Markdown files
    "sphinx_autodoc_typehints",    # Render PEP 484 annotations in sig + body
    "sphinx_copybutton",           # Copy button on every code block
    "sphinxcontrib.mermaid",       # Mermaid diagram support
]

# -- autodoc ------------------------------------------------------------------
autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "show-inheritance": True,
    "member-order": "bysource",
}
# Heavy rendering stack; never needed for building docs
autodoc_mock_imports = ["manim", "manimgl", "llvmlite"]

# -- napoleon -----------------------------------------------------------------
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_use_param = True
napoleon_use_returns = True

# -- sphinx-autodoc-typehints -------------------------------------------------
always_document_param_types = True
typehints_fully_qualified = False
simplify_optional_unions = True

# -- intersphinx --------------------------------------------------------------
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "manim": ("https://docs.manim.community/en/stable", None),
}

# -- MyST parser (Markdown support) -------------------------------------------
myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "fieldlist",
    "tasklist",
]

# -- autosectionlabel ---------------------------------------------------------
autosectionlabel_prefix_document = True  # avoids duplicate label warnings

# -- HTML output --------------------------------------------------------------
html_theme = "furo"
html_title = "LLVManim"
html_static_path = ["_static"]
html_css_files = ["custom.css"]
html_theme_options = {
    "sidebar_hide_name": False,
    "navigation_with_keys": True,
    "source_repository": "https://github.com/BenHoule/LLVManim",
    "source_branch": "main",
    "source_directory": "docs/sphinx/",
    "light_logo": "logo.svg",
    "dark_logo": "logo.svg",
}

# -- Templates & miscellaneous -----------------------------------------------
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
templates_path = ["_templates"]
default_role = "any"

# Suppress noisy warnings from third-party modules and placeholder JSON examples
suppress_warnings = [
    "sphinx_autodoc_typehints.guarded_import",
    "misc.highlighting_failure",
    "docutils",
]

# -- Graphviz output ----------------------------------------------------------
graphviz_output_format = "svg"
