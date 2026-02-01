import os
import sys

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'NEST - Architectures and Service Platforms'
copyright = '2026, Alejandro Botas Bárcena, Javier Grimaldos Chavarría, Estela Mora Barba'
author = 'Alejandro Botas Bárcena, Javier Grimaldos Chavarría, Estela Mora Barba'

version = '1.0'
release = '1.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

sys.path.insert(0, os.path.abspath('../../NEST Device/main'))
sys.path.insert(0, os.path.abspath('../../NEST Device/tests'))
sys.path.insert(0, os.path.abspath('../../NEST Simulations'))
sys.path.insert(0, os.path.abspath('../../ThingsBoard'))
sys.path.insert(0, os.path.abspath('../../Telegram'))

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
    'sphinx_copybutton',
    'sphinx.ext.autosummary',
    'sphinx_simplepdf',
    'sphinxcontrib.mermaid'
]

# Enable automatic member detection
autodoc_default_options = {
    'members': True,          # Auto-document all members
    'member-order': 'bysource', # Follow source order
    'undoc-members': True,    # Show undocumented members
    'show-inheritance': True, # Display inheritance
    'special-members': '__init__', # Document __init__ methods
}

autodoc_mock_imports = [
    'rosidl_runtime_py',
    'rclpy',
    'std_msgs',
    'grpc', 
    'rosidl_generator_py',
    'action_msgs',
    'google',
    'commands_action_interface',
    'concurrent_log_handler',
    'mariadb',
    'paho',
    'connexion',
    'six',
    'flask',
    'GRPC',
    'cv2',
    'numpy',
    'picamera2',
    'pandas',
    'PIL',
    'ultralytics',
    'tqdm'
]

# Enable automatic module discovery
autosummary_generate = True

templates_path = ['_templates']
exclude_patterns = []
suppress_warnings = ['epub.unknown_project_files']


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']