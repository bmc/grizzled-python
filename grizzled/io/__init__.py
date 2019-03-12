"""
Input/Output utility methods and classes.
"""

__docformat__ = "markdown"

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

import os
from typing import IO, TextIO, Union, AnyStr, NoReturn, Sequence, Iterable
from . import filelock

# ---------------------------------------------------------------------------
# Exports
# ---------------------------------------------------------------------------

__all__ = ['AutoFlush', 'MultiWriter', 'PushbackFile', 'filelock']

# ---------------------------------------------------------------------------
# Classes
# ---------------------------------------------------------------------------

class AutoFlush(object):
    """
    An `AutoFlush` wraps a file-like object and flushes the output
    (via a call to `flush()` after every write operation. Here's how
    to use an `AutoFlush` object to force standard output to flush after
    every write:

        import sys
        from grizzled.io import AutoFlush

        sys.stdout = AutoFlush(sys.stdout)
    """
    def __init__(self, f: IO) -> NoReturn:
        """
        Create a new `AutoFlush` object to wrap a file-like object.

        **Parameters**

        - `f` (file-like object): A file-like object that contains both a
          `write()` method and a `flush()` method.
        """
        self._file = f

    def write(self, buf: Union[bytes, bytearray, AnyStr]):
        """
        Write the specified buffer to the file.

        **Parameters**

        - `buf` (`str` or `bytes`): buffer to write
        """
        self._file.write(buf)
        self._file.flush()

    def flush(self) -> NoReturn:
        """
        Force a flush.
        """
        self._file.flush()

    def truncate(self, size: int =-1) -> NoReturn:
        """
        Truncate the underlying file. Might fail.

        **Parameters**

        - `size` (`int`): Where to truncate. If less than 0, then file's
          current position is used.
        """
        if size < 0:
            size = self._file.tell()
        self._file.truncate(size)

    def tell(self) -> int:
        """
        Return the file's current position, if applicable.
        """
        return self._file.tell()

    def seek(self, offset: int, whence: int = os.SEEK_SET) -> NoReturn:
        """
        Set the file's current position. The `whence` argument is optional;
        legal values are:

        - `os.SEEK_SET` or 0: absolute file positioning (default)
        - `os.SEEK_CUR` or 1: seek relative to the current position
        - `os.SEEK_END` or 2: seek relative to the file's end

        There is no return value. Note that if the file is opened for
        appending (mode 'a' or 'a+'), any `seek()` operations will be undone
        at the next write. If the file is only opened for writing in append
        mode (mode 'a'), this method is essentially a no-op, but it remains
        useful for files opened in append mode with reading enabled (mode
        'a+'). If the file is opened in text mode (without 'b'), only offsets
        returned by `tell()` are legal. Use of other offsets causes
        undefined behavior.

        Note that not all file objects are seekable.
        """
        self._file.seek(offset, whence)

    def fileno(self) -> int:
        """
        Return the integer file descriptor used by the underlying file.
        """
        return self._file.fileno()


class MultiWriter(object):
    """
    Wraps multiple file-like objects so that they all may be written at once.
    For example, the following code arranges to have anything written to
    `sys.stdout` go to `sys.stdout` and to a temporary file:

        import sys
        from grizzled.io import MultiWriter

        sys.stdout = MultiWriter(sys.__stdout__, open('/tmp/log', 'w'))
    """
    def __init__(self, *args: IO):
        """
        Create a new `MultiWriter` object to wrap one or more file-like
        objects.

        **Parameters**

        - `args` (iterable): One or more file-like objects to wrap
        """
        self._files = list(args)

    def write(self, buf: Union[bytes, bytearray, AnyStr]) -> NoReturn:
        """
        Write the specified buffer to the wrapped files.

        **Parameters**

        - `buf` (`str` or bytes): buffer to write
        """
        for f in self._files:
            f.write(buf)

    def flush(self) -> NoReturn:
        """
        Force a flush.
        """
        for f in self._files:
            f.flush()

    def close(self) -> NoReturn:
        """
        Close all contained files.
        """
        for f in self._files:
            f.close()


class PushbackFile(object):
    """
    A file-like wrapper object that permits pushback.
    """
    def __init__(self, f: TextIO):
        """
        Create a new `PushbackFile` object to wrap a file-like object.

        **Parameters**

        - `f` (file-like object): A file-like object that contains both a
          `write()` method and a `flush()` method.
        """
        self.__buf = [c for c in ''.join(f.readlines())]

    def write(self, buf: Union[bytes, bytearray, AnyStr]):
        """
        Write the specified buffer to the file. This method throws an
        unconditional exception, since `PushbackFile` objects are read-only.

        **Parameters**

        - `buf` (`str` or `bytes`): buffer to write

        **Raises**

        `NotImplementedError`: unconditionally
        """
        raise NotImplementedError('PushbackFile is read-only')

    def pushback(self, s: str) -> NoReturn:
        """
        Push a character or string back onto the input stream.

        **Parameters**

        `s` (`str`): the string to push back onto the input stream
        """
        self.__buf = [c for c in s] + self.__buf

    unread=pushback

    def read(self, n: int = -1) -> str:
        """
        Read *n* bytes from the open file as a string.

        **Parameters**

        - `n` (`int`): Number of bytes to read. A negative number instructs
          `read()` to read all remaining bytes.

        **Returns**

        the bytes read, joined into a string
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
        """
        return self.read(-1)

    def __iter__(self):
        return self

    def __next__(self):
        line = self.readline()
        if (line == None) or (len(line) == 0):
            raise StopIteration
        return line

    def close(self):
        """Close the file. A no-op in this class."""
        pass

    def flush(self):
        """
        Force a flush. This method throws an unconditional exception, since
        `PushbackFile` objects are read-only.

        **Raises**

        `NotImplementedError`: unconditionally
        """
        raise NotImplementedError('PushbackFile is read-only')

    def truncate(self, size: int =-1) -> NoReturn:
        """
        Truncate the underlying file. This method throws an unconditional
        exception, since `PushbackFile` objects are read-only.

        **Parameters**

        - `size` (`int`): Where to truncate. If less than 0, then file's
          current position is used.

        **Raises**

        `NotImplementedError`: unconditionally
        """
        raise NotImplementedError()

    def tell(self) -> int:
        """
        Return the file's current position, if applicable. This method throws
        an unconditional exception, since `PushbackFile` objects are
        read-only.

        **Raises**

        `NotImplementedError`: unconditionally
        """
        raise NotImplementedError()

    def seek(self, offset, whence=os.SEEK_SET):
        """
        Set the file's current position. This method throws an unconditional
        exception, since `PushbackFile` objects are not seekable.

        **Raises**

        `NotImplementedError`: unconditionally
        """
        raise NotImplementedError('PushbackFile is not seekable')

    def fileno(self):
        """
        Return the integer file descriptor used by the underlying file. This
        method always returns -1.
        """
        return -1


def extract_into(self, output_dir: str) -> NoReturn:
        """
        Unpack the zip file into the specified output directory.

        **Parameters**

        - `output_dir` (`str`): Path to output directory. The directory is
          created if it doesn't already exist.
        """
        if not output_dir.endswith(':') and not os.path.exists(output_dir):
            os.mkdir(output_dir)

        # extract files to directory structure
        for i, name in enumerate(self.namelist()):
            if not name.endswith('/'):
                directory = os.path.dirname(name)
                if directory == '':
                    directory = None
                if directory:
                    directory = os.path.join(output_dir, directory)
                    if not os.path.exists(directory):
                        os.makedirs(directory)

                outfile = open(os.path.join(output_dir, name), 'wb')
                outfile.write(self.read(name))
                outfile.flush()
                outfile.close()
