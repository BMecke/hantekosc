import os
import sys

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

# Add source code directory to path (required for autodoc)
project_path = os.path.join('..', '..', '..')
sys.path.insert(0, os.path.abspath(project_path))

extensions = ['sphinx.ext.napoleon', 'sphinx.ext.autodoc']

templates_path = ['_templates']
exclude_patterns = []


# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'hantekosc'
copyright = '2023, Bruno Mecke'
author = 'Bruno Mecke'
release = '0.1.0'

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
