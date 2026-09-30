"""
# Introduction

The `grizzled.file.includer` module contains a class that can be used to
process includes within a text file, returning a file-like object. It also
contains some utility functions that permit using include-enabled files in
other contexts.

# Include Syntax

The *include* syntax is defined by a regular expression; any line that matches
the regular expression is treated as an *include* directive. The default
regular expression matches include directives like this::

```
%include "/absolute/path/to/file"
%include "../relative/path/to/file"
%include "local_reference"
```

Relative and local file references are relative to the including file. That
is, if an `Includer` is processing file "/home/bmc/foo.txt" and encounters
an attempt to include file "bar.txt", it will assume "bar.txt" is to be found
in "/home/bmc".

Nested includes are permitted; that is, an included file may, itself, include
other files. The maximum recursion level is configurable and defaults to 100.

The include syntax can be changed by passing a different regular expression to
the `Includer` class constructor.

# Usage

This module provides an `Includer` class, which processes include directives
in a file and behaves like a file-like object. See the class documentation for
more details.

The module also provides a `preprocess()` convenience function that expands
an open file into a caller-supplied output object.

An `Includer` reads from an open file-like object, and `preprocess()` reads
from an open file-like object and writes the expanded output to a second
file-like object. Neither one opens or closes the caller's objects on the
caller's behalf; the included files, however, are opened and closed by
`Includer`.

# Examples

Expand a file containing include directives, then read the result:

```python
import sys

from grizzled.file import includer

with open(path, encoding='utf-8') as f:
    inc = includer.Includer(f)
    for line in inc:
        sys.stdout.write(line)
```


Use an include-enabled file with the standard Python `logging` module:

```python
from io import StringIO
import logging.config

from grizzled.file import includer

expanded = StringIO()
with open("mylog.cfg", encoding='utf-8') as f:
    includer.preprocess(f, expanded)

expanded.seek(0)
logging.config.fileConfig(expanded)
```

"""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

import logging
import os
import re
from io import TextIOBase, UnsupportedOperation
from string import Template
from typing import BinaryIO, Iterable, Iterator, Self, TextIO

__docformat__ = "markdown"

__all__ = ["Includer", "IncludeError", "preprocess", "MaxNestingExceededError"]

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

log = logging.getLogger("includer")

# ---------------------------------------------------------------------------
# Public classes
# ---------------------------------------------------------------------------


class IncludeError(Exception):
    """
    Thrown by `Includer` when an error occurs while processing the file.
    An `IncludeError` object always contains a single string value that
    contains an error message describing the problem.
    """

    def __init__(self: Self, message: str):
        super().__init__(message)
        self.message = message


class MaxNestingExceededError(IncludeError):
    """
    Thrown by `Includer` when the maximum include file nesting level is
    exceeded.
    """


class Includer(TextIOBase):
    """
    An `Includer` object reads an open file-like object, expanding include
    references into a second file-like object. The resulting `Includer`
    object is, itself, a read-only file-like object, offering the same
    methods and capabilities as a file opened for reading.

    By default, `Includer` supports this include syntax:

    ```
    %include "path"
    ```

    However, the include directive syntax is controlled by a regular
    expression, so it can be configured.

    See the module documentation for details.
    """

    def __init__(
        self: Self,
        source: TextIO,
        include_regex: str = r'^%include\s"([^"]+)"',
        max_nest_level: int = 100,
        encoding: str = "utf-8",
        before_include: str | None = None,
        after_include: str | None = None,
    ):
        """
        Create a new `Includer` object.

        :param source: The source to be read and expanded. Must be an open
            file-like object (`StringIO` is permitted).
        :param include_regex: Regular expression defining the include syntax.
            Must contain a single parenthetical group that can be used to
            extract the included file.
        :param max_nest_level: Maximum include nesting level. Exceeding this
            level will cause `Includer` to throw an `IncludeError`.
        :param encoding: The encoding to use when opening included files.
            Defaults to "utf-8".
        :param before_include: Text to insert before each included file, if
            any. If the text includes the string $FILE or ${FILE}, it will be
            replaced with the name of the included file.
        :param after_include: Text to insert after each included file, if any.
            If the text includes the string $FILE or ${FILE}, it will be
            replaced with the name of the included file.
        :raises IncludeError: If an error occurs while processing includes.
        """
        super().__init__()

        self._encoding = encoding
        self._include_pattern = re.compile(include_regex)
        self._max_nest_level = max_nest_level
        self._before_include = before_include
        self._after_include = after_include
        self._name = getattr(source, "name", None)

        buf: list[str] = []
        self._process_includes(source, self._name, buf, 1)
        self._text = "".join(buf)
        self._pos = 0

    # -----------------------------------------------------------------
    # Properties
    # -----------------------------------------------------------------

    @property
    def name(self: Self) -> str | None:
        """
        The name of the source being processed, or `None` if the source
        has no name (e.g., it's a `StringIO` object).
        """
        return self._name

    # typeshed declares _TextIOBase.encoding as a mutable "str" field,
    # but at runtime it's a read-only descriptor (it returns None), so a
    # property is the only way to override it. Hence the suppression.
    @property
    def encoding(self: Self) -> str:  # pyright: ignore
        """
        The encoding used when opening included files.
        """
        return self._encoding

    # -----------------------------------------------------------------
    # Capabilities
    # -----------------------------------------------------------------

    def readable(self: Self) -> bool:
        """An `Includer` is always readable."""
        return True

    def seekable(self: Self) -> bool:
        """An `Includer` is always seekable."""
        return True

    def writable(self: Self) -> bool:
        """An `Includer` is never writable."""
        return False

    # -----------------------------------------------------------------
    # Reading
    # -----------------------------------------------------------------

    def read(self: Self, size: int | None = -1) -> str:
        """
        Read characters from the expanded content.

        :param size: Number of characters to read. A negative number or `None`
            reads all remaining characters.
        :return: The characters read, as a string. An empty string signals end
            of file.
        :raises ValueError: If the `Includer` is closed.
        """
        self._check_open()
        if (size is None) or (size < 0):
            end = len(self._text)
        else:
            end = min(self._pos + size, len(self._text))

        result = self._text[self._pos : end]
        self._pos = end
        return result

    def readline(self: Self, size: int | None = -1) -> str:
        """
        Read the next line from the expanded content.

        :param size: Maximum number of characters to read, or a negative number
            (or `None`) for no limit
        :return: The line read, including its trailing newline, if any. An
            empty string signals end of file.
        :raises ValueError: If the `Includer` is closed.
        """
        self._check_open()
        i = self._text.find("\n", self._pos)
        end = len(self._text) if i < 0 else i + 1
        if (size is not None) and (size >= 0):
            end = min(end, self._pos + size)

        line = self._text[self._pos : end]
        self._pos = end
        return line

    def readlines(self: Self, hint: int = -1) -> list[str]:
        """
        Read all remaining lines from the expanded content.

        :param hint: Stop once this many characters have been read, without
            truncating the last line. A negative number (or `None`) means "read
            everything".
        :return: A list of the lines read.
        :raises ValueError: If the `Includer` is closed.
        """
        self._check_open()
        lines: list[str] = []
        total = 0
        while True:
            line = self.readline()
            if len(line) == 0:
                break

            lines.append(line)
            total += len(line)
            if (hint is not None) and (hint >= 0) and (total >= hint):
                break

        return lines

    def __iter__(self) -> Iterator[str]:
        """An `Includer` is its own iterator."""
        return self

    def __next__(self) -> str:
        """
        Return the next line of expanded content, throwing
        `StopIteration` at end of file.
        """
        line = self.readline()
        if len(line) == 0:
            raise StopIteration

        return line

    def getvalue(self: Self) -> str:
        """
        Retrieve the entire expanded content, as a single string. The
        current file offset is neither used nor changed.

        :return: The entire expanded content as a single string.
        :raises ValueError: If the `Includer` is closed.
        """
        self._check_open()
        return self._text

    # -----------------------------------------------------------------
    # Positioning
    # -----------------------------------------------------------------

    def seek(self: Self, offset: int, whence: int = 0) -> int:
        """
        Change the current offset within the expanded content.

        :param offset: The new offset, interpreted according to `whence`.
        :param whence: `0` (the default) to seek relative to the beginning of
            the content, `1` to seek relative to the current offset, `2` to
            seek relative to the end of the content.
        :return: The new absolute offset.
        :raises ValueError: If the `Includer` is closed, or if `whence` is
            invalid, or if the resulting offset is negative.
        """
        self._check_open()
        if whence == 0:
            new_pos = offset
        elif whence == 1:
            new_pos = self._pos + offset
        elif whence == 2:
            new_pos = len(self._text) + offset
        else:
            raise ValueError(f"Invalid whence value: {whence}")

        if new_pos < 0:
            raise ValueError(f"Negative seek position: {new_pos}")

        self._pos = min(new_pos, len(self._text))
        return self._pos

    def tell(self: Self) -> int:
        """
        Get the current offset within the expanded content.

        :return: The current offset.
        :raises ValueError: If the `Includer` is closed.
        """
        self._check_open()
        return self._pos

    # -----------------------------------------------------------------
    # Unsupported operations
    # -----------------------------------------------------------------

    def write(self: Self, s: str) -> int:
        """Not supported: `Includer` objects are read-only."""
        raise UnsupportedOperation("Includers are read-only file objects.")

    def writelines(self: Self, lines: Iterable[str]) -> None:
        """Not supported: `Includer` objects are read-only."""
        raise UnsupportedOperation("Includers are read-only file objects.")

    def truncate(self: Self, size: int | None = None) -> int:
        """Not supported: `Includer` objects are read-only."""
        raise UnsupportedOperation("Includers are read-only file objects.")

    def detach(self: Self) -> BinaryIO:
        """Not supported: there's no underlying binary buffer."""
        raise UnsupportedOperation("Includers have no underlying buffer.")

    # -----------------------------------------------------------------
    # Private methods
    # -----------------------------------------------------------------

    def _check_open(self: Self) -> None:
        if self.closed:
            raise ValueError("I/O operation on closed file.")

    def _process_includes(
        self: Self,
        file_in: TextIO,
        filename: str | None,
        buf: list[str],
        level: int,
    ) -> None:
        log.debug(f'Processing includes in "{filename}"')

        for line in file_in:
            if (match := self._include_pattern.search(line)) is None:
                buf.append(line)
                continue

            if level >= self._max_nest_level:
                raise MaxNestingExceededError(
                    f"Exceeded maximum include depth of "
                    f"{self._max_nest_level}"
                )

            log.debug(f"Found include directive: {line.rstrip()}")
            f, included_name = self._open(match.group(1), filename)
            if self._before_include is not None:
                t = Template(self._before_include)
                buf.append(t.safe_substitute(FILE=included_name))

            with f:
                self._process_includes(f, included_name, buf, level + 1)

            if self._after_include is not None:
                t = Template(self._after_include)
                buf.append(t.safe_substitute(FILE=included_name))

    def _open(
        self: Self, name_to_open: str, enclosing_file: str | None
    ) -> tuple[TextIO, str]:
        if not os.path.isabs(name_to_open):
            # Not an absolute path. Base it on the enclosing file's
            # directory, or on the current directory, if the enclosing
            # file has no name.
            if enclosing_file is None:
                enclosing_dir = os.getcwd()
            else:
                enclosing_dir = os.path.dirname(enclosing_file)

            name_to_open = os.path.join(enclosing_dir, name_to_open)

        log.debug(
            f'Opening "{name_to_open}" with encoding ' f"{self._encoding}"
        )

        # NOTE: The caller owns the returned handle and is responsible for
        # closing it; opening it in a "with" block here would hand back an
        # already-closed file.
        try:
            return (open(name_to_open, encoding=self._encoding), name_to_open)
        except OSError as e:
            raise IncludeError(f'Unable to open "{name_to_open}": {e}') from e


# ---------------------------------------------------------------------------
# Public functions
# ---------------------------------------------------------------------------


def preprocess(file: TextIO, output: TextIO, encoding: str = "utf-8") -> None:
    """
    Process all include directives in the specified file, writing the
    expanded result to `output`.

    **Parameters**

    - `file`: File-like object to expand.
    - `output` (`file`): A file or file-like object to receive the output.
    - `encoding` (`str`): String encoding for included files. Defaults to
      UTF-8.
    """
    with Includer(file, encoding=encoding) as f:
        for line in f:
            output.write(line)
