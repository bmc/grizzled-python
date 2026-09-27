"""
This module contains file- and path-related methods, classes, and modules.
"""

__docformat__ = "markdown"

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

import os as _os
from collections.abc import Generator
from contextlib import chdir, suppress
from pathlib import Path
from typing import Sequence

# ---------------------------------------------------------------------------
# Exports
# ---------------------------------------------------------------------------

__all__ = [
    "unlink_quietly",
    "copy",
    "touch",
    "eglob",
    "universal_path",
    "native_path",
    "list_recursively",
]

# ---------------------------------------------------------------------------
# Functions
# ---------------------------------------------------------------------------


def unlink_quietly(
    *paths: str | Sequence[str] | Path | Sequence[Path],
) -> None:
    """
    Like the standard `os.unlink()` function, this function attempts to
    delete a file. However, it swallows any exceptions that occur during the
    unlink operation, making it more suitable for certain uses (e.g.,
    in `atexit` handlers).

    :param paths: path(s) to unlink
    """

    def looper(
        *paths: str | Sequence[str] | Path | Sequence[Path],
    ) -> Generator[Path]:
        for i in paths:
            if type(i) is str:
                yield Path(i)
            if type(i) is Path:
                yield i
            if isinstance(i, Sequence):
                for path in i:
                    yield Path(path) if not isinstance(path, Path) else path

    for path in looper(*paths):
        with suppress(OSError, FileNotFoundError):
            _os.unlink(path)


def list_recursively(
    dir: str | Path, *, include_files: bool = True, include_dirs: bool = True
) -> Generator[str]:
    """
    Recursively list the contents of a directory. Yields the contents of
    the directory and all subdirectories. This method returns a generator,
    so it evaluates its recursive walk lazily. This function is just a
    simple wrapper around `os.walk`.

    Each yielded value is a partial path, relative to the original directory.

    :param dir: path to the directory to list
    :param include_files: whether or not to include files in the listing
    :param include_dirs: whether or not to include directories in the listing
    :return: a generator of the partial paths of all directories and files
        below the specified directory
    :raises ValueError: if `dir` does not exist or is not a directory
    """
    dir = Path(dir) if not isinstance(dir, Path) else dir
    if not dir.is_dir():
        raise ValueError(f"{dir} is not a directory.")

    with chdir(dir):
        for dirpath, dirnames, filenames in _os.walk("."):
            if include_dirs:
                for d in dirnames:
                    yield _os.path.normpath(_os.path.join(dirpath, d))
            if include_files:
                for f in filenames:
                    yield _os.path.normpath(_os.path.join(dirpath, f))


def copy(
    files: Sequence[str] | str | Path | Sequence[Path],
    target_dir: str | Path,
    create_target: bool = False,
) -> None:
    """
    Copy one or more files to a target directory.

    :param files: path(s) to the file(s) to copy
    :param target_dir: path to the target directory
    :param create_target: whether or not to create the target directory if it
        does not exist
    :raises OSError: if `target_dir` does not exist and `create_target` is
        `False`
    :raises ValueError: if `target_dir` is not a directory
    """
    to_copy: list[Path] = _map_paths(files)
    if type(target_dir) is str:
        target_dir = Path(target_dir)

    assert isinstance(target_dir, Path)

    if target_dir.exists() and not target_dir.is_dir():
        raise ValueError(f"{target_dir} is not a directory.")

    if (not target_dir.exists()) and create_target:
        target_dir.mkdir()

    if target_dir.exists() and (not target_dir.is_dir()):
        raise OSError(f'Cannot copy files to non-directory "{target_dir}"')

    for f in to_copy:
        targetFile = target_dir / f.name
        with open(targetFile, "wb") as f_out, open(f, "rb") as f_in:
            f_out.write(f_in.read())


def touch(
    files: Sequence[str] | str | Path | Sequence[Path],
    *,
    times: tuple[int, int] | None = None,
    ns: tuple[int, int] | None = None,
) -> None:
    """
    Similar to the Unix *touch* command, this function:

    - updates the access and modification times for any existing files in a
      list of files
    - creates any non-existent files in the list of files

    `files` can be a single string or a sequence of strings.

    If any file in the list is a directory, this function will throw an
    exception.

    :param files: path(s) to the file(s) to touch
    :param times: a 2-tuple of the form `(atime, mtime)` expressing access and
        modification times in seconds
    :param ns: a 2-tuple of the form `(atime_ns, mtime_ns)` expressing access
        and modification times in nanoseconds
    :raises OSError: if any file in the list is a directory
    :raises ValueError: if both `times` and `ns` are specified
    """
    to_touch: list[Path] = _map_paths(files)

    if (times is not None) and (ns is not None):
        raise ValueError("Can't specify both ns and times.")

    for f in to_touch:
        if f.exists():
            if not f.is_file():
                raise OSError(f'Cannot touch non-file "{f}"')
            if ns:
                _os.utime(f, times=None, ns=ns)
            else:
                _os.utime(f, times)

        else:
            # Doesn't exist. Create it.
            open(f, "wb").close()


def eglob(pattern: str, directory: str = ".") -> Generator[str]:
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
    pieces = Path(pattern).parts
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
    if _os.name != "posix":
        path = path.replace(_os.path.sep, "/")

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
    if _os.name != "posix":
        path = path.replace("/", _os.path.sep)

    return path


def _map_paths(
    paths: str | Sequence[str] | Path | Sequence[Path],
) -> list[Path]:
    """Maps various path input types to a list of Path objects."""
    mapped: list[Path]
    if type(paths) is str:
        mapped = [Path(paths)]
    elif isinstance(paths, Path):
        mapped = [paths]
    else:
        mapped = []
        for f in paths:
            if isinstance(f, Path):
                mapped.append(f)
            else:
                mapped.append(Path(f))

    return mapped


def _find_matches(
    pattern_pieces: Sequence[str], directory: str
) -> Generator[str]:
    """
    Used by eglob.
    """
    import glob

    if not _os.path.isdir(directory):
        return

    piece = pattern_pieces[0]
    last = len(pattern_pieces) == 1
    remaining_pieces = []
    if piece == "**":
        if not last:
            remaining_pieces = pattern_pieces[1:]

        for root, _, _ in _os.walk(directory):
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
