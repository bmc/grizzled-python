# Nose program for testing grizzled.io Zip class

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

from grizzled.io import Zip
from grizzled.os import working_directory
import os
from tempfile import TemporaryDirectory
import shutil

# ---------------------------------------------------------------------------
# Classes
# ---------------------------------------------------------------------------

class TestZip(object):

    def testZip(self):
        from grizzled.file import list_recursively

        with TemporaryDirectory() as path:
            subdir_name = 'foo'
            subdir = os.path.join(path, subdir_name)
            os.makedirs(subdir)
            for d in ('one', 'two', 'three', 'four/five', 'six/seven/eight'):
                os.makedirs(os.path.join(subdir, self.fix_path(d)))
            for f in ('one/foo.py', 'one/foo.txt', 'two/bar.c',
                      'four/test.py', 'four/test2.py', 'four/me.txt',
                      'four/five/x.py', 'six/seven/test.py'):
                with open(os.path.join(subdir, self.fix_path(f)), 'w') as f:
                    f.write("lkajsdflkjasdf\n")

            source_files = set(list_recursively(subdir, include_dirs=False))
            with working_directory(subdir):
                shutil.make_archive(os.path.join(path, 'foo'), 'zip')

            # Source and unpacked won't match, because empty directories
            # aren't zipped. So, just check the files.
            unpack_dir = 'bar'
            with working_directory(path):
                z = Zip('foo.zip')
                z.extract_into(unpack_dir)
                unpacked_files = set(list_recursively(unpack_dir,
                                                      include_dirs=False))

            assert(source_files == unpacked_files)


    def fix_path(self, p: str) -> str:
        return p.replace('/', os.path.sep)
