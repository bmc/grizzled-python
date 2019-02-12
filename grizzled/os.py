"""
Overview
========

The `grizzled.os` module contains some operating system-related functions and
classes. It is a conceptual extension of the standard Python `os` module.
"""

__docformat__ = "markdown"

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

import logging
import os as _os
import sys
import glob
from contextlib import contextmanager
from typing import Sequence, Optional, Union, NoReturn

# ---------------------------------------------------------------------------
# Exports
# ---------------------------------------------------------------------------

__all__ = ['daemonize', 'DaemonError', 'working_directory', 'path_separator',
           'find_command', 'spawnd']


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

PATH_SEPARATOR = {'nt' : ';', 'posix' : ':', 'java' : ':'}
FILE_SEPARATOR = {'nt' : '\\', 'posix' : '/', 'java' :'/'}

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

log = logging.getLogger('grizzled.os')

# ---------------------------------------------------------------------------
# Public classes
# ---------------------------------------------------------------------------

class DaemonError(OSError):
    """
    Thrown by `daemonize()` when an error occurs while attempting to create
    a daemon.
    """
    pass

# ---------------------------------------------------------------------------
# Public functions
# ---------------------------------------------------------------------------

def path_separator() -> str:
    """
    Get the path separator for the current operating system. The path
    separator is used to separate elements of a path string, such as
    "PATH" or "CLASSPATH". (It's a ":" on Unix-like systems and a ";"
    on Windows.)

    :rtype: str
    :return: the path separator
    """
    return PATH_SEPARATOR[_os.name]


def path_elements(path: str) -> Sequence[str]:
    """
    Given a path string value (e.g., the value of the environment variable
    `PATH`), this function returns each item in the path.

    **Parameters**

    - `path` (`str`): the path to break up

    **Returns**

    list of pieces of the path
    """
    return path.split(path_separator())


@contextmanager
def working_directory(directory: str):
    """
    This function is intended to be used as a `with` statement context
    manager. It allows you to replace code like this:

        original_directory = _os.getcwd()
        try:
            _os.chdir(some_dir)
            what_you_want_to_do()
        finally:
            _os.chdir(original_directory)

    with something simpler:

        from grizzled.os import working_directory

        with working_directory(some_dir):
            what_you_want_to_do()

    **Parameters**

    - `directory` (`str`): directory in which to execute your code
    """
    original_directory = _os.getcwd()
    try:
        _os.chdir(directory)
        yield directory

    finally:
        _os.chdir(original_directory)

def find_command(command_name: str,
                 path: Optional[Union[str, Sequence[str]]] = None) -> str:
    """
    Determine whether the specified system command exists in the specified
    path.

    **Parameters**

    - `command_name` (`str`): (simple) file name of command to find
    - `path` (`str` or sequence): Path string (or sequence of path elements)
      to use. Defaults to environment `PATH`.

    **Returns**

    Full path to the command, or `None` if not found.
    """
    if not path:
        path = _os.environ.get('PATH', '.')

    if type(path) == str:
        path = path.split(path_separator())
    elif (type(path) == list) or (type(path) == tuple):
        pass
    else:
        assert False, 'path parameter must be a list, tuple or a string'

    found = None
    for p in path:
        full_path = _os.path.join(p, command_name)
        for p2 in glob.glob(full_path):
            if _os.access(p2, _os.X_OK):
                found = p2
                break

        if found:
            break

    return found


def spawnd(path: str,
           args: Sequence[str],
           pidfile: Optional[str] = None) -> NoReturn:
    """
    Run a command as a daemon. This method is really just shorthand for the
    following code:

        from grizzled.os import daemonize
        import os

        daemonize(pidfile=pidfile)
        os.execv(path, args)

    **Parameters**

    - `path` (`str`): Full path to program to run
    - `args` (list of `str`): List of command arguments. The first element in
      this list must be the command name (i.e., arg0).
    - `pidfile` (`str`): Path to file to which to write daemon's process ID.
      The string may contain a `${pid}` token, which is replaced with the
      process ID of the daemon. e.g.: `"/var/run/myserver-${pid}"`
    """
    daemonize(no_close=True, pidfile=pidfile)
    _os.execv(path, args)


def daemonize(no_close: bool = False, pidfile: Optional[str] = None):
    """
    Convert the calling process into a daemon. To make the current Python
    process into a daemon process, you need two lines of code:

        from grizzled.os import daemonize
        daemonize.daemonize()

    If `daemonize()` fails for any reason, it throws a `DaemonError`,
    which is a subclass of the standard `OSError` exception. also logs debug
    messages, using the standard Python `logging` package, to channel
    "grizzled.os.daemon".

    **Adapted from:** <http://software.clapper.org/daemonize/>

    **See Also:**

    - Stevens, W. Richard. _Unix Network Programming_ (Addison-Wesley, 1990).

    **Parameters**

    - `no_close` (`bool`): If `True`, don't close the file descriptors. Useful
      if the calling process has already redirected file descriptors to an
      output file. **Warning**: Only set this parameter to `True` if you're
      _sure_ there are no open file descriptors to the calling terminal.
      Otherwise, you'll risk having the daemon re-acquire a control terminal,
      which can cause it to be killed if someone logs off that terminal.
    - `pidfile` (`str`): Path to file to which to write daemon's process ID.
      The string may contain a `${pid}` token, which is replaced with the
      process ID of the daemon. e.g.: `"/var/run/myserver-${pid}"`

    **Raises**

    `DaemonError`: Error during daemonizing
    """
    log = logging.getLogger('grizzled.os.daemon')

    def _fork():
        try:
            return _os.fork()
        except OSError as e:
            raise DaemonError(('Cannot fork', e.errno, e.strerror))

    def _redirect_file_descriptors():
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

            _os.open(NULL_DEVICE, _os.O_RDWR)
            _os.dup2(0, 1)
            _os.dup2(0, 2)


    if _os.name != 'posix':
        import errno
        raise DaemonError(
            ('daemonize() is only supported on Posix-compliant systems.',
             errno.ENOSYS, _os.strerror(errno.ENOSYS))
        )

    try:
        # Fork once to go into the background.

        log.debug('Forking first child.')
        pid = _fork()
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
        pid = _fork()
        if pid != 0:
            # Original child. Exit.
            _os._exit(0)

        # This is the second child. Set the umask.
        log.debug('Setting umask')
        _os.umask(UMASK)

        # Go to a neutral corner (i.e., the primary file system, so
        # the daemon doesn't prevent some other file system from being
        # unmounted).
        log.debug('Changing working directory to "%s"' % WORKDIR)
        _os.chdir(WORKDIR)

        # Unless no_close was specified, close all file descriptors.
        if not no_close:
            log.debug('Redirecting file descriptors')
            _redirect_file_descriptors()

        if pidfile:
            from string import Template
            t = Template(pidfile)
            pidfile = t.safe_substitute(pid=str(_os.getpid()))
            open(pidfile, 'w').write(str(_os.getpid()) + '\n')

    except DaemonError:
        raise

    except OSError as e:
        raise DaemonError(('Unable to daemonize()', e.errno, e.strerror))
