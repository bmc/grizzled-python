#!/usr/bin/env python
#
# $Id$

# NOTE: Documentation is intended to be processed by epydoc and contains
# epydoc markup.

"""
Overview
========
The C{grizzled.os} module contains some operating system-related methods and
classes. It is a conceptual extension of the standard Python C{os} module.
"""
from __future__ import absolute_import

__all__ = ['daemonize', 'DaemonError', 'workingDirectory', 'getPathSeparator']

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

import logging
import os as _os
import sys
from contextlib import contextmanager

from grizzled.decorators import deprecated

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Default daemon parameters.
# File mode creation mask of the daemon.
UMASK = 0

# Default working directory for the daemon.
WORKDIR = "/"

# Default maximum for the number of available file descriptors.
MAXFD = 1024

# The standard I/O file descriptors are redirected to /dev/null by default.
if (hasattr(_os, "devnull")):
    NULL_DEVICE = _os.devnull
else:
    NULL_DEVICE = "/dev/null"

# The path separator for the operating system.

PATH_SEPARATOR = {'nt' : ';', 'posix' : ':'}
FILE_SEPARATOR = {'nt' : '\\', 'posix' : '/'}

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

log = logging.getLogger('grizzled.os')

# ---------------------------------------------------------------------------
# Public classes
# ---------------------------------------------------------------------------

class DaemonError(OSError):
    """
    Thrown by L{C{daemonize()}<daemonize>} when an error occurs while
    attempting to create a daemon.
    """
    pass

# ---------------------------------------------------------------------------
# Public functions
# ---------------------------------------------------------------------------

@deprecated(since='0.4', message='use path_separator')
def getPathSeparator():
    return get_path_separator

def path_separator():
    """
    Get the path separator for the current operating system. The path
    separator is used to separate elements of a path string, such as
    "PATH" or "CLASSPATH". (It's a ":" on Unix-like systems and a ";"
    on Windows.)

    @rtype: str
    @return: the path separator
    """
    return PATH_SEPARATOR[_os.name]

def file_separator():
    """
    Get the file separator for the current operating system. The file
    separator is used to separate file elements in a pathname. (It's
    "/" on Unix-like systems and a "\\" on Windows.)

    @rtype: str
    @return: the file separator
    """
    return FILE_SEPARATOR[_os.name]

@deprecated(since='0.4', message='use working_directory')
def workingDirectory(directory):
    return working_directory(directory)

@contextmanager
def working_directory(directory):
    """
    This function is intended to be used as a C{with} statement context
    manager. It allows you to replace code like this::

        import os

        original_directory = os.getcwd()
        try:
            os.chdir(some_dir)
            ... bunch of code ...
        finally:
            os.chdir(original_directory)

    with something simpler::

        from __future__ import with_statement
        from grizzled.os import working_directory

        with working_directory(some_dir):
            ... bunch of code ...

    @type directory:  path
    @param directory: directory in which to execute

    @return: yields the C{directory} parameter
    """
    original_directory = _os.getcwd()
    try:
        _os.chdir(directory)
        yield directory

    finally:
        _os.chdir(original_directory)

def daemonize(no_close=False):
    """
    Convert the calling process into a daemon. To make the current Python
    process into a daemon process, you need two lines of code::

        from grizzled.os import daemon
        daemon.daemonize()

    If C{daemonize()} fails for any reason, it throws a
    L{C{DaemonError}<DaemonError>} exception, which is a subclass of the
    standard C{OSError} exception. also logs debug messages, using the
    standard Python C{logging} package, to channel 'grizzled.os.daemon'.

    B{Adapted from:}

     - U{http://www.clapper.org/software/daemonize/}

    B{See Also:}

     - Stevens, W. Richard. I{Unix Network Programming} (Addison-Wesley, 1990).

    @type no_close:  boolean
    @param no_close: If C{True}, don't close the file descriptors. Useful
                     if the calling process has already redirected file
                     descriptors to an output file. B{Warning}: Only set this
                     parameter to C{True} if you're I{sure} there are no open
                     file descriptors to the calling terminal. Otherwise,
                     you'll risk having the daemon re-acquire a control
                     terminal, which can cause it to be killed if someone logs
                     off that terminal.

    @raise DaemonError: Error during daemonizing
    """
    log = logging.getLogger('grizzled.os.daemon')

    def __fork():
        try:
            return os.fork()
        except OSError, e:
            raise DaemonError, ('Cannot fork', e.errno, e.strerror)

    def __redirect_file_descriptors():
        import resource  # POSIX resource information
        maxfd = resource.getrlimit(resource.RLIMIT_NOFILE)[1]
        if maxfd == resource.RLIM_INFINITY:
            maxfd = MAXFD

        # Close all file descriptors.

        for fd in range(0, maxfd):
            # Only close TTYs.
            try:
                _os.ttyname(fd)
            except:
                continue

            try:
                _os.close(fd)
            except OSError:
                # File descriptor wasn't open. Ignore.
                pass

            # Redirect standard input, output and error to something safe.
            # os.open() is guaranteed to return the lowest available file
            # descriptor (0, or standard input). Then, we can dup that
            # descriptor for standard output and standard error.

            _os.open(NULL_DEVICE, os.O_RDWR)
            _os.dup2(0, 1)
            _os.dup2(0, 2)


    if _os.name != 'posix':
        import errno
        raise DaemonError, \
              ('daemonize() is only supported on Posix-compliant systems.',
               errno.ENOSYS, _os.strerror(errno.ENOSYS))

    try:
        # Fork once to go into the background.

        log.debug('Forking first child.')
        pid = __fork()
        if pid != 0:
            # Parent. Exit using os._exit(), which doesn't fire any atexit
            # functions.
            _os._exit(0)

        # First child. Create a new session. os.setsid() creates the session
        # and makes this (child) process the process group leader. The process
        # is guaranteed not to have a control terminal.
        log.debug('Creating new session')
        _os.setsid()

        # Fork a second child to ensure that the daemon never reacquires
        # a control terminal.
        log.debug('Forking second child.')
        pid = __fork()
        if pid != 0:
            # Original child. Exit.
            _os._exit(0)

        # This is the second child. Set the umask.
        log.debug('Setting umask')
        os.umask(UMASK)

        # Go to a neutral corner (i.e., the primary file system, so
        # the daemon doesn't prevent some other file system from being
        # unmounted).
        log.debug('Changing working directory to "%s"' % WORKDIR)
        _os.chdir(WORKDIR)

        # Unless no_close was specified, close all file descriptors.
        if not no_close:
            log.debug('Redirecting file descriptors')
            __redirect_file_descriptors()

    except DaemonError:
        raise

    except OSError, e:
        raise DaemonError, ('Unable to daemonize()', e.errno, e.strerror)

# ---------------------------------------------------------------------------
# Main program (for testing)
# ---------------------------------------------------------------------------

if __name__ == '__main__':

    log = logging.getLogger('grizzled.os')
    hdlr = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s', '%T')
    hdlr.setFormatter(formatter)
    log.addHandler(hdlr)
    log.setLevel(logging.DEBUG)

    log.debug('Before daemonizing, PID=%d' % os.getpid())
    daemonize(no_close=True)
    log.debug('After daemonizing, PID=%d' % os.getpid())
    log.debug('Daemon is sleeping for 10 seconds')

    import time
    time.sleep(10)

    log.debug('Daemon exiting')
    sys.exit(0)
