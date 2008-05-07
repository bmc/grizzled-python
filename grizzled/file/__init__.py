# $Id$

"""
This module contains file- and path-related methods, classes, and modules.
"""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

from __future__ import with_statement, absolute_import

import os
import sys
import shutil

# ---------------------------------------------------------------------------
# Functions
# ---------------------------------------------------------------------------

def unlinkQuietly(*paths):
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
            os.unlink(path)
        except:
            pass

def recursivelyRemove(dir):
    """
    Recursively remove all files and directories below and including a specified
    directory.

    @type dir:  string
    @param dir: path to directory to remove
    """
    if not os.path.exists(dir):
        return

    shutil.rmtree(dir)

def copyRecursively(sourceDir, targetDir):
    """
    Recursively copy a source directory (and all its contents) to a target
    directory.

    @type sourceDir:  str
    @param sourceDir: Source directory to copy recursively. This path must
                      exist and must specify a directory; otherwise, this
                      function throws a C{ValueError}

    @type targetDir:  str
    @param targetDir: Directory to which to copy the contents of C{sourceDir}.
                      This directory must not already exist.

    @raise ValueError: If: C{sourceDir} does not exist; C{sourceDir} exists
                       but is not a directory; or C{targetDir} exists but is
                       not a directory.
    """
    shutil.copytree(sourceDir, targetDir)

def copy(files, targetDir, createTarget=False):
    """
    Copy one or more files to a target directory.

    @type files:  string or list
    @param files: a single file path or a list of file paths to be copied

    @type targetDir:  string
    @param targetDir: path to target directory

    @type createTarget:  boolean
    @param createTarget: If C{True}, C{copy()} will attempt to create the
                         target directory if it does not exist. If C{False},
                         C{copy()} will throw an exception if the target
                         directory does not exist.
    """
    if type(files) == str:
        files = [files]

    if not os.path.exists(targetDir):
        if createTarget:
            os.mkdir(targetDir)

    if os.path.exists(targetDir) and (not os.path.isdir(targetDir)):
        raise OSError, 'Cannot copy files to non-directory "%s"' % targetDir

    for f in files:
        targetFile = os.path.join(targetDir, os.path.basename(f))
        o = open(targetFile, 'wb')
        i = open(f, 'rb')

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
        if os.path.exists(f):
            if not os.path.isfile(f):
                raise OSError, "Can't touch non-file \"%s\"" % f
            os.utime(f, times)

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
    (head, tail) = os.path.split(path)

    if (not head) or (head == path):
        # No file separator. Done.
        pass

    else:
        result = pathsplit(head)
        
    if tail:
        result += [tail]

    return result

def __findMatches(patternPieces, directory):
    """
    Used by eglob.
    """
    import glob

    result = []
    if not os.path.isdir(directory):
        return []

    last = len(patternPieces) == 1
    piece = patternPieces[0]
    if piece == '**':
        if not last:
            remainingPieces = patternPieces[1:]

        for root, dirs, files in os.walk(directory):
            if last:
                # At the end of a pattern, "**" just recursively matches
                # directories.
                result += [root]
            else:
                # Recurse downward, trying to match the rest of the
                # pattern.
                subResult = __findMatches(remainingPieces, root)
                for partialPath in subResult:
                    result += [partialPath]

    else:
        # Regular glob pattern.

        matches = glob.glob(os.path.join(directory, piece))
        if len(matches) > 0:
            if last:
                for match in matches:
                    result += [match]
            else:
                remainingPieces = patternPieces[1:]
                for match in matches:
                    subResult = __findMatches(remainingPieces, match)
                    for partialPath in subResult:
                        result += [partialPath]

    # Normalize the paths.

    for i in range(len(result)):
        result[i] = os.path.normpath(result[i])

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
    return __findMatches(pieces, directory)
