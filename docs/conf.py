# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

# -- Project information -----------------------------------------------------
project = 'ak'
author = 'Aharon Haravon'
copyright = '2025, Aharon Haravon'
release = '0.1.5'

# -- General configuration ---------------------------------------------------
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',  # For Google or NumPy style docstrings
    'sphinx.ext.viewcode',  # Optional: add [view code] links to doc pages
    'sphinx.ext.todo',      # Optional: for .. todo:: directives
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# If you use syntax highlighting, you can set a theme (e.g. 'monokai', 'friendly', etc.)
highlight_language = 'python'

# -- Options for HTML output -------------------------------------------------
html_theme = 'alabaster'
html_static_path = ['_static']

# If you want "todo" directives to show up in the docs, set:
# todo_include_todos = True

html_baseurl = "https://aharonh.github.io/ak-tool/"
