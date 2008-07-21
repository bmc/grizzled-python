#!/usr/bin/env python
#
# $Id$
# ---------------------------------------------------------------------------

"""
Provides some classes and functions for use with the standard Python
``logging`` module.
"""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

import logging
import textwrap

# ---------------------------------------------------------------------------
# Exports
# ---------------------------------------------------------------------------

__all__ = ['WrappingLogFormatter']

# ---------------------------------------------------------------------------
# Classes
# ---------------------------------------------------------------------------

class WrappingLogFormatter(logging.Formatter):
    """
    A ``logging`` ``Formatter`` class that writes each message wrapped on line
    boundaries. Here's a typical usage scenario:
    
    .. python::
    
        import logging
        import sys
        from grizzled.log import WrappingLogFormatter

        stderr_handler = logging.StreamHandler(sys.stderr)
        formatter = WrappingLogFormatter(format='%(levelname)s %(message)s")
        stderr_handler.setLevel(logging.WARNING)
        stderr_handler.setFormatter(formatter)
        logging.getLogger('').handlers = [stderr_handler]
    """
    def __init__(self, format=None, date_format=None, max_width=79):
        """
        Initialize a new ``WrappingLogFormatter``.

        :Parameters:
            format : str
                The format to use, or ``None`` for the logging default

            date_format : str
                Date format, or ``None`` for the logging default

            max_width : int
                Maximum line width, or ``None`` to default to 79./
        """
        self.wrapper = textwrap.TextWrapper(width=max_width,
                                            subsequent_indent='    ')
        logging.Formatter.__init__(self, format, date_format)

    def format(self, record):
        s = logging.Formatter.format(self, record)
        result = []
        for line in s.split('\n'):
            result += [self.wrapper.fill(line)]

        return '\n'.join(result)
