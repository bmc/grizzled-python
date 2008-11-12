#!/usr/bin/env python
#
# EasyInstall setup script for The Grizzled Utility Library
#
# $Id$
# ---------------------------------------------------------------------------

import ez_setup
ez_setup.use_setuptools(download_delay=2)
from setuptools import setup, find_packages
import sys
import os
import imp

here = os.path.dirname(os.path.abspath(__file__))
module_file = os.path.join(here, 'grizzled', '__init__.py')
module = imp.load_module('grizzled', open(module_file), module_file,
                         ('__init__.py', 'r', imp.PY_SOURCE))

# Now the setup stuff.

setup (name             = 'grizzled',
       version          = module.version,
       description      = module.title,
       long_description = module.__doc__,
       packages         = find_packages(),
       py_modules       = ['ez_setup'],
       url              = module.url,
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
