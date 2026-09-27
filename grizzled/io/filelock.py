"""
This module provides portable advisory file locking primitives that operate on
file descriptors. POSIX-like systems and Windows systems use different
primitives to perform file locking, and these different primitives are modeled
by incompatible (and different) modules in the Python standard library. This
module provides an abstract `FileLock` class, and underlying
implementations, to hide the operating system dependencies behind a simple
portable interface.

To create a file lock, simply instantiate the `FileLock` class with an open
file descriptor. It handles the rest:

```python
from grizzled.io.filelock import FileLock

fd = open('/tmp/lockfile', 'r+')
lock = FileLock(fd)
lock.acquire()

...

lock.release()
```

You can also use the `locked_file()` context manager to simplify your code:

```python
from grizzled.io.filelock import locked_file

fd = open('/tmp/lockfile', 'r+')
with locked_file(fd):
    pass

# Automatically unlocked once you get here
```
"""

__docformat__ = "markdown"

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

import fcntl
from contextlib import contextmanager
from typing import Generator, Self

# ---------------------------------------------------------------------------
# Exports
# ---------------------------------------------------------------------------

__all__ = ["FileLock", "locked_file"]

# ---------------------------------------------------------------------------
# Classes
# ---------------------------------------------------------------------------


class FileLock:
    """
    A `FileLock` object models a file lock. It wraps a file descriptor
    and contains methods to acquire and release a lock on the file.

    File lock implementations that implement this interface are guaranteed
    to be advisory, but not mandatory, file locks. (They may, in fact, also
    be mandatory file locks, but they are not guaranteed to be.)

    Currently, this implementation only supports POSIX-compliant systems.
    """

    def __init__(self: Self, fd: int) -> None:
        """
        Allocate a new file lock that operates on the specified file
        descriptor.

        :param fd: Open file descriptor. The file must be opened for writing or
            updating, not reading.
        :raises OSError: If the underlying platform does not support file
            locking.
        """
        self._fd = fd

    def acquire(self: Self, no_wait: bool = False) -> None:
        """
        Lock the associated file. If someone already has the file locked, this
        method will suspend the calling process, unless `no_wait` is `True`.

        :param no_wait: If `False`, then `acquire()` will suspend the calling
            process if someone has the file locked. If `True`, then `acquire()`
            will raise an `IOError` if the file is locked by someone else.
        :raises IOError: If the file cannot be locked for any reason.
        """
        flags = fcntl.LOCK_EX
        if no_wait:
            flags |= fcntl.LOCK_NB

        fcntl.lockf(self._fd, flags)

    def release(self: Self) -> None:
        """
        Unlock (i.e., release the lock on) the associated file.
        """
        fcntl.lockf(self._fd, fcntl.LOCK_UN)


# ---------------------------------------------------------------------------
# Functions
# ---------------------------------------------------------------------------


@contextmanager
def locked_file(fd: int, no_wait: bool = False) -> Generator[FileLock]:
    """
    This function is intended to be used as a `with` statement context
    manager. It wraps a `FileLock` object so that the locking and unlocking
    of the file descriptor are automatic. With the `locked_file()` function,
    you can replace this code:

    ```python
    from grizzled.io.filelock import FileLock

    lock = FileLock(fd)
    lock.acquire()
    try:
        do_something()
    finally:
        lock.release()
    ```

    with this code:

    ```python
    from grizzled.io.filelock import locked_file

    with locked_file(fd):
        do_something()
    ```

    :param fd: Open file descriptor.
    :param no_wait: If `False`, then `locked_file()` will suspend the calling
        process if someone has the file locked. If `True`, then `locked_file()`
        will raise an `IOError` if the file is already locked by someone else.
    """
    locked = False
    lock = None
    try:
        lock = FileLock(fd)
        lock.acquire(no_wait)
        locked = True
        yield lock
    finally:
        if locked and lock:
            lock.release()
