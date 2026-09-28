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


def universal_path(path: str) -> str:
    """
    Converts a path name from its operating system-specific format to a
    universal path notation. Universal path notation always uses a Unix-style
    "/" to separate path elements. A universal path can be converted to a
    native (operating system-specific) path via the `native_path()`
    function. Note that on POSIX-compliant systems, this function simply
    returns the `path` parameter unmodified.

    :param path: The path to convert to universal path notation.
    :return: The path in universal path notation.
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

    :param path: The universal path to convert to native path notation.
    :return: The path in native path notation.
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

