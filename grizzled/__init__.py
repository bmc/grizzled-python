"""
The Grizzled Utility Library is a general-purpose Python library with
a variety of different modules and packages. It's roughly organized into
subpackages that group different kinds of utility functions and classes.
"""

import grizzled.collections as collections
import grizzled.decorators as decorators
import grizzled.file as file
import grizzled.io as io
import grizzled.log as log
import grizzled.misc as misc
import grizzled.os as os
import grizzled.text as text

__docformat__ = "markdown"

__version__ = "3.3.0"
__author__ = "Brian M. Clapper"
__email__ = "bmc@clapper.org"
__url__ = "https://software.clapper.org/grizzled-python/"
__license__ = "Apache Software License"
__title__ = "The Grizzled Python Utility Library"

# Public stuff

version = __version__
author = __author__
email = __email__
url = __url__
license = __license__
title = __title__

__all__ = (
    "version",
    "author",
    "email",
    "url",
    "license",
    "title",
    "collections",
    "decorators",
    "file",
    "io",
    "log",
    "misc",
    "os",
    "text",
)
