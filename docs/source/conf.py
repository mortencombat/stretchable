# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import re
import sys

sys.path.append(os.path.abspath("./_ext"))

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

# The master toctree document.
master_doc = "index"

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
    "sphinx_autodoc_typehints",
    "sphinx.ext.autosectionlabel",
    "autoenum",
]

autodoc_member_order = "groupwise"
autodoc_typehints = "both"

# autoclass_content = "class"

myst_enable_extensions = [
    "colon_fence",
    "smartquotes",
    "replacements",
    "deflist",
]
templates_path = ["_templates"]
exclude_patterns = ["build"]

# The reST default role (used for this markup: `text`) to use for all
# documents.
default_role = "any"

typehints_use_signature = True
typehints_use_signature_return = True
typehints_simplify_optional_unions = False
typehints_defaults = "comma"
napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = True

# If true, '()' will be appended to :func: etc. cross-reference text.
add_function_parentheses = True

# napoleon_type_aliases = {
#     "MeasureFunc": "stretchable.node.MeasureFunc",
# }

todo_include_todos = True

intersphinx_mapping = {"python": ("https://docs.python.org/3", None)}

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "furo"
html_static_path = ["_static"]
html_title = "stretchable"
html_css_files = [
    "https://rsms.me/inter/inter.css",
    "custom.css",
]
html_theme_options = {
    "light_css_variables": {
        "font-stack": "Inter, -apple-system, BlinkMacSystemFont, Segoe UI, Helvetica, Arial, sans-serif, Apple Color Emoji, Segoe UI Emoji",
    },
}
