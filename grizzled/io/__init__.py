"""
Input/Output utility methods and classes.
"""

__docformat__ = "markdown"

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

import os
from typing import IO, AnyStr, NoReturn, TextIO

from . import filelock

# ---------------------------------------------------------------------------
# Exports
# ---------------------------------------------------------------------------

__all__ = ['AutoFlush', 'MultiWriter', 'PushbackFile', 'filelock']

# ---------------------------------------------------------------------------
# Classes
# ---------------------------------------------------------------------------

class AutoFlush:
    """
    An `AutoFlush` wraps a file-like object and flushes the output
    (via a call to `flush()` after every write operation. Here's how
    to use an `AutoFlush` object to force standard output to flush after
    every write:

    ```python
    import sys
    from grizzled.io import AutoFlush

    sys.stdout = AutoFlush(sys.stdout)
    ```
    """
    def __init__(self, f: IO) -> None:
        """
        Create a new `AutoFlush` object to wrap a file-like object.

        :param f: Open file-like object to wrap.
        """
        self._file = f

    def write(self, buf: bytes | bytearray | AnyStr):
        """
        Write the specified buffer to the file.

        :param buf: Buffer to write to the file. Can be a string, bytes, or
            bytearray.
        :raises IOError: If the write operation fails.
        """
        self._file.write(buf)
        self._file.flush()

    def flush(self) -> None:
        """
        Force a flush.
        """
        self._file.flush()

    def truncate(self, size: int =-1) -> None:
        """
        Truncate the underlying file. Might fail.

        :param size: Where to truncate. If less than 0, then file's current
            position is used.
        :raises IOError: If the truncate operation fails.
        """
        if size < 0:
            size = self._file.tell()
        self._file.truncate(size)

    def tell(self) -> int:
        """
        Return the file's current position, if applicable.

        :return: Current file position.
        :raises IOError: If the tell operation fails.
        """
        return self._file.tell()

    def seek(self, offset: int, whence: int = os.SEEK_SET) -> None:
        """
        Set the file's current position. The `whence` argument is optional;
        legal values are:

        - `os.SEEK_SET` or 0: absolute file positioning (default)
        - `os.SEEK_CUR` or 1: seek relative to the current position
        - `os.SEEK_END` or 2: seek relative to the file's end

        There is no return value. Note that if the file is opened for appending
        (mode 'a' or 'a+'), any `seek()` operations will be undone at the next
        write. If the file is only opened for writing in append mode (mode
        'a'), this method is essentially a no-op, but it remains useful for
        files opened in append mode with reading enabled (mode 'a+'). If the
        file is opened in text mode (without 'b'), only offsets returned by
        `tell()` are legal. Use of other offsets causes undefined behavior.

        Note that not all file objects are seekable.

        :param offset: Offset to seek to.
        :param whence: Optional; defaults to `os.SEEK_SET`. Specifies the
            reference point for the offset.
        :raises IOError: If the seek operation fails.
        """
        self._file.seek(offset, whence)

    def fileno(self) -> int:
        """
        Return the integer file descriptor used by the underlying file.

        :return: Integer file descriptor.
        :raises IOError: If the operation fails.
        """
        return self._file.fileno()


class MultiWriter:
    """
    Wraps multiple file-like objects so that they all may be written at once.
    For example, the following code arranges to have anything written to
    `sys.stdout` go to `sys.stdout` and to a temporary file:

    ```python
    import sys
    from grizzled.io import MultiWriter

    sys.stdout = MultiWriter(sys.__stdout__, open('/tmp/log', 'w'))
    ```
    """
    def __init__(self, *args: IO):
        """
        Create a new `MultiWriter` object to wrap one or more file-like
        objects.

        :param args: One or more file-like objects to wrap.
        """
        self._files = list(args)

    def write(self, buf: bytes | bytearray | AnyStr) -> None:
        """
        Write the specified buffer to the wrapped files.

        :param buf: Buffer to write to the wrapped files.
        """
        for f in self._files:
            f.write(buf)

    def flush(self) -> None:
        """
        Force a flush.
        """
        for f in self._files:
            f.flush()

    def close(self) -> None:
        """
        Close all contained files.
        """
        for f in self._files:
            f.close()


class PushbackFile:
    """
    A file-like wrapper object that permits pushback.
    """
    def __init__(self, f: TextIO):
        """
        Create a new `PushbackFile` object to wrap a file-like object.

        :param f: The file-like object to wrap.
        """
        self.__buf = [c for c in ''.join(f.readlines())]

    def write(self, buf: bytes | bytearray | AnyStr):
        """
        Write the specified buffer to the file. This method throws an
        unconditional exception, since `PushbackFile` objects are read-only.

        :param buf: Buffer to write to the file.
        :raises NotImplementedError: unconditionally
        """
        raise NotImplementedError('PushbackFile is read-only')

    def pushback(self, s: str) -> None:
        """
        Push a character or string back onto the input stream.

        :param s: the string to push back onto the input stream
        """
        self.__buf = [c for c in s] + self.__buf

    def unread(self, s: str) -> None:
        """
        Alias for `pushback()`.

        :param s: the string to push back onto the input stream
        """
        self.pushback(s)

    def read(self, n: int = -1) -> str:
        """
        Read *n* bytes from the open file as a string.
        :param n: Number of bytes to read. A negative number instructs
            `read()` to read all remaining bytes.
        :return: The bytes read, joined into a string.
        """
        resultBuf = None
        if n > len(self.__buf):
            n = len(self.__buf)

        if (n < 0) or (n >= len(self.__buf)):
            resultBuf = self.__buf
            self.__buf = []

        else:
            resultBuf = self.__buf[0:n]
            self.__buf = self.__buf[n:]

        return ''.join(resultBuf)

    def readline(self):
        """
        Read the next line from the file.

        :return: The next line from the file, including the newline character
            if present.
        """
        i = 0
        while i < len(self.__buf) and (self.__buf[i] != '\n'):
            i += 1

        result = self.__buf[0:i+1]
        self.__buf = self.__buf[i+1:]
        return ''.join(result)

    def readlines(self):
        """
        Read all remaining lines in the file.

        :return: All remaining lines in the file as a single string.
        """
        return self.read(-1)

    def __iter__(self):
        """
        Returns this object, since it is its own iterator.
        """
        return self

    def __next__(self):
        """
        Return the next line from the file, or raise StopIteration if at EOF.
        """
        line = self.readline()
        if (line is None) or (len(line) == 0):
            raise StopIteration
        return line

    def close(self):
        """Close the file. A no-op in this class."""
        pass

    def flush(self):
        """
        Force a flush. This method throws an unconditional exception, since
        `PushbackFile` objects are read-only.

        :raises NotImplementedError: always
        """
        raise NotImplementedError('PushbackFile is read-only')

    def truncate(self, size: int =-1) -> NoReturn:
        """
        Truncate the underlying file. This method throws an unconditional
        exception, since `PushbackFile` objects are read-only.

        :param size: Where to truncate. If less than 0, then file's current
            position is used.
        :raises NotImplementedError: always
        """
        raise NotImplementedError()

    def tell(self) -> int:
        """
        Return the file's current position, if applicable. This method throws
        an unconditional exception, since `PushbackFile` objects are
        read-only.

        :raises NotImplementedError: always
        """
        raise NotImplementedError()

    def seek(self, offset, whence=os.SEEK_SET):
        """
        Set the file's current position. This method throws an unconditional
        exception, since `PushbackFile` objects are not seekable.

        :raises NotImplementedError: always
        """
        raise NotImplementedError('PushbackFile is not seekable')

    def fileno(self):
        """
        Return the integer file descriptor used by the underlying file. This
        method always returns -1.

        :return: Always -1.
        """
        return -1

