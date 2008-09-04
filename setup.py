#!/usr/bin/env python
#
# EasyInstall setup script for The Grizzled Utility Library
#
# $Id$
# ---------------------------------------------------------------------------

import ez_setup
ez_setup.use_setuptools(download_delay=2)
from setuptools import setup, find_packages
import re
import sys
import os

LONG_DESCRIPTION =\
"""
The *Grizzled Utility Library* is a general-purpose Python library with
a variety of different modules and packages. It's roughly organized into
subpackages that group different kinds of utility functions and classes.

See the `API documentation`_ for complete details.

.. _API documentation: http://www.clapper.org/software/python/grizzled/epydoc
"""

# Now the setup stuff.

setup (name             = 'grizzled',
       version          = '0.8.2',
       description      = 'The Grizzled Utility Library',
       long_description = LONG_DESCRIPTION,
       packages         = find_packages(),
       py_modules       = ['ez_setup'],
       url              = 'http://www.clapper.org/software/python/grizzled/',
       license          = 'BSD license',
       author           = 'Brian M. Clapper',
       author_email     = 'bmc@clapper.org',
       #install_requires = ['includer>=1.0.5'],
       test_suite       = 'nose.collector',
       classifiers = [
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules'
        ]
)
