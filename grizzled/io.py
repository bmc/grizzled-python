# $Id$

"""
Input/Output utility methods and classes.
"""
# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

from __future__ import absolute_import

import os

# ---------------------------------------------------------------------------
# Classes
# ---------------------------------------------------------------------------

class AutoFlush(object):
    """
    An C{AutoFlush} wraps a file-like object and flushes the output
    (via a call to C{flush()}) after every write operation. Here's how
    to use an C{AutoFlush} object to force standard output to flush after
    every write::

        import sys
        from grizzled.io import AutoFlush

        sys.stdout = AutoFlush(sys.stdout)
    """
    def __init__(self, f):
        """
        Create a new C{AutoFlush} object to wrap a file-like object.

        @type f:  file
        @param f: A file-like object that contains both a C{write()} method
                  and a C{flush()} object.
        """
        self.__file = f

    def write(self, buf):
        """
        Write the specified buffer to the file.

        @type buf:  string or bytes
        @param buf: buffer to write
        """
        self.__file.write(buf)
        self.__file.flush()

    def flush(self):
        """
        Force a flush.
        """
        self.__file.flush()

    def truncate(self, size=-1):
        """
        Truncate the underlying file. Might fail.

        @type size:  int
        @param size: Where to truncate. If less than 0, then file's current
                     position is used
        """
        if size < 0:
            size = self.__file.tell()
        self.__file.truncate(size)

    def tell(self):
        """
        Return the file's current position, if applicable.

        @rtype:  int
        @return: Current file position
        """
        return self.__file.tell()

    def seek(self, offset, whence=os.SEEK_SET):
        """
        Set the file's current position. The C{whence} argument is optional;
        legal values are:

         - C{os.SEEK_SET} or 0: absolute file positioning (default)
         - C{os.SEEK_CUR} or 1: seek relative to the current position
         - C{os.SEEK_END} or 2: seek relative to the file's end

        There is no return value. Note that if the file is opened for
        appending (mode 'a' or 'a+'), any C{seek()} operations will be
        undone at the next write. If the file is only opened for writing in
        append mode (mode 'a'), this method is essentially a no-op, but it
        remains useful for files opened in append mode with reading enabled
        (mode 'a+'). If the file is opened in text mode (without 'b'), only
        offsets returned by C{tell()} are legal. Use of other offsets
        causes undefined behavior.

        Note that not all file objects are seekable.

        @type offset:  int
        @param offset: where to seek

        @type whence:  int
        @param whence: see above
        """
        self.__file.seek(offset, whence)

    def fileno(self):
        """
        Return the integer file descriptor used by the underlying file.

        @rtype:  int
        @return: the file descriptor
        """
        return self.__file.fileno()

class MultiWriter(object):
    """
    Wraps multiple file-like objects so that they all may be written at once.
    For example, the following code arranges to have anything written to
    C{sys.stdout} go to C{sys.stdout} and to a temporary file::

        import sys
        from grizzled.io import MultiWriter

        sys.stdout = MultiWriter(sys.__stdout__, open('/tmp/log', 'w'))
    """
    def __init__(self, *args):
        """
        Create a new C{MultiWriter} object to wrap one or more file-like
        objects.

        @type args:  arguments
        @param args: One or more file-like objects to wrap
        """
        self.__files = args

    def write(self, buf):
        """
        Write the specified buffer to the wrapped files.

        @type buf:  string or bytes
        @param buf: buffer to write
        """
        for f in self.__files:
            f.write(buf)

    def flush(self):
        """
        Force a flush.
        """
        for f in self.__files:
            f.flush()

    def close(self):
        """
        Close all contained files.
        """
        for f in self.__files:
            f.close()
    
