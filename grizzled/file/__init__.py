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


def eglob(pattern, directory='.', recursive=False):
    """
    Extended glob function that supports both a recursive and a non-recursive
    mode. In non-recursive mode (C{recursive=False}), this function behaves
    exactly like the standard C{glob} function. In recursive mode
    (C{recursive=True}), this function finds all matches for a file name
    pattern in every directory below the specified directory (including the
    specified directory).
    
    @type pattern:    str
    @param pattern:   The wildcard pattern. Must be a simple pattern with
                      no directories.
                    
    @type directory:  str
    @param directory: The directory in which to do the globbing.
    
    @type recursive:  boolean
    @param recursive: C{True} to do a recursive search, C{False} to do a local
                      search
                      
    @rtype:  list
    @return: A list of matched files, or an empty list for no match
    """
    import fnmatch
    import glob
    from grizzled.os import workingDirectory

    result = []
    with workingDirectory(directory):
        if not recursive:
            for f in glob.glob(pattern):
                if os.path.isabs(f):
                    result += [f]
                else:
                    result += [os.path.join(directory, f)]

        else:
            for root, dirs, files in os.walk(directory):
                for f in files:
                    if fnmatch.fnmatch(f, pattern):
                        result += [os.path.join(root, f)]

                for d in dirs:
                    result += eglob(pattern,
                                    os.path.join(root, d),
                                    recursive=recursive)

    return result
