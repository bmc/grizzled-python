"""
Provides some classes and functions for use with the standard Python
`logging` module.
"""

__docformat__ = "markdown"

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

import logging
import sys
import os
import textwrap
from typing import Optional, TextIO, Sequence

# ---------------------------------------------------------------------------
# Exports
# ---------------------------------------------------------------------------

__all__ = ['WrappingLogFormatter', 'init_simple_stream_logging']

# ---------------------------------------------------------------------------
# Classes
# ---------------------------------------------------------------------------

class WrappingLogFormatter(logging.Formatter):
    """
    A `logging` `Formatter` class that writes each message wrapped on line
    boundaries. Here's a typical usage scenario:

        import logging
        import sys
        from grizzled.log import WrappingLogFormatter

        stderr_handler = logging.StreamHandler(sys.stderr)
        formatter = WrappingLogFormatter(format='%(levelname)s %(message)s")
        stderr_handler.setLevel(logging.WARNING)
        stderr_handler.setFormatter(formatter)
        logging.getLogger('').handlers = [stderr_handler]
    """
    def __init__(self,
                 format: Optional[str] = None,
                 date_format: Optional[str] = None,
                 max_width: Optional[int] = None):
        """
        Initialize a new `WrappingLogFormatter`.

        **Parameters**

        - `format` (`str`): The format to use, or `None` for the logging default
        - `date_format` (`str`): Date format, or `None` for the logging default
        - `max_width` (`int`): Maximum line width, or `None` to default. The
          default is the value of the environment variable "COLUMNS" (minus 1),
          or 79 if the environment variable is not set.
        """
        if max_width is None:
            try:
                max_width = int(os.environ.get('COLUMNS', '80')) - 1
            except ValueError:
                max_width = 79

        self.wrapper = textwrap.TextWrapper(width=max_width,
                                            subsequent_indent='    ')
        logging.Formatter.__init__(self, format, date_format)

    def format(self, record: logging.LogRecord):
        s = logging.Formatter.format(self, record)
        result = []
        for line in s.split('\n'):
            result += [self.wrapper.fill(line)]

        return '\n'.join(result)

# ---------------------------------------------------------------------------
# Functions
# ---------------------------------------------------------------------------

def init_simple_stream_logging(level: int = logging.INFO,
                               streams: Optional[Sequence[TextIO]] = None,
                               format: Optional[str] = None,
                               date_format: Optional[str] = None):
    """
    Useful for simple command-line tools, this method configures the Python
    logging API to:

    - log to one or more open streams (defaulting to standard output) and
    - use a `WrappingLogFormatter`

    **Parameters**

    - `level` (`int`): Desired log level
    - `streams` (`list` of file like objects): List of files or file-like
      objects to which to log, or `None` to log to standard output.
    - `format` (`str`): A log format to use, or none for
      `"%(asctime)s %(message)s"`
    - `date_format` (`str`): `strftime` date format to use in log messages, or
      `None` for `"%H:%M:%S"`
    """
    if not streams:
        streams = [sys.stdout]

    if not format:
        format = '%(asctime)s %(message)s'

    if not date_format:
        date_format = '%H:%M:%S'

    logging.basicConfig(level=level)
    handlers = []

    formatter = WrappingLogFormatter(format=format, date_format=date_format)
    for stream in streams:
        log_handler = logging.StreamHandler(stream)
        log_handler.setLevel(level)
        log_handler.setFormatter(formatter)

        handlers += [log_handler]

    logging.getLogger('').handlers = handlers
