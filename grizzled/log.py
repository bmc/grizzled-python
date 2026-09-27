"""
Provides some classes and functions for use with the standard Python
`logging` module.
"""

__docformat__ = "markdown"

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

import logging
import os
import sys
import textwrap
from typing import Sequence, TextIO

# ---------------------------------------------------------------------------
# Exports
# ---------------------------------------------------------------------------

__all__ = ["WrappingLogFormatter", "init_simple_stream_logging"]

# ---------------------------------------------------------------------------
# Classes
# ---------------------------------------------------------------------------


class WrappingLogFormatter(logging.Formatter):
    """
    A `logging` `Formatter` class that writes each message wrapped on line
    boundaries. Here's a typical usage scenario:

    ```python
    import logging
    import sys
    from grizzled.log import WrappingLogFormatter

    stderr_handler = logging.StreamHandler(sys.stderr)
    formatter = WrappingLogFormatter(format='%(levelname)s %(message)s")
    stderr_handler.setLevel(logging.WARNING)
    stderr_handler.setFormatter(formatter)
    logging.getLogger('').handlers = [stderr_handler]
    ```
    """

    def __init__(
        self,
        format: str | None = None,
        date_format: str | None = None,
        max_width: int | None = None,
    ):
        """
        Initialize a new `WrappingLogFormatter`.

        :param format: The format to use, or `None` for the logging default
        :param date_format: Date format, or `None` for the logging default
        :param max_width: Maximum line width, or `None` to default. The default
            is the value of the environment variable "COLUMNS" (minus 1), or 79
            if the environment variable is not set.
        """
        if max_width is None:
            try:
                max_width = int(os.environ.get("COLUMNS", "80")) - 1
            except ValueError:
                max_width = 79

        self.wrapper = textwrap.TextWrapper(
            width=max_width, subsequent_indent="    "
        )
        logging.Formatter.__init__(self, format, date_format)

    def format(self, record: logging.LogRecord):
        s = logging.Formatter.format(self, record)
        result = []
        for line in s.split("\n"):
            result += [self.wrapper.fill(line)]

        return "\n".join(result)


# ---------------------------------------------------------------------------
# Functions
# ---------------------------------------------------------------------------


def init_simple_stream_logging(
    level: int = logging.INFO,
    streams: Sequence[TextIO] | None = None,
    format: str | None = None,
    date_format: str | None = None,
):
    """
    Useful for simple command-line tools, this method configures the Python
    logging API to:

    - log to one or more open streams (defaulting to standard output) and
    - use a `WrappingLogFormatter`

    :param level: Desired log level
    :param streams: List of files or file-like objects to which to log, or
        `None` to log to standard output.
    :param format: A log format to use, or `None` for the default.
    :param date_format: `strftime` date format to use in log messages, or
        `None` for the default.
    """
    if not streams:
        streams = [sys.stdout]

    if not format:
        format = "%(asctime)s %(message)s"

    if not date_format:
        date_format = "%H:%M:%S"

    logging.basicConfig(level=level)
    handlers = []

    formatter = WrappingLogFormatter(format=format, date_format=date_format)
    for stream in streams:
        log_handler = logging.StreamHandler(stream)
        log_handler.setLevel(level)
        log_handler.setFormatter(formatter)

        handlers += [log_handler]

    logging.getLogger("").handlers = handlers
