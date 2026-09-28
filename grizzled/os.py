"""
The `grizzled.os` module contains some operating system-related functions and
classes. It is a conceptual extension of the standard Python `os` module.
"""

__docformat__ = "markdown"

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

import errno
import logging
import os as _os
from contextlib import suppress
from pathlib import Path
from typing import NoReturn, Sequence

from .file import _map_paths

# ---------------------------------------------------------------------------
# Exports
# ---------------------------------------------------------------------------

__all__ = [
    "daemonize",
    "DaemonError",
    "find_command",
    "spawnd",
    "get_terminal_size",
    "ENV_COLUMNS",
    "ENV_LINES",
    "DEFAULT_TERMINAL_WIDTH",
    "DEFAULT_TERMINAL_HEIGHT",
]


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

NULL_DEVICE = _os.devnull if hasattr(_os, "devnull") else "/dev/null"

DEFAULT_TERMINAL_WIDTH = 80
DEFAULT_TERMINAL_HEIGHT = 24
ENV_COLUMNS = "COLUMNS"
ENV_LINES = "LINES"

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

log = logging.getLogger("grizzled.os")

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


def get_terminal_size(fd: int | None = None) -> tuple[int, int]:
    """
    Get the size of the terminal.

    :param fd: the file descriptor of the terminal (default is None, which uses
        the standard output)

    :return: A `(columns, rows)` tuple
    """

    def to_int(s: str, default: int, env_var: str) -> int:
        """
        Convert a string to an integer, falling back to a default value if the
        conversion fails or if the value is not positive.

        :param s: the string to convert
        :param default: the default value to return if conversion fails
        :param env_var: the name of the environment variable being converted
        :return: the converted integer or the default value
        """
        try:
            value = int(s)
            if value <= 0:
                raise ValueError("Value must be positive.")
            return value
        except (ValueError, TypeError):
            log.warning(
                f'Invalid value for environment variable "{env_var}": "{s}". '
                f"Using default value of {default}."
            )
            return default

    try:
        ts = (
            _os.get_terminal_size()
            if fd is None
            else _os.get_terminal_size(fd)
        )
        return (ts[0], ts[1])

    except OSError as e:
        log.warning(f"Could not determine current terminal size: {e}.")
        log.warning("Falling back to environment and/or default values.")
        match (_os.environ.get("COLUMNS"), _os.environ.get("LINES")):
            case (None, None):
                return DEFAULT_TERMINAL_WIDTH, DEFAULT_TERMINAL_HEIGHT
            case (None, s_height):
                return (
                    DEFAULT_TERMINAL_WIDTH,
                    to_int(s_height, DEFAULT_TERMINAL_HEIGHT, ENV_LINES),
                )
            case (s_width, None):
                return (
                    to_int(s_width, DEFAULT_TERMINAL_WIDTH, ENV_COLUMNS),
                    DEFAULT_TERMINAL_HEIGHT,
                )
            case (s_width, s_height):
                return (
                    to_int(s_width, DEFAULT_TERMINAL_WIDTH, ENV_COLUMNS),
                    to_int(s_height, DEFAULT_TERMINAL_HEIGHT, ENV_LINES),
                )


def find_command(
    command_name: str,
    path: str | Sequence[str] | Path | Sequence[Path] | None = None,
) -> Path | None:
    """
    Determine whether the specified system command exists in the specified
    path.

    :param command_name: the name of the command to find
    :param path: the path string or sequence of path elements to search,
        or None to use the system's default PATH environment variable
    :return: full path to the command, or `None` if not found
    """
    paths: list[Path]
    if path is not None:
        if type(path) is str and len(path) == 0:
            env = _os.environ
        else:
            paths = _map_paths(path)
            env = {"PATH": _os.pathsep.join(str(p) for p in paths)}
    else:
        env = _os.environ

    for directory in _os.get_exec_path(env=env):
        p = Path(directory) / command_name
        if p.exists() and p.is_file() and _os.access(p, _os.X_OK):
            return p

    return None


def spawnd(
    path: str, args: list[str] | tuple[str, ...], pidfile: str | None = None
) -> NoReturn:
    """
    Run a command as a daemon. This method is really just shorthand for the
    following code:

    ```python
    from grizzled.os import daemonize
    import os

    daemonize(pidfile=pidfile)
    os.execv(path, args)
    ```

    :param path: Full path to program to run
    :param args: List of command arguments. The first element in this list must
        be the command name (i.e., arg0).
    :param pidfile: Path to file to which to write daemon's process ID. The
        string may contain a `${pid}` token, which is replaced with the process
        ID of the daemon. e.g.: `"/var/run/myserver-${pid}"`
    """
    daemonize(no_close=True, pidfile=pidfile)
    _os.execv(path, args)


def daemonize(no_close: bool = False, pidfile: str | None = None) -> None:
    """
    Convert the calling process into a daemon. To make the current Python
    process into a daemon process, you need two lines of code:

    ```python
    from grizzled.os import daemonize
    daemonize()
    ```

    If `daemonize()` fails for any reason, it throws a `DaemonError`,
    which is a subclass of the standard `OSError` exception. also logs debug
    messages, using the standard Python `logging` package, to channel
    "grizzled.os.daemon".

    **See Also:**

    - Stevens, W. Richard. _Unix Network Programming_ (Addison-Wesley, 1990).

    :param no_close: If `True`, don't close the file descriptors. Useful if the
        calling process has already redirected file descriptors to an output
        file. **Warning**: Only set this parameter to `True` if you're sure
        there are no open file descriptors to the calling process.
    :param pidfile: Path to file to which to write daemon's process ID. The
        string may contain a `${pid}` token, which is replaced with the process
        ID of the daemon. e.g.: `"/var/run/myserver-${pid}"`
    :raises DaemonError: Error during daemonizing
    """
    log = logging.getLogger("grizzled.os.daemon")

    def _fork():
        try:
            return _os.fork()
        except OSError as e:
            raise DaemonError(("Cannot fork", e.errno, e.strerror)) from e

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
            except Exception:
                continue

            with suppress(OSError):
                _os.close(fd)

            # Redirect standard input, output and error to something safe.
            # os.open() is guaranteed to return the lowest available file
            # descriptor (0, or standard input). Then, we can dup that
            # descriptor for standard output and standard error.

            _os.open(NULL_DEVICE, _os.O_RDWR)
            _os.dup2(0, 1)
            _os.dup2(0, 2)

    if _os.name != "posix":
        raise DaemonError(
            (
                "daemonize() is only supported on Posix-compliant systems.",
                errno.ENOSYS,
                _os.strerror(errno.ENOSYS),
            )
        )

    try:
        # Fork once to go into the background.

        log.debug("Forking first child.")
        pid = _fork()
        if pid != 0:
            # Parent. Exit using os._exit(), which doesn't fire any atexit
            # functions.
            _os._exit(0)

        # First child. Create a new session. os.setsid() creates the session
        # and makes this (child) process the process group leader. The process
        # is guaranteed not to have a control terminal.
        log.debug("Creating new session")
        _os.setsid()

        # Fork a second child to ensure that the daemon never reacquires
        # a control terminal.
        log.debug("Forking second child.")
        pid = _fork()
        if pid != 0:
            # Original child. Exit.
            _os._exit(0)

        # This is the second child. Set the umask.
        log.debug("Setting umask")
        _os.umask(UMASK)

        # Go to a neutral corner (i.e., the primary file system, so
        # the daemon doesn't prevent some other file system from being
        # unmounted).
        log.debug(f'Changing working directory to "{WORKDIR}"')
        _os.chdir(WORKDIR)

        # Unless no_close was specified, close all file descriptors.
        if not no_close:
            log.debug("Redirecting file descriptors")
            _redirect_file_descriptors()

        if pidfile:
            from string import Template

            t = Template(pidfile)
            pidfile = t.safe_substitute(pid=str(_os.getpid()))
            with open(pidfile, "w") as f:
                f.write(str(_os.getpid()) + "\n")

    except DaemonError:
        raise

    except OSError as e:
        raise DaemonError(
            ("Unable to daemonize()", e.errno, e.strerror)
        ) from e
