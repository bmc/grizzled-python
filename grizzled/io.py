# $Id$

"""
Input/Output utility methods and classes.
"""

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
    
