# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import re

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "stretchable"
author = "Kenneth Trelborg Vestergaard"
copyright = f"2023, {author}"

# The full version, including alpha/beta/rc tags.
release = re.sub("^v", "", os.popen("git describe --tags --abbrev=0").read().strip())
if "dev" in release:
    release = version = "UNRELEASED"
elif "-" in release:
    version = release
else:
    # The short X.Y version.
    version = release.rsplit(".", 1)[0]

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.doctest",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
    "sphinx.ext.todo",
    "sphinx_copybutton",
]

myst_enable_extensions = [
    "colon_fence",
    "smartquotes",
    "deflist",
]
templates_path = ["_templates"]
exclude_patterns = ["_build"]

# If true, '()' will be appended to :func: etc. cross-reference text.
add_function_parentheses = True

intersphinx_mapping = {"python": ("https://docs.python.org/3", None)}

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "furo"
html_static_path = ["_static"]
html_css_files = [
    "https://rsms.me/inter/inter.css",
]
html_theme_options = {
    "light_css_variables": {
        "font-stack": "Inter, -apple-system, BlinkMacSystemFont, Segoe UI, Helvetica, Arial, sans-serif, Apple Color Emoji, Segoe UI Emoji",
    },
}
