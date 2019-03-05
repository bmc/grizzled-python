"""
This module contains file- and path-related methods, classes, and modules.
"""

__docformat__ = "markdown"

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

import os as _os
import shutil
from typing import (Sequence, Mapping, Any, Optional, Union, NoReturn,
                    Generator, Tuple)

# ---------------------------------------------------------------------------
# Exports
# ---------------------------------------------------------------------------

__all__ = ['unlink_quietly', 'recursively_remove', 'copy', 'touch',
           'pathsplit', 'eglob', 'universal_path', 'native_path',
           'list_recursively', 'includer']

# ---------------------------------------------------------------------------
# Functions
# ---------------------------------------------------------------------------

def unlink_quietly(*paths: Union[str, Sequence[str]]) -> NoReturn:
    """
    Like the standard `os.unlink()` function, this function attempts to
    delete a file. However, it swallows any exceptions that occur during the
    unlink operation, making it more suitable for certain uses (e.g.,
    in `atexit` handlers).

    **Parameters**

    - `paths` (`str` or sequence of `str`): path(s) to unlink
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

def recursively_remove(dir: str) -> NoReturn:
    """
    Recursively remove all files and directories below and including a
    specified directory.

    **Parameters**

    - `dir` (`str`): path to directory to remove
    """
    if not _os.path.exists(dir):
        return

    shutil.rmtree(dir)


def list_recursively(dir: str, *,
                     include_files: bool = True,
                     include_dirs: bool = True) -> Generator[None, str, None]:
    """
    Recursively list the contents of a directory. Yields the contents of
    the directory and all subdirectories. This method returns a generator,
    so it evaluates its recursive walk lazily. This function is just a
    simple wrapper around `os.walk`.

    Each yielded value is a partial path, relative to the original directory.

    **Parameters**

    - `dir` (`str`): Path to directory to list
    - `include_files` (`bool`): Whether or not to yield directories. `True`
      by default.
    - `include_dirs` (`bool`): Whether or not to yield files. `True` by
      default.

    **Yields**

    partial paths of all directories and/or files below the specified directory

    **Raises**

    `ValueError`: If `dir` does not exist, or if `dir` exists but is not a
                  directory.
    """
    if not _os.path.isdir(dir):
        raise ValueError("{0} is not a directory.".format(dir))

    from grizzled.os import working_directory

    with working_directory(dir):
        for dirpath, dirnames, filenames in _os.walk('.'):
            if include_dirs:
                for d in dirnames:
                    yield _os.path.normpath(_os.path.join(dirpath, d))
            if include_files:
                for f in filenames:
                    yield _os.path.normpath(_os.path.join(dirpath, f))


def copy(files : Union[Sequence[str], str],
         target_dir : str,
         create_target : bool = False) -> None:
    """
    Copy one or more files to a target directory.

    **Parameters**

    - `files` (`str` or `list` of `str`): a string representing a single path,
      or a list of strings representing multiple paths, to be copied
    - `target_dir` (`str`): path to the target directory
    - `create_target` (`bool`): whether or not to create the target

    **Returns** Nothing

    **Raises**

    - `OSError`: `target_dir` does not exist and `create_target` is `False`.
    """
    if type(files) == str:
        files = [files]

    if not _os.path.exists(target_dir):
        if create_target:
            _os.mkdir(target_dir)

    if _os.path.exists(target_dir) and (not _os.path.isdir(target_dir)):
        raise OSError(
	    'Cannot copy files to non-directory "{0}"'.format(target_dir)
	)

    for f in files:
        targetFile = _os.path.join(target_dir, _os.path.basename(f))
        open(targetFile, 'wb').write(open(f, 'rb').read())

def touch(files: Union[str, Sequence[str]], *,
          times: Optional[Tuple[int, int]] = None,
          ns: Optional[Tuple[int, int]] = None) -> NoReturn:
    """
    Similar to the Unix *touch* command, this function:

    - updates the access and modification times for any existing files
      in a list of files
    - creates any non-existent files in the list of files

    `files` can be a single string or a sequence of strings.

    If any file in the list is a directory, this function will throw an
    exception.

    - If `ns` is not `None`, it must be a 2-tuple of the form
     `(atime_ns, mtime_ns)` where each member is an `int` expressing
     nanoseconds.
    - If `times` is not `None`, it must be a 2-tuple of the form
      `(atime, mtime)` where each member is an `int` or `float` expressing
      seconds.
    - If `times` is `None` and `ns` is `None`, this is equivalent to
      specifying `ns=(atime_ns, mtime_ns)` where both times are the current
      time.
    - If both are specified, `ValueError` is raised.
    """
    if type(files) == str:
        files = [files]

    if (times is not None) and (ns is not None):
        raise ValueError("Can't specify both ns and times.")

    for f in files:
        if _os.path.exists(f):
            if not _os.path.isfile(f):
                raise OSError('Cannot touch non-file "{0}"'.format(f))
            if ns:
                _os.utime(f, times=None, ns=ns)
            else:
                _os.utime(f, times)

        else:
            # Doesn't exist. Create it.
            open(f, 'wb').close()


def pathsplit(path: str) -> Sequence[str]:
    """
    Split a path into an array of path components, using the file separator
    (e.g., '/' on POSIX systems) that's appropriate for the underlying operating
    system. Does not take drive letters into account. If there's a Windows
    drive letter in the path, it'll end up with the first component.

    **Parameters**

    - `path` (`str`): path to split. Can be relative or absolute

    **Returns**

    a list of path components
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

def _find_matches(pattern_pieces: Sequence[str],
                  directory: str) -> Generator[str, str, None]:
    """
    Used by eglob.
    """
    import glob

    if not _os.path.isdir(directory):
        return

    piece = pattern_pieces[0]
    last = len(pattern_pieces) == 1
    remaining_pieces = []
    if piece == '**':
        if not last:
            remaining_pieces = pattern_pieces[1:]

        for root, dirs, files in _os.walk(directory):
            if last:
                # At the end of a pattern, "**" just recursively matches
                # directories.
                yield _os.path.normpath(root)
            else:
                # Recurse downward, trying to match the rest of the
                # pattern.
                sub_result = _find_matches(remaining_pieces, root)
                for partial_path in sub_result:
                    yield _os.path.normpath(partial_path)

    else:
        # Regular glob pattern.

        matches = glob.glob(_os.path.join(directory, piece))
        if len(matches) > 0:
            if last:
                for match in matches:
                    yield _os.path.normpath(match)
            else:
                remaining_pieces = pattern_pieces[1:]
                for match in matches:
                    sub_result = _find_matches(remaining_pieces, match)
                    for partial_path in sub_result:
                        yield _os.path.normpath(partial_path)

def eglob(pattern: str, directory: str = '.') -> Generator[str, str, None]:
    """
    Extended glob function that supports the all the wildcards supported
    by the Python standard `glob` routine, as well as a special `**`
    wildcard that recursively matches any directory.

    **Parameters**

    - `pattern` (`str`): The wildcard pattern.
    - `directory` (`str`): The directory in which to do the globbing. Defaults
      to `.`

    **Yields**

    The matched paths.
    """
    pieces = pathsplit(pattern)
    return _find_matches(pieces, directory)

def universal_path(path: str) -> str:
    """
    Converts a path name from its operating system-specific format to a
    universal path notation. Universal path notation always uses a Unix-style
    "/" to separate path elements. A universal path can be converted to a
    native (operating system-specific) path via the `native_path()`
    function. Note that on POSIX-compliant systems, this function simply
    returns the `path` parameter unmodified.

    **Parameters**

    - `path` (`str`): the path to convert to universal path notation

    **Returns**

    The path in universal path notation.
    """
    if _os.name != 'posix':
        path = path.replace(_os.path.sep, '/')

    return path

def native_path(path: str) -> str:
    """
    Converts a path name from universal path notation to the operating
    system-specific format. Universal path notation always uses a Unix-style
    "/" to separate path elements. A native path can be converted to a
    universal path via the `universal_path()` function. Note that on
    POSIX-compliant systems, this function simply returns the `path`
    parameter unmodified.

    **Parameters**

    - `path` (`str`): the universal path to convert to native path notation

    **Returns**

    The path in native path notation.
    """
    if _os.name != 'posix':
        path = path.replace('/', _os.path.sep)

    return path
