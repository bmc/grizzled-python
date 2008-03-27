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

# Now the setup stuff.

setup (name             = 'grizzled',
       version          = '0.1',
       description      = 'The Grizzled Utility Library',
       packages         = find_packages(),
       url              = 'http://www.clapper.org/software/python/grizzled/',
       license          = 'BSD license',
       author           = 'Brian M. Clapper',
       author_email     = 'bmc@clapper.org',
       #install_requires = ['includer>=1.0.5'],
       test_suite       = 'nose.collector',
)
