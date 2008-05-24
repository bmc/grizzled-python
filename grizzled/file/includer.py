#!/usr/bin/env python
#
# $Id$

# NOTE: Documentation is intended to be processed by epydoc and contains
# epydoc markup.

'''
Introduction
============

The C{grizzled.file.includer} module contains a class that can be used to
process includes within a text file, returning a file-like object. It also
contains some utility functions that permit using include-enabled files in
other contexts.

Include Syntax
==============

The I{include} syntax is defined by a regular expression; any line that
matches the regular expression is treated as an I{include} directive. The
default regular expression matches include directives like this::

    %include "/absolute/path/to/file"
    %include "../relative/path/to/file"
    %include "local_reference"
    %include "http://localhost/path/to/my.config"

Relative and local file references are relative to the including file or
URL. That, if an C{Includer} is processing file "/home/bmc/foo.txt"
and encounters an attempt to include file "bar.txt", it will assume "bar.txt"
is to be found in "/home/bmc".

Similarly, if an C{Includer} is processing URL "http://localhost/bmc/foo.txt"
and encounters an attempt to include file "bar.txt", it will assume "bar.txt"
is to be found at "http://localhost/bmc/bar.txt".

Nested includes are permitted; that is, an included file may, itself, include
other files. The maximum recursion level is configurable and defaults to 100.

The include syntax can be changed by passing a different regular expression to
the L{C{Includer}<Includer>} class constructor.

Usage
=====

This module provides an L{C{Includer}<Includer>} class, which processes
include directives in a file and behaves like a file-like object. See the
class documentation for more details.

The module also provides a L{C{preprocess()}<preprocess>} convenience
function that can be used to preprocess a file; it returns the path to
the resulting preprocessed file. See the
L{function documentation<preprocess>} for details.

Examples
========

Preprocess a file containing include directives, then read the result::

    import includer
    import sys

    inc = includer.Includer(path)
    for line in inc:
        sys.stdout.write(line)


Use an include-enabled file with the standard Python logging module::

    import logging
    import includer

    logging.fileConfig(includer.preprocess("mylog.cfg"))

'''

__all__ = ['Includer', 'IncludeError', 'preprocess']

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

import logging
import os
import sys
import re
import tempfile
import atexit
import urllib2
import urlparse
import grizzled.exception

# ---------------------------------------------------------------------------
# Exports
# ---------------------------------------------------------------------------

__all__ = ['IncludeError', 'Includer', 'preprocess']

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

log = logging.getLogger('includer')

# ---------------------------------------------------------------------------
# Public classes
# ---------------------------------------------------------------------------

class IncludeError(grizzled.exception.ExceptionWithMessage):
    """
    Thrown by C{Includer()} when an error occurs while processing the file.
    An C{IncludeError} object always contains a single string value that
    contains an error message describing the problem.
    """
    pass

class Includer(object):
    '''
    An C{Includer} object preprocesses a path or file-like object,
    expanding include references. The resulting C{Includer} object is a
    file-like object, offering the same methods and capabilities as an open
    file.

    By default, C{Includer} supports this include syntax::

        %include "path"
        %include "url"

    However, the include directive syntax is controlled by a regular
    expression, so it can be configured.

    See the L{module documentation<includer>} for details.
    '''
    def __init__(self,
                 source,
                 include_regex='^%include\s"([^"]+)"',
                 max_nest_level=100,
                 output=None):
        """
        Create a new C{Includer} object.

        @type source:  open file-like object, path name, or URL
        @param source: the source to read and expand.

        @type include_regex:  string
        @param include_regex: Regular expression defining the include syntax.
                              Must contain a single parenthetical group
                              that can be used to extract the included file
                              or URL.

        @type max_nest_level:  int
        @param max_nest_level: Maximum include nesting level. Exceeding this
                               level causing the C{Includer} to throw an
                               C{IncludeError}

        @type output:  string or file-like object
        @param output: Save the expanded output to C{output}, which can specify
                       a path name (string) or a file-like object.

        @raise IncludeError: On error
        """

        if isinstance(source, str):
            f, is_url, name = self.__open(source, None, False)
        else:
            # Assume file-like object.
            f = source
            is_url = False
            try:
                name = source.name
            except AttributeError:
                name = None

        self.closed = False
        self.mode = None
        self.__include_pattern = re.compile(include_regex)
        self.__name = name

        if output == None:
            from cStringIO import StringIO
            output = StringIO()

        self.__maxnest = max_nest_level
        self.__nested = 0
        self.__process_includes(f, name, is_url, output)
        self.__f = output
        self.__f.seek(0)

    @property
    def name(self):
        """
        Get the name of the file being processed.
        """
        return self.__name

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
        """Close the includer, preventing any further I/O operations."""
        if not self.closed:
            self.closed = true
            self.__f.close()
            del self.__f

    def fileno(self):
        """
        Get the file descriptor. Returns the descriptor of the file being
        read.

        @rtype:  int
        @return: the file descriptor of the file being read
        """
        _complain_if_closed(self.closed)
        return self.__f.fileno()

    def isatty(self):
        """
        Determine whether the file being processed is a TTY or not.

        @return: True/False
        """
        _complain_if_closed(self.closed)
        return self.__f.isatty()

    def seek(self, pos, mode=0):
        """
        Seek to the specified file offset in the include-processed file.

        @type pos:  int
        @param pos: file offset

        @type mode:  int
        @param mode: Seek mode (0=seek from top of file,
                                1=seek relative to current file position,
                                2=seek from bottom of file)
        """
        self.__f.seek(pos, mode)

    def tell(self):
        """
        Get the current file offset. Note that seeking to a file offset
        is not supported.

        @rtype:  int
        @return: current file offset
        """
        _complain_if_closed(self.closed)
        return self.__f.tell()

    def read(self, n=-1):
        """
        Read I{n} bytes from the open file.

        @type n:  int
        @param n: Number of bytes to read. A negative number instructs
                  the method to read all remaining bytes.

        @return: the bytes read
        """
        _complain_if_closed(self.closed)
        return self.__f.read(n)

    def readline(self, length=-1):
        """
        Read the next line from the file.

        @type length:  int
        @param length: a length hint, or negative if you don't care
        """
        _complain_if_closed(self.closed)
        return self.__f.readline(length)

    def readlines(self, sizehint=0):
        """
        Read all remaining lines in the file.

        @rtype:  array
        @return: array of lines
        """
        _complain_if_closed(self.closed)
        return self.__f.readlines(sizehint)

    def truncate(self, size=None):
        """Not supported, since C{Includer} objects are read-only."""
        raise IncludeError, 'Includers are read-only file objects.'

    def write(self, s):
        """Not supported, since C{Includer} objects are read-only."""
        raise IncludeError, 'Includers are read-only file objects.'

    def writelines(self, iterable):
        """Not supported, since C{Includer} objects are read-only."""
        raise IncludeError, 'Includers are read-only file objects.'

    def flush(self):
        """No-op."""
        pass

    def getvalue(self):
        """
        Retrieve the entire contents of the file, which includes expanded,
        at any time before the C{close()} method is called.

        @rtype:  string
        @return: a single string containing the contents of the file
        """
        return ''.join(self.readlines())

    def __process_includes(self, file_in, filename, is_url, file_out):
        log.debug('Processing includes in "%s", is_url=%s' % (filename, is_url))

        for line in file_in:
            match = self.__include_pattern.search(line)
            if match:
                if self.__nested >= self.__maxnest:
                    raise IncludeError, 'Exceeded maximum include recursion ' \
                                        'depth of %d' % self.__maxnest

                inc_name = match.group(1)
                logging.debug('Found include directive: %s' % line[:-1])
                f, included_is_url, included_name = self.__open(inc_name,
                                                                filename,
                                                                is_url)
                self.__nested += 1
                self.__process_includes(f, filename, is_url, file_out)
                self.__nested -= 1
            else:
                file_out.write(line)

    def __open(self, name_to_open, enclosing_file, enclosing_file_is_url):
        is_url = False
        openFunc = None

        parsed_url = urlparse.urlparse(name_to_open)

        # Account for Windows drive letters.

        if (parsed_url.scheme != '') and (len(parsed_url.scheme) > 1):
            openFunc = urllib2.urlopen
            is_url = True

        else:
            # It's not a URL. What we do now depends on the including file.

            if enclosing_file_is_url:
                # Use the parent URL as the base URL.
                
                name_to_open = urlparse.urljoin(enclosing_file, name_to_open)
                open_func = urllib2.urlopen
                is_url = True

            elif not os.path.isabs(name_to_open):
                # Not an absolute file. Base it on the parent.

                enclosing_dir = None
                if enclosing_file == None:
                    enclosing_dir = os.getcwd()
                else:
                    enclosing_dir = os.path.dirname(enclosing_file)

                name_to_open = os.path.join(enclosing_dir, name_to_open)
                open_func = open

            else:
                open_func = open

        assert(name_to_open != None)
        assert(open_func != None)

        try:
            log.debug('Opening "%s"' % name_to_open)
            f = open_func(name_to_open)
        except:
            raise IncludeError, 'Unable to open "%s" as a file or a URL' %\
                  name_to_open
        return (f, is_url, name_to_open)
    
# ---------------------------------------------------------------------------
# Public functions
# ---------------------------------------------------------------------------

def preprocess(file_or_url, output=None, temp_suffix='.txt', temp_prefix='inc'):
    """
    Process all include directives in the specified file, returning a path
    to a temporary file that contains the results of the expansion. The
    temporary file is automatically removed when the program exits, though
    the caller is free to remove it whenever it is no longer needed.

    @type file_or_url:   string or file-like object
    @param file_or_url:  URL or path to file to be expanded; or, a file-like
                         object
 
    @type output:  file-like object
    @param output: A file or file-like object to receive the output.

    @type temp_suffix:  string
    @param temp_suffix: suffix to use with temporary file

    @type temp_prefix:  string
    @param temp_prefix: prefix to use with temporary file.

    @rtype:  string
    @return: C{output}, if C{output} is not C{None}; otherwise, the path to
             temporary file containing expanded content
    """
    result = None
    if not output:
        fd, path = tempfile.mkstemp(suffix=temp_suffix, prefix=temp_prefix)
        output = open(path, 'w')
        atexit.register(os.unlink, path)
        os.close(fd)
        result = path
    else:
        result = output

    Includer(file_or_url, output=output)
    return result

    
# ---------------------------------------------------------------------------
# Private functions
# ---------------------------------------------------------------------------

def _complain_if_closed(closed):
    if closed:
        raise IncludeError, "I/O operation on closed file"

# ---------------------------------------------------------------------------
# Main program (for testing)
# ---------------------------------------------------------------------------

if __name__ == '__main__':

    format = '%(asctime)s %(name)s %(levelname)s %(message)s'
    logging.basicConfig(level=logging.DEBUG, format=format)

    for file in sys.argv[1:]:
        import cStringIO as StringIO
        out = StringIO.StringIO()
        preprocess(file, output=out)
        
        header = 'File: %s, via preprocess()'
        sep = '-' * len(header)
        print '\n%s\n%s\n%s\n' % (sep, header, sep)
        for line in out.readlines():
            sys.stdout.write(line)
        print sep

        inc = Includer(file)
        header = 'File: %s, via Includer'
        sep = '-' * len(header)
        print '\n%s\n%s\n%s\n' % (sep, header, sep)
        for line in inc:
            sys.stdout.write(line)
        print '%s' % sep
