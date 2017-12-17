#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# drf-yasg documentation build configuration file, created by
# sphinx-quickstart on Sun Dec 10 15:20:34 2017.
import os
import sys

import sphinx_rtd_theme
from docutils import nodes, utils
from docutils.parsers.rst import roles
from docutils.parsers.rst.roles import set_classes
from pkg_resources import get_distribution

# -- General configuration ------------------------------------------------

# If your documentation needs a minimal Sphinx version, state it here.
#
# needs_sphinx = '1.0'

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = ['sphinx.ext.autodoc', 'sphinx.ext.viewcode']

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# The suffix(es) of source filenames.
# You can specify multiple suffix as a list of string:
#
# source_suffix = ['.rst', '.md']
source_suffix = '.rst'

# The master toctree document.
master_doc = 'index'

# General information about the project.
project = 'drf-yasg'
copyright = '2017, Cristi V.'
author = 'Cristi V.'

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.

# The full version, including alpha/beta/rc tags.
release = get_distribution('drf_yasg').version

# The short X.Y.Z version.
version = '.'.join(release.split('.')[:3])

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
#
# This is also used if you do content translation via gettext catalogs.
# Usually you set "language" from the command line for these cases.
language = None

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This patterns also effect to html_static_path and html_extra_path
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'

modindex_common_prefix = ['drf_yasg.']

# If true, `todo` and `todoList` produce output, else they produce nothing.
todo_include_todos = False

# -- Options for HTML output ----------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
# html_theme = 'default'

html_theme = "sphinx_rtd_theme"
html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
#
# html_theme_options = {}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

# Custom sidebar templates, must be a dictionary that maps document names
# to template names.
#
# This is required for the alabaster theme
# refs: http://alabaster.readthedocs.io/en/latest/installation.html#sidebars
html_sidebars = {
    '**': [
        'relations.html',  # needs 'show_related': True theme option to display
        'searchbox.html',
    ]
}

# -- Options for HTMLHelp output ------------------------------------------

# Output file base name for HTML help builder.
htmlhelp_basename = 'drf-yasgdoc'

# -- Options for LaTeX output ---------------------------------------------

latex_elements = {
    # The paper size ('letterpaper' or 'a4paper').
    #
    # 'papersize': 'letterpaper',

    # The font size ('10pt', '11pt' or '12pt').
    #
    # 'pointsize': '10pt',

    # Additional stuff for the LaTeX preamble.
    #
    # 'preamble': '',

    # Latex figure (float) alignment
    #
    # 'figure_align': 'htbp',
}

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title,
#  author, documentclass [howto, manual, or own class]).
latex_documents = [
    (master_doc, 'drf-yasg.tex', 'drf-yasg Documentation',
     'Cristi V.', 'manual'),
]

# -- Options for manual page output ---------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [
    (master_doc, 'drf-yasg', 'drf-yasg Documentation',
     [author], 1)
]

# -- Options for Texinfo output -------------------------------------------

# Grouping the document tree into Texinfo files. List of tuples
# (source start file, target name, title, author,
#  dir menu entry, description, category)
texinfo_documents = [
    (master_doc, 'drf-yasg', 'drf-yasg Documentation',
     author, 'drf-yasg', 'One line description of project.',
     'Miscellaneous'),
]

autodoc_default_flags = ['private-members']
autodoc_member_order = 'bysource'
autoclass_content = 'both'
autodoc_mock_imports = []

nitpick_ignore = [
    ('py:class', 'object'),
    ('py:class', 'Exception'),
    ('py:class', 'collections.OrderedDict'),

    ('py:class', 'ruamel.yaml.dumper.SafeDumper'),
    ('py:class', 'rest_framework.renderers.BaseRenderer'),
    ('py:class', 'rest_framework.schemas.generators.EndpointEnumerator'),
    ('py:class', 'rest_framework.views.APIView'),

    ('py:class', 'OpenAPICodecYaml'),
    ('py:class', 'OpenAPICodecJson'),
    ('py:class', 'OpenAPISchemaGenerator'),

    ('py:obj', 'bool'),
    ('py:obj', 'dict'),
    ('py:obj', 'list'),
    ('py:obj', 'str'),
    ('py:obj', 'int'),
    ('py:obj', 'bytes'),
    ('py:obj', 'tuple'),
    ('py:obj', 'callable'),
    ('py:obj', 'type'),
    ('py:obj', 'OrderedDict'),

    ('py:obj', 'coreapi.Field'),
    ('py:obj', 'BaseFilterBackend'),
    ('py:obj', 'BasePagination'),
    ('py:obj', 'rest_framework.request.Request'),
    ('py:obj', 'rest_framework.serializers.Field'),
    ('py:obj', 'serializers.Field'),
    ('py:obj', 'serializers.BaseSerializer'),
    ('py:obj', 'Serializer'),
    ('py:obj', 'APIView'),
]

# even though the package should be already installed, the sphinx build on RTD
# for some reason needs the sources dir to be in the path in order for viewcode to work
sys.path.insert(0, os.path.abspath('../src'))

# activate the Django testproj to be able to succesfully import drf_yasg
sys.path.insert(0, os.path.abspath('../testproj'))
os.putenv('DJANGO_SETTINGS_MODULE', 'testproj.settings')

from django.conf import settings  # noqa: E402

settings.configure()

# instantiate a SchemaView in the views module to make it available to autodoc
import drf_yasg.views  # noqa: E402

drf_yasg.views.SchemaView = drf_yasg.views.get_schema_view(None)

# custom interpreted role for linking to GitHub issues and pull requests
# use as :issue:`14` or :pr:`17`
gh_issue_uri = "https://github.com/axnsan12/drf-yasg/issues/%d"
gh_pr_uri = "https://github.com/axnsan12/drf-yasg/pull/%d"


def role_github_pull_request_or_issue(name, rawtext, text, lineno, inliner, options=None, content=None):
    options = options or {}
    content = content or []
    try:
        ghid = int(text)
        if ghid <= 0:
            raise ValueError
    except ValueError:
        msg = inliner.reporter.error(
            'GitHub pull request or issue number must be a number greater than or equal to 1; '
            '"%s" is invalid.' % text, line=lineno
        )
        prb = inliner.problematic(rawtext, rawtext, msg)
        return [prb], [msg]
        # Base URL mainly used by inliner.rfc_reference, so this is correct:

    if name == 'pr':
        ref = gh_pr_uri
    elif name == 'issue':
        ref = gh_issue_uri
    else:
        msg = inliner.reporter.error('unknown tag name for GitHub reference - "%s"' % name, line=lineno)
        prb = inliner.problematic(rawtext, rawtext, msg)
        return [prb], [msg]

    ref = ref % ghid
    set_classes(options)
    node = nodes.reference(rawtext, '#' + utils.unescape(text), refuri=ref, **options)
    return [node], []


roles.register_local_role('pr', role_github_pull_request_or_issue)
roles.register_local_role('issue', role_github_pull_request_or_issue)
