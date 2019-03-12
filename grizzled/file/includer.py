"""
Introduction
============

The `grizzled.file.includer` module contains a class that can be used to
process includes within a text file, returning a file-like object. It also
contains some utility functions that permit using include-enabled files in
other contexts.

Include Syntax
==============

The *include* syntax is defined by a regular expression; any line that matches
the regular expression is treated as an *include* directive. The default
regular expression matches include directives like this::

    %include "/absolute/path/to/file"
    %include "../relative/path/to/file"
    %include "local_reference"

Relative and local file references are relative to the including file. That
That is, if an `Includer` is processing file "/home/bmc/foo.txt" and encounters
an attempt to include file "bar.txt", it will assume "bar.txt" is to be found
in "/home/bmc".

Nested includes are permitted; that is, an included file may, itself, include
other files. The maximum recursion level is configurable and defaults to 100.

The include syntax can be changed by passing a different regular expression to
the `Includer` class constructor.

Usage
=====

This module provides an `Includer` class, which processes include directives
in a file and behaves like a file-like object. See the class documentation for
more details.

The module also provides a `preprocess()` convenience function that can be
used to preprocess a file; it returns the path to the resulting preprocessed
file.

Examples
========

Preprocess a file containing include directives, then read the result:

    import includer
    import sys

    inc = includer.Includer(path)
    for line in inc:
        sys.stdout.write(line)


Use an include-enabled file with the standard Python logging module:

    import logging
    import includer

    logging.fileConfig(includer.preprocess("mylog.cfg"))

"""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

import logging
import os
import sys
import re
import tempfile
import atexit
import codecs

from grizzled.file import unlink_quietly

from typing import (Union, Sequence, AnyStr, TextIO, Optional, Iterable, List,
                    Tuple, Any)


__docformat__ = "markdown"

__all__ = ['Includer', 'IncludeError', 'preprocess', 'MaxNestingExceededError']

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

log = logging.getLogger('includer')

# ---------------------------------------------------------------------------
# Public classes
# ---------------------------------------------------------------------------

class IncludeError(Exception):
    """
    Thrown by `Includer` when an error occurs while processing the file.
    An `IncludeError` object always contains a single string value that
    contains an error message describing the problem.
    """
    def __init__(self, message):
        Exception.__init__(self, message)
        self.message = message


class MaxNestingExceededError(IncludeError):
    """
    Thrown by `Includer` when the maximum include file nesting level is
    exceeded.
    """


class Includer(object):
    """
    An `Includer` object preprocesses a path or file-like object,
    expanding include references. The resulting `Includer` object is a
    file-like object, offering the same methods and capabilities as an open
    file.

    By default, `Includer` supports this include syntax:

        %include "path"
        %include "url"

    However, the include directive syntax is controlled by a regular
    expression, so it can be configured.

    See the module documentation for details.
    """
    def __init__(self,
                 source: Union[TextIO, AnyStr],
                 include_regex: AnyStr = '^%include\s"([^"]+)"',
                 max_nest_level: int = 100,
                 output: Optional[Union[TextIO, AnyStr]] = None,
                 encoding: str = 'utf-8'):
        """
        Create a new `Includer` object.

        **Parameters**

        - `source` (`file` or `str`): The source to be read and expanded. May
          be an open file-like object or a path name.
        - `include_regex` (`str`):  Regular expression defining the include
          syntax. Must contain a single parenthetical group that can be used
          to extract the included file.
        - `max_nest_level` (`int`): Maximum include nesting level. Exceeding
          this level will cause `Includer` to throw an `IncludeError`.
        - `output` (`str` or `file`): A string (path name) or file-like object
          to which to save the expanded output.
        - `encoding` (`str`): The encoding to use to open the files. Defaults
          to "utf-8".

        **Raises**

        `IncludeError` on error
        """

        self._encoding = encoding
        if isinstance(source, str):
            f, name = self._open(source, None)
        else:
            # Assume file-like object.
            f = source
            try:
                name = source.name
            except AttributeError:
                name = None

        self.closed = False
        self.mode = None
        self._include_pattern = re.compile(include_regex)
        self._name = name

        if output == None:
            from io import StringIO
            output = StringIO()

        self._maxnest = max_nest_level
        self._nested = 0
        self._process_includes(f, name, output)
        self._f = output
        self._f.seek(0)

    @property
    def name(self) -> str:
        """
        Get the name of the file being processed.
        """
        return self._name

    def __iter__(self) -> Iterable[str]:
        return self

    def __next__(self) -> str:
        """A file object is its own iterator."""
        line = self.readline()
        if (line == None) or (len(line) == 0):
            raise StopIteration
        return line

    def close(self) -> None:
        """Close the includer, preventing any further I/O operations."""
        if not self.closed:
            self.closed = True
            self._f.close()
            del self._f

    def fileno(self) -> int:
        """
        Get the file descriptor. Returns the descriptor of the file being
        read.
        """
        _complain_if_closed(self.closed)
        return self._f.fileno()

    def isatty(self) -> bool:
        """
        Determine whether the file being processed is a TTY or not.
        """
        _complain_if_closed(self.closed)
        return self._f.isatty()

    def seek(self, pos: int, mode: int = 0) -> None:
        """
        Seek to the specified file offset in the include-processed file.

        **Parameters**

        - `pos` (`int`): file offset
        - `mode` (`int`): the seek mode, as specified to a Python file's
          `seek()` method
        """
        self._f.seek(pos, mode)

    def tell(self) -> int:
        """
        Get the current file offset.

        **Returns**

        the current file offset
        """
        _complain_if_closed(self.closed)
        return self._f.tell()

    def read(self, n: int = -1) -> Sequence[int]:
        """
        Read *n* bytes from the open file.

        **Parameters**

        - `n` (`int`): Number of bytes to read. A negative number instructs
          the method to read all remaining bytes.

        **Returns**

        the bytes read
        """
        _complain_if_closed(self.closed)
        return self._f.read(n)

    def readline(self, length: int = -1) -> str:
        """
        Read the next line from the file.

        **Parameters**

        - `length` (`int`): a length hint, or negative if you don't care

        **Returns**

        the line read
        """
        _complain_if_closed(self.closed)
        return self._f.readline(length)

    def readlines(self, sizehint: int = 0) -> List[str]:
        """
        Read all remaining lines in the file.
        """
        _complain_if_closed(self.closed)
        return self._f.readlines(sizehint)

    def truncate(self, size: Optional[int] = None) -> None:
        """Not supported, since `Includer` objects are read-only."""
        raise IncludeError('Includers are read-only file objects.')

    def write(self, s: str) -> None:
        """Not supported, since `Includer` objects are read-only."""
        raise IncludeError('Includers are read-only file objects.')

    def writelines(self, iterable: Iterable[str]):
        """Not supported, since `Includer` objects are read-only."""
        raise IncludeError('Includers are read-only file objects.')

    def flush(self) -> None:
        """No-op."""
        pass

    def getvalue(self) -> str:
        """
        Retrieve the entire contents of the file, as a string, with includes
        expanded, at any time before the `close()` method is called.
        """
        return ''.join(self.readlines())

    def _process_includes(self,
                          file_in: TextIO,
                          filename: str,
                          file_out: TextIO) -> None:
        log.debug(f'Processing includes in "{filename}"')

        for line in file_in:
            match = self._include_pattern.search(line)
            if match:
                if self._nested >= self._maxnest:
                    raise MaxNestingExceededError(
                        f'Exceeded maximum include depth of {self._maxnest}'
                    )

                inc_name = match.group(1)
                log.debug(f'Found include directive: {line[:-1]}')
                f, included_name = self._open(inc_name, filename)
                self._nested += 1
                self._process_includes(f, filename, file_out)
                self._nested -= 1
            else:
                file_out.write(line)

    def _open(self,
              name_to_open: str,
              enclosing_file: Optional[str]) -> Tuple[TextIO, str]:

        if not os.path.isabs(name_to_open):
            # Not an absolute file. Base it on the parent.
            if enclosing_file == None:
                enclosing_dir = os.getcwd()
            else:
                enclosing_dir = os.path.dirname(enclosing_file)

            name_to_open = os.path.join(enclosing_dir, name_to_open)

        try:
            log.debug(f'Opening "{name_to_open}" with encoding {self._encoding}')
            f = codecs.open(name_to_open, mode='r', encoding=self._encoding)
        except:
            raise IncludeError(
                f'Unable to open "{name_to_open}".'
            )
        return (f, name_to_open)

# ---------------------------------------------------------------------------
# Public functions
# ---------------------------------------------------------------------------

def preprocess(file: Union[TextIO, str],
               encoding: str = 'utf8',
               output: Optional[TextIO] = None,
               temp_suffix: str = '.txt',
               temp_prefix: str = 'inc'):
    """
    Process all include directives in the specified file, returning a path
    to a temporary file that contains the results of the expansion. The
    temporary file is automatically removed when the program exits, though
    the caller is free to remove it whenever it is no longer needed.

    **Parameters**

    - `file` (`file` or `str`): path to file to be expanded, or file-like object
    - `encoding` (`str`): String encoding for input file. Defaults to UTF-8.
    - `output` (`file`): A file or file-like object to receive the output.
    - `temp_suffix` (`str`): suffix to use with temporary file that holds
      preprocessed output
    - `temp_prefix` (`str`): prefix to use with temporary file that holds
      preprocessed output

    **Returns**

    `output`, if `output` is not `None`; otherwise, the path to temporary file
    containing expanded content
    """
    result = None
    path = None
    if not output:
        fd, path = tempfile.mkstemp(suffix=temp_suffix, prefix=temp_prefix)
        output = open(path, 'w')
        atexit.register(unlink_quietly, path)
        os.close(fd)
        result = path
    else:
        result = output

    Includer(file, output=output, encoding=encoding)
    return result


# ---------------------------------------------------------------------------
# Private functions
# ---------------------------------------------------------------------------

def _complain_if_closed(closed: bool) -> None:
    if closed:
        raise IncludeError("I/O operation on closed file")

# ---------------------------------------------------------------------------
# Main program (for testing)
# ---------------------------------------------------------------------------

if __name__ == '__main__':

    format = '%(asctime)s %(name)s %(levelname)s %(message)s'
    logging.basicConfig(level=logging.DEBUG, format=format)

    for file in sys.argv[1:]:
        import io as StringIO
        out = StringIO.StringIO()
        preprocess(file, output=out)

        header = 'File: %s, via preprocess()'
        sep = '-' * len(header)
        print('\n{0}\n{1}\n{2}\n'.format(sep, header, sep))
        for line in out.readlines():
            sys.stdout.write(line)
        print(sep)

        inc = Includer(file)
        header = 'File: %s, via Includer'
        sep = '-' * len(header)
        print('\n{0}\n{1}\n{2}\n'.format(sep, header, sep))
        for line in inc:
            sys.stdout.write(line)
        print(sep)
