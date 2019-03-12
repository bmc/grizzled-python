
from grizzled.file import eglob, touch
import os
from os import path
from tempfile import TemporaryDirectory
from contextlib import contextmanager
import pytest

from typing import Sequence, Set, Generator

class Files(object):
    def __init__(self,
                 tempdir: str,
                 files: [str],
                 dirs: Sequence[str],
                 py_files: Set[str],
                 txt_files: Set[str],
                 top_level_files: Set[str],
                 readmes: Set[str]):
        self.tempdir = tempdir
        self.files = files
        self.dirs = dirs
        self.py_files = py_files
        self.txt_files = txt_files
        self.top_level_files = top_level_files
        self.readmes = readmes

@pytest.fixture
def tempfiles() -> Generator[Files, None, None]:
    with TemporaryDirectory() as tempdir:
        foo = path.join(tempdir, "foo")
        bar = path.join(tempdir, "bar")
        baz = path.join(tempdir, "baz")
        quux = path.join(tempdir, "quux")
        foo_sub = path.join(foo, "foosub1")
        bar_sub = path.join(bar, "barsub1")
        foo_sub_sub = path.join(foo_sub, "hellothere")

        dirs = (foo, bar, baz, quux, foo_sub, bar_sub, foo_sub_sub)
        files = (
            path.join(foo, "file1.py"),
            path.join(bar, "file2.py"),
            path.join(foo_sub, "file3.py"),
            path.join(foo_sub_sub, "file4.py"),
            path.join(quux, "readme.txt"),
            path.join(baz, "license.txt"),
            path.join(foo_sub_sub, "readme.txt"),
            path.join(bar_sub, "changelog.md"),
            path.join(tempdir, "foo.py"),
            path.join(tempdir, "bar.py"),
            path.join(tempdir, "readme"),
            path.join(tempdir, "license.txt"),
        )

        py_files = { f for f in files if f.endswith(".py") }
        readmes = { f for f in files if f.endswith("readme.txt") }
        txt_files = { f for f in files if f.endswith(".txt") }
        top_level_files = {
            f for f in files if path.dirname(f) == tempdir
        }

        for d in dirs:
            os.makedirs(d)

        for f in files:
            touch(f)

        yield Files(tempdir=tempdir,
                    files=files,
                    dirs=dirs,
                    py_files=py_files,
                    readmes=readmes,
                    txt_files=txt_files,
                    top_level_files=top_level_files)


def test_readme(tempfiles):
    files = set(eglob("**/readme.txt", tempfiles.tempdir))
    assert files == tempfiles.readmes

def test_py_files(tempfiles):
    files = set(eglob("**/*.py", tempfiles.tempdir))
    assert files == tempfiles.py_files

def test_text_files(tempfiles):
    files = set(eglob("**/*.txt", tempfiles.tempdir))
    assert files == tempfiles.txt_files

def test_top_level_files(tempfiles):
    top = set(eglob("*", tempfiles.tempdir))
    files = { f for f in top if os.path.isfile(f) }
    assert files == tempfiles.top_level_files

