#!/usr/bin/env python
#
# EasyInstall setup script for The Grizzled Utility Library
#
# $Id$
# ---------------------------------------------------------------------------

from setuptools import setup, find_packages
import sys
import os
import imp

here = os.path.dirname(os.path.abspath(__file__))
module_file = os.path.join(here, 'grizzled', '__init__.py')
module = imp.load_module('grizzled', open(module_file), module_file,
                         ('__init__.py', 'r', imp.PY_SOURCE))

NAME = 'grizzled-python'
DOWNLOAD_URL = ('http://pypi.python.org/packages/source/g/%s/%s-%s.tar.gz' %
                (NAME, NAME, module.version))

# Now the setup stuff.

setup (name             = NAME,
       version          = module.version,
       description      = module.title,
       long_description = module.__doc__,
       packages         = find_packages(),
       url              = module.url,
       download_url     = DOWNLOAD_URL,
       license          = module.version,
       author           = module.author,
       author_email     = module.email,
       test_suite       = 'nose.collector',
       classifiers = [
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules'
        ]
)
