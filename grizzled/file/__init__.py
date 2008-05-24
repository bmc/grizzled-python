# $Id$

"""
This module contains file- and path-related methods, classes, and modules.
"""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

from __future__ import with_statement, absolute_import

import os as _os
import sys
import shutil

from grizzled.decorators import deprecated
from grizzled.os import file_separator

# ---------------------------------------------------------------------------
# Exports
# ---------------------------------------------------------------------------

__all__ = ['unlink_quietly', 'recursively_remove', 'copy_recursively',
           'copy', 'touch', 'pathsplit', 'eglob', 'universal_path',
           'native_path']

# ---------------------------------------------------------------------------
# Functions
# ---------------------------------------------------------------------------

@deprecated(since='0.4', message='Use unlink_quietly')
def unlinkQuietly(*paths):
    return unlink_quietly(*paths)

def unlink_quietly(*paths):
    """
    Like the standard C{os.unlink()} function, this function attempts to
    delete a file. However, it swallows any exceptions that occur during the
    unlink operation, making it more suitable for certain uses (e.g.,
    in C{atexit} handlers).

    @type paths:  strings or lists of strings
    @param paths: path(s) to unlink
    """
    def looper(*paths):
        for i in paths:
            if type(i) == list:
                for path in i:
                    yield path
            else:
                yield i

    for path in looper(*paths):
        try:
            _os.unlink(path)
        except:
            pass

@deprecated(since='0.4', message='Use recursively_remove')
def recursivelyRemove(dir):
    recursively_remove(dir)

def recursively_remove(dir):
    """
    Recursively remove all files and directories below and including a specified
    directory.

    @type dir:  string
    @param dir: path to directory to remove
    """
    if not _os.path.exists(dir):
        return

    shutil.rmtree(dir)

@deprecated(since='0.4', message='Use copy_recursively')
def copyRecursively(dir):
    copy_recursively(dir)

def copy_recursively(source_dir, target_dir):
    """
    Recursively copy a source directory (and all its contents) to a target
    directory.

    @type source_dir:  str
    @param source_dir: Source directory to copy recursively. This path must
                       exist and must specify a directory; otherwise, this
                       function throws a C{ValueError}

    @type target_dir:  str
    @param target_dir: Directory to which to copy the contents of C{source_dir}.
                       This directory must not already exist.

    @raise ValueError: If: C{source_dir} does not exist; C{source_dir} exists
                       but is not a directory; or C{target_dir} exists but is
                       not a directory.
    """
    shutil.copytree(source_dir, target_dir)

def copy(files, target_dir, createTarget=False):
    """
    Copy one or more files to a target directory.

    @type files:  string or list
    @param files: a single file path or a list of file paths to be copied

    @type target_dir:  string
    @param target_dir: path to target directory

    @type createTarget:  boolean
    @param createTarget: If C{True}, C{copy()} will attempt to create the
                         target directory if it does not exist. If C{False},
                         C{copy()} will throw an exception if the target
                         directory does not exist.
    """
    if type(files) == str:
        files = [files]

    if not _os.path.exists(target_dir):
        if createTarget:
            _os.mkdir(target_dir)

    if _os.path.exists(target_dir) and (not _os.path.isdir(target_dir)):
        raise OSError, 'Cannot copy files to non-directory "%s"' % target_dir

    for f in files:
        targetFile = _os.path.join(target_dir, _os.path.basename(f))
        open(targetFile, 'wb').write(open(f, 'rb').read())

def touch(files, times=None):
    """
    Similar to the Unix I{touch}(1) command, this function:

     - updates the access and modification times for any existing files
       in a list of files
     - creates any non-existent files in the list of files

    If any file in the list is a directory, this function will throw an
    exception.

    @type files:  list or string
    @param files: pathname or list of pathnames of files to be created or
                  updated

    @type times:  tuple
    @param times: tuple of the form (I{atime}, I{mtime}), identical to
                  what is passed to the standard C{os.utime()} function.
                  If this tuple is C{None}, then the current time is used.
    """
    if type(files) == str:
        files = [files]

    for f in files:
        if _os.path.exists(f):
            if not _os.path.isfile(f):
                raise OSError, "Can't touch non-file \"%s\"" % f
            _os.utime(f, times)

        else:
            # Doesn't exist. Create it.
            open(f, 'wb').close()


def pathsplit(path):
    """
    Split a path into an array of path components, using the file separator
    ('/' on POSIX systems, '\' on Windows) that's appropriate for the
    underlying operating system. Does not take drive letters into account.
    If there's a Windows drive letter in the path, it'll end up with the
    first component.

    @type path:  str
    @param path: path to split. Can be relative or absolute.

    @rtype:  list
    @return: a list of path components
    """
    result = []
    (head, tail) = _os.path.split(path)

    if (not head) or (head == path):
        # No file separator. Done.
        pass

    else:
        result = pathsplit(head)

    if tail:
        result += [tail]

    return result

def __find_matches(pattern_pieces, directory):
    """
    Used by eglob.
    """
    import glob

    result = []
    if not _os.path.isdir(directory):
        return []

    piece = pattern_pieces[0]
    last = len(pattern_pieces) == 1
    if piece == '**':
        if not last:
            remaining_pieces = pattern_pieces[1:]

        for root, dirs, files in _os.walk(directory):
            if last:
                # At the end of a pattern, "**" just recursively matches
                # directories.
                result += [root]
            else:
                # Recurse downward, trying to match the rest of the
                # pattern.
                sub_result = __find_matches(remaining_pieces, root)
                for partial_path in sub_result:
                    result += [partial_path]

    else:
        # Regular glob pattern.

        matches = glob.glob(_os.path.join(directory, piece))
        if len(matches) > 0:
            if last:
                for match in matches:
                    result += [match]
            else:
                remaining_pieces = pattern_pieces[1:]
                for match in matches:
                    sub_result = __find_matches(remaining_pieces, match)
                    for partial_path in sub_result:
                        result += [partial_path]

    # Normalize the paths.

    for i in range(len(result)):
        result[i] = _os.path.normpath(result[i])

    return result

def eglob(pattern, directory='.'):
    """
    Extended glob function that supports the all the wildcards supported
    by the Python standard C{glob} routine, as well as a special "**"
    wildcard that recursively matches any directory. Examples::

        **/*.py    all files ending in '.py' under the current directory
        foo/**/bar all files name 'bar' anywhere under subdirectory 'foo'

    @type pattern:    str
    @param pattern:   The wildcard pattern. Must be a simple pattern with
                      no directories.

    @type directory:  str
    @param directory: The directory in which to do the globbing.

    @rtype:  list
    @return: A list of matched files, or an empty list for no match
    """
    pieces = pathsplit(pattern)
    return __find_matches(pieces, directory)

def universal_path(path):
    """
    Converts a path name from its operating system-specific format to a
    universal path notation. Universal path notation always uses a Unix-style
    "/" to separate path elements. A universal path can be converted to a
    native (operating system-specific) path via the
    L{C{native_path()}<native_path>} function. Note that on POSIX-compliant
    systems, this function simply returns C{path} argument unmodified.

    @type path:  str
    @param path: the path to convert to universal path notation

    @rtype:  str
    @return: the universal path.
    """
    if _os.name != 'posix':
        path = path.replace(file_separator(), '/')

    return path

def native_path(path):
    """
    Converts a path name from universal path notation to the operating
    system-specific format. Universal path notation always uses a Unix-style
    "/" to separate path elements. A native path can be converted to a
    universal path via the L{C{universal_path()}<universal_path>} function.
    Note that on POSIX-compliant systems, this function simply returns C{path}
    argument unmodified.

    @type path:  str
    @param path: the path to convert to native path notation

    @rtype:  str
    @return: the native path.
    """
    if _os.name != 'posix':
        path = path.replace('/', file_separator())

    return path
