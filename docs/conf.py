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
              "sphinx.ext.mathjax",
              "sphinx.ext.intersphinx",
              "sphinx.ext.todo",
              "sphinx.ext.githubpages",
              "sphinx.ext.autosectionlabel",
              "sphinx.ext.doctest",
              "sphinx.ext.duration",
              "sphinx.ext.viewcode",     # 소스 코드 보기 링크 추가
            #   "sphinxcontrib.bibtex",
            #   "sphinx_tabs.tabs"
              "myst_parser",              
              "autodocsumm",
              ]

intersphinx_mapping = {
    "rtd": ("https://docs.readthedocs.io/en/stable/", None),
    "python": ("https://docs.python.org/3/", None),
    "sphinx": ("https://www.sphinx-doc.org/en/master/", None),
}

# mathjax hacks
mathjax3_config = {
    "tex": {
        "inlineMath": [["\\(", "\\)"]],
        "displayMath": [["\\[", "\\]"]],
    },
}

intersphinx_disabled_domains = ["std"]


templates_path = ['_templates']
suppress_warnings = ["myst.header", "autosectionlabel.*"]
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store', 'README.md']

# -- Options for EPUB output
epub_show_urls = "footnote"

# 언어 설정
language = 'en'

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_theme_path = ["_themes", ]
html_static_path = ['_static']

html_css_files = [
    'css/custom.css',
]

html_js_files = [
    'js/custom.js',
]

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