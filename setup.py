#!/usr/bin/env python

from __future__ import with_statement
from setuptools import setup, find_packages
import os
import imp
from distutils.cmd import Command

here = os.path.dirname(os.path.abspath(__file__))
module_file = os.path.join(here, 'grizzled', '__init__.py')
module = imp.load_module('grizzled', open(module_file), module_file,
                         ('__init__.py', 'r', imp.PY_SOURCE))

NAME = 'grizzled-python'

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
        module_file = os.path.join(here, 'grizzled', 'file', '__init__.py')
        gf = imp.load_module('grizzled.file', open(module_file),
                             module_file, ('__init__.py', 'r', imp.PY_SOURCE))

        # Docs

        gh_pages = os.path.join('..', 'gh-pages')
        doc_dir = os.path.join(gh_pages, 'epydoc')
        print('Removing %s' % doc_dir)
        gf.recursively_remove(doc_dir)
        print('Copying epydoc to %s...' % gh_pages)
        gf.copy_recursively('epydoc', doc_dir)

        # Changelog

        changelog = 'CHANGELOG.md'
        print('Copying %s to %s' % (changelog, gh_pages))
        with open(changelog) as f:
            lines = ''.join(f.readlines())

        header = ['---',
                  'title: Change log for %s' % NAME,
                  'layout: default',
                  '---']
        with open(os.path.join(gh_pages, changelog), 'w') as f:
            f.write('\n'.join(header))
            f.write('\n\n')
            f.write(lines)

# Now the setup stuff.

setup (name             = NAME,
       version          = module.version,
       description      = module.title,
       long_description = module.__doc__,
       install_requires = ['backports.tempfile >= 1.0rc1',
                          ],
       packages         = find_packages(),
       url              = module.url,
       license          = module.license,
       author           = module.author,
       author_email     = module.email,
       test_suite       = 'nose.collector',
       cmdclass         = {'gh' : GH },
       classifiers = [
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules'
        ]
)
