# Nose program for testing (some) grizzled.file classes/functions

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

import os
import tempfile
from contextlib import chdir
from tempfile import TemporaryDirectory

from grizzled.file import eglob, list_recursively, touch, unlink_quietly


def fix_path(p: str) -> str:
    return p.replace('/', os.path.sep)


def test_unlink_quietly():
    fd, path = tempfile.mkstemp()
    os.unlink(path)

    try:
        os.unlink(path)
        raise AssertionError('Expected an exception')
    except OSError:
        pass

    unlink_quietly(path)

def test_list_recursively():
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

def test_touch():
    with TemporaryDirectory() as path:
        f = os.path.join(path, 'foo')
        assert not os.path.exists(f)
        touch(f)
        assert os.path.exists(f)

def test_eglob():
    with TemporaryDirectory() as path:
        for d in ('one', 'two', 'three', 'four/five', 'six/seven/eight'):
            os.makedirs(os.path.join(path, fix_path(d)))
        for f in ('one/foo.py', 'one/foo.txt', 'two/bar.c',
                  'four/test.py', 'four/test2.py', 'four/me.txt',
                  'four/five/x.py', 'six/seven/test.py'):
            with open(os.path.join(path, fix_path(f)), 'w'):
                pass

        with chdir(path):
            expected = {
                'one/foo.py', 'four/test.py', 'four/test2.py',
                'four/five/x.py', 'six/seven/test.py'
            }
            res = set(eglob('**/*.py'))
            assert(res == expected)
