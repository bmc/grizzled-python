# Nose program for testing (some) grizzled.file classes/functions

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

import os
import tempfile
from tempfile import TemporaryDirectory

from grizzled.file import list_recursively, unlink_quietly


def fix_path(p: str) -> str:
    """
    Fix a path to use the native path separator.

    :param p: The path to fix.
    :returns: The path with native separators.
    """
    return p.replace('/', os.path.sep)


def test_unlink_quietly() -> None:
    """Test that unlink_quietly removes a file without raising an exception."""
    fd, path = tempfile.mkstemp()
    os.unlink(path)

    try:
        os.unlink(path)
        raise AssertionError('Expected an exception')
    except OSError:
        pass

    unlink_quietly(path)

def test_list_recursively() -> None:
    """Test that list_recursively correctly lists all files and directories."""
    # Code below uses "/" as a path separator, but paths are coerced
    # to use the native path separator.

    with TemporaryDirectory() as path:
        for d in ('one', 'two', 'three', 'four/five'):
            os.makedirs(os.path.join(path, fix_path(d)))

        for f in ('one/foo.txt', 'two/bar.txt', 'four/hello.c',
                  'four/five/hello.py'):
            with open(os.path.join(path, fix_path(f)), 'w'):
                pass

        expected = set([fix_path(p) for p in (
            'three', 'one', 'two', 'four', 'one/foo.txt', 'two/bar.txt',
            'four/five', 'four/hello.c', 'four/five/hello.py'
        )])

        res = set(list_recursively(path))

        assert(res == expected)
