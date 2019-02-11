#!/usr/bin/env python

from __future__ import with_statement
from setuptools import setup, find_packages
import os
import sys
from distutils.cmd import Command
from textwrap import TextWrapper
import re

columns = int(os.environ.get('COLUMNS', '80')) - 1
wrap = TextWrapper(width=columns)

if sys.version_info[0] < 3:
    msg = ('As of version 1.2.0, grizzled-python is no longer supported on ' +
           'Python 2. Either upgrade to Python 3, or use an older version ' +
           'of grizzled-python.')
    sys.stderr.write(wrap.fill(msg) + '\n')
    raise Exception(msg)

here = os.path.dirname(os.path.abspath(__file__))
module_file = os.path.join(here, 'grizzled', '__init__.py')

def import_from_file(file, name):
    # See https://stackoverflow.com/a/19011259/53495
    import importlib.machinery
    import importlib.util
    loader = importlib.machinery.SourceFileLoader(name, file)
    spec = importlib.util.spec_from_loader(loader.name, loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod

module = import_from_file(os.path.join('grizzled', '__init__.py'), 'grizzled')

NAME = 'grizzled-python'
API_DOCS_BUILD = 'apidocs'
GRIZZLED_FILE = os.path.join(here, 'grizzled', 'file', '__init__.py')

# Custom commands

class GH(Command):
    description = 'copy stuff to ../gh-pages'

    user_options = []

    def __init__(self, dist):
        Command.__init__(self, dist)

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):

        gh_pages = os.path.join('..', 'gh-pages')

        # Docs

        API_DOCS_SRC = os.path.join(API_DOCS_BUILD, 'grizzled')
        API_DOCS_TARGET = os.path.join(gh_pages, 'apidocs')
        gf = import_from_file(GRIZZLED_FILE, 'gf')

        print('Removing {}'.format(API_DOCS_TARGET))
        gf.recursively_remove(API_DOCS_TARGET)
        print('Copying {} to {}...'.format(API_DOCS_SRC, gh_pages))
        gf.copy_recursively(API_DOCS_SRC, API_DOCS_TARGET)

class Doc(Command):
    description = 'create the API docs'

    user_options = []

    def __init__(self, dist):
        Command.__init__(self, dist)

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        gf = import_from_file(GRIZZLED_FILE, 'gf')
        if os.path.exists(API_DOCS_BUILD):
            gf.recursively_remove(API_DOCS_BUILD)

        cmd = 'pdoc --html --html-dir {} grizzled'.format(API_DOCS_BUILD)
        print('+ {}'.format(cmd))
        rc = os.system(cmd)
        if rc != 0:
            raise Exception("Failed to run pdoc. rc={}".format(rc))

# Now the setup stuff.

setup (name             = NAME,
       version          = module.version,
       description      = module.title,
       long_description = module.__doc__,
       install_requires = [
           'backports.tempfile >= 1.0rc1',
        ],
       packages         = find_packages(),
       url              = module.url,
       license          = module.license,
       author           = module.author,
       author_email     = module.email,
       test_suite       = 'nose.collector',
       cmdclass         = {
           'gh':   GH,
           'docs': Doc
       },
       classifiers = [
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules'
      ]
)
