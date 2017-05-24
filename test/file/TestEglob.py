
from grizzled.file import eglob, touch
import os
from os import path
from backports.tempfile import TemporaryDirectory

class TestEglob(object):

    def __init__(self):
        self.files = None
        self.dirs = None
        self.tempdir = None

    def setup(self):
        self.tempdir = TemporaryDirectory()
        tempname = self.tempdir.name
        foo = path.join(tempname, "foo")
        bar = path.join(tempname, "bar")
        baz = path.join(tempname, "baz")
        quux = path.join(tempname, "quux")
        foo_sub = path.join(foo, "foosub1")
        bar_sub = path.join(bar, "barsub1")
        foo_sub_sub = path.join(foo_sub, "hellothere")

        self.dirs = (foo, bar, baz, quux, foo_sub, bar_sub, foo_sub_sub)
        self.files = (
            path.join(foo, "file1.py"),
            path.join(bar, "file2.py"),
            path.join(foo_sub, "file3.py"),
            path.join(foo_sub_sub, "file4.py"),
            path.join(quux, "readme.txt"),
            path.join(baz, "license.txt"),
            path.join(foo_sub_sub, "readme.txt"),
            path.join(bar_sub, "changelog.md"),
            path.join(tempname, "foo.py"),
            path.join(tempname, "bar.py"),
            path.join(tempname, "readme"),
            path.join(tempname, "license.txt"),
        )

        self.py_files = { f for f in self.files if f.endswith(".py") }
        self.readmes = { f for f in self.files if f.endswith("readme.txt") }
        self.txt_files = { f for f in self.files if f.endswith(".txt") }
        self.top_level_files = {
            f for f in self.files if path.dirname(f) == tempname
        }

        for d in self.dirs:
            os.makedirs(d)

        for f in self.files:
            touch(f)

    def teardown(self):
        self.tempdir.cleanup()

    def testReadMes(self):
        files = set(eglob("**/readme.txt", self.tempdir.name))
        assert files == self.readmes

    def testPyFiles(self):
        files = set(eglob("**/*.py", self.tempdir.name))
        assert files == self.py_files

    def testTextFiles(self):
        files = set(eglob("**/*.txt", self.tempdir.name))
        assert files == self.txt_files

    def testTopLevelFiles(self):
        top = set(eglob("*", self.tempdir.name))
        files = { f for f in top if os.path.isfile(f) }
        assert files == self.top_level_files

