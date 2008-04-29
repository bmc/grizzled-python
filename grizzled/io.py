# $Id$

"""
Input/Output utility methods and classes.
"""
# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

from __future__ import absolute_import

import os
import zipfile

# ---------------------------------------------------------------------------
# Exports
# ---------------------------------------------------------------------------

__all__ = ['AutoFlush', 'MultiWriter', 'PushbackFile']

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
    
class PushbackFile(object):
    """
    A file-like wrapper object that permits pushback.
    """
    def __init__(self, f):
        """
        Create a new C{PushbackFile} object to wrap a file-like object.

        @type f:  file
        @param f: A file-like object that contains both a C{write()} method
                  and a C{flush()} object.
        """
        self.__buf = [c for c in ''.join(f.readlines())]

    def write(self, buf):
        """
        Write the specified buffer to the file.

        @type buf:  string or bytes
        @param buf: buffer to write
        """
        raise NotImplementedError, 'PushbackFile is read-only'

    def pushback(self, s):
        """
        Push a character or string back onto the input stream.
        
        @type s:  str
        @param s: the string to push back onto the input stream
        """
        self.__buf = [c for c in s] + self.__buf
        
    unread=pushback
    
    def read(self, n=-1):
        """
        Read I{n} bytes from the open file.

        @type n:  int
        @param n: Number of bytes to read. A negative number instructs
                  the method to read all remaining bytes.

        @return: the bytes read
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

    def readline(self, length=-1):
        """
        Read the next line from the file.

        @type length:  int
        @param length: a length hint, or negative if you don't care
        """
        i = 0
        while i < len(self.__buf) and (self.__buf[i] != '\n'):
            i += 1

        result = self.__buf[0:i+1]
        self.__buf = self.__buf[i+1:]
        return ''.join(result)

    def readlines(self, sizehint=0):
        """
        Read all remaining lines in the file.

        @rtype:  array
        @return: array of lines
        """
        return self.read(-1)

    def __iter__(self):
        return self

    def next(self):
        """A file object is its own iterator.

        @rtype: string
        @return: the next line from the file

        @raise StopIteration: end of file
        @raise IncludeError: on error
        """
        line = self.readline()
        if (line == None) or (len(line) == 0):
            raise StopIteration
        return line

    def close(self):
        """Close the file. A no-op in this class."""
        pass

    def flush(self):
        """
        Force a flush.
        """
        raise NotImplementedError, 'PushbackFile is read-only'

    def truncate(self, size=-1):
        """
        Truncate the underlying file. Might fail.

        @type size:  int
        @param size: Where to truncate. If less than 0, then file's current
                     position is used
        """
        raise NotImplementedError, 'PushbackFile is read-only'

    def tell(self):
        """
        Return the file's current position, if applicable.

        @rtype:  int
        @return: Current file position
        """
        raise NotImplementedError, 'PushbackFile is not seekable'

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
        raise NotImplementedError, 'PushbackFile is not seekable'

    def fileno(self):
        """
        Return the integer file descriptor used by the underlying file.

        @rtype:  int
        @return: the file descriptor
        """
        return -1

class Zip(zipfile.ZipFile):
    """
    C{Zip} extends the standard C{zipfile.ZipFile} class and provides a method
    to extract the contents of a zip file into a directory. Adapted from
    U{http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/252508}.
    """
    def __init__(self, file, mode="r",
                 compression=zipfile.ZIP_STORED,
                 allowZip64=False):
        """
        Constructor. Initialize a new zip file.

        @type file:  str
        @param file: path to zip file

        @type mode:  str
        @param mode: Open mode. Valid values are 'r' (read), 'w' (write), and
                     'a' (append)

        @type compression:  int
        @param compression: Compression type. Valid values:
                            C{zipfile.ZIP_STORED}, C{zipfile.ZIP_DEFLATED}

        @type allowZip64:  bool
        @param allowZip64: Whether or not Zip64 extensions are to be used
        """
        zipfile.ZipFile.__init__(self, file, mode, compression, allowZip64)
        self.zipFile = file

    def extract(self, outputDir):
        """
        Unpack the zip file into the specified output directory.

        @type outputDir:  str
        @param outputDir: path to output directory. The directory is
                          created if it doesn't already exist.
        """
        if not outputDir.endswith(':') and not os.path.exists(outputDir):
            os.mkdir(outputDir)

        num_files = len(self.namelist())

        # extract files to directory structure
        for i, name in enumerate(self.namelist()):
            if not name.endswith('/'):
                directory = os.path.dirname(name)                        
                if directory == '':
                    directory = None
                if directory:
                    directory = os.path.join(outputDir, directory)
                    if not os.path.exists(directory):
                        os.makedirs(directory)

                outfile = open(os.path.join(outputDir, name), 'wb')
                outfile.write(self.read(name))
                outfile.flush()
                outfile.close()
