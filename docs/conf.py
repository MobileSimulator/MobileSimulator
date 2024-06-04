# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'MobileSimulator'
copyright = '2024, Ji Sue Lee, Dong Beom Kim'
author = 'Ji Sue Lee, Dong Beom Kim'
release = '1.0.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ["sphinx_rtd_theme",
              "sphinx.ext.autodoc",      # 자동화된 문서화 기능
              "sphinx.ext.napoleon",     # Google 스타일 docstring 지원
              "sphinx.ext.viewcode",     # 소스 코드 보기 링크 추가
              # "sphinxcontrib.youtube",
              "sphinx_tabs.tabs"
              ]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# 언어 설정
language = 'en'

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_theme_path = ["_themes", ]
html_static_path = ['_static']

html_logo = "_static/robot.png"
html_theme_options = {
    'logo_only': True,
    'display_version': False,
    'style_nav_header_background': '#FFD700'
}
html_show_copyright = True
html_show_sphinx = False

# The master toctree document.
master_doc = "index"