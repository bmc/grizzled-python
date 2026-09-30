import logging
import os
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from grizzled.file.includer import Includer, MaxNestingExceededError
from grizzled.text import strip_margin


@pytest.fixture
def log() -> logging.Logger:
    """Fixture that provides a logger for the tests.

    :returns: A logger instance named 'test'.
    """
    return logging.getLogger('test')


def test_simple(log: logging.Logger) -> None:
    """Test that a simple include works correctly."""
    outer = '''|First non-blank line.
               |Second non-blank line.
               |%include "inner.txt"
               |Last line.
               |'''
    inner = '''|Inner line 1
               |Inner line 2
               |'''
    expected = strip_margin(
        '''|First non-blank line.
           |Second non-blank line.
           |Inner line 1
           |Inner line 2
           |Last line.
           |'''
    )
    with TemporaryDirectory() as dir:
        outer_path = Path(dir) / "outer.txt"
        all = (
            (outer, outer_path),
            (inner, Path(dir) / "inner.txt"),
        )
        for text, path in all:
            log.debug(f'writing "{path}"')
            with open(path, mode='w', encoding='utf-8') as f:
                f.write(strip_margin(text))

        with outer_path.open(mode="r", encoding="utf-8") as f:
            inc = Includer(f)
            lines = [line for line in inc]
            res = ''.join(lines)
            assert res == expected

def test_nested(log: logging.Logger) -> None:
    """Test that nested includes work correctly."""
    outer = '''|First non-blank line.
               |Second non-blank line.
               |%include "nested1.txt"
               |Last line.
               |'''
    nested1 = '''|Nested 1 line 1
                 |%include "nested2.txt"
                 |Nested 1 line 3
                 |'''
    nested2 = '''|Nested 2 line 1
                 |Nested 2 line 2
                 |'''
    expected = strip_margin(
        '''|First non-blank line.
           |Second non-blank line.
           |Nested 1 line 1
           |Nested 2 line 1
           |Nested 2 line 2
           |Nested 1 line 3
           |Last line.
           |'''
    )
    with TemporaryDirectory() as dir:
        outer_path = os.path.join(dir, "outer.txt")
        all = (
            (outer, outer_path),
            (nested1, os.path.join(dir, "nested1.txt")),
            (nested2, os.path.join(dir, "nested2.txt")),
        )
        for text, path in all:
            with open(path, mode='w', encoding='utf-8') as f:
                f.write(strip_margin(text))

        with Path(outer_path).open(mode="r", encoding="utf-8") as f:
            inc = Includer(f)
            lines = [line for line in inc]
            res = ''.join(lines)
            assert res == expected

def test_overflow(log: logging.Logger) -> None:
    """Test that exceeding the maximum nesting level raises an exception."""
    outer = '''|First non-blank line.
               |Second non-blank line.
               |%include "outer.txt"
               |Last line.
               |'''
    with TemporaryDirectory() as dir:
        outer_path = os.path.join(dir, "outer.txt")
        with open(outer_path, mode='w', encoding='utf-8') as f:
            f.write(strip_margin(outer))

        try:
            with Path(outer_path).open(mode="r", encoding="utf-8") as f:
                Includer(f, max_nest_level=10)
            raise AssertionError("Expected max-nesting exception")
        except MaxNestingExceededError as e:
            print(e)


def _expand_nested(
    before_include: str | None, after_include: str | None
) -> str:
    """Expand a two-level nested include with the given markers.

    :param before_include: Text to insert before each included file.
    :param after_include: Text to insert after each included file.
    :returns: The fully expanded text.
    """
    outer = '''|Outer line 1
               |%include "nested1.txt"
               |Outer line 3
               |'''
    nested1 = '''|Nested 1 line 1
                 |%include "nested2.txt"
                 |Nested 1 line 3
                 |'''
    nested2 = '''|Nested 2 line 1
                 |'''
    with TemporaryDirectory() as dir:
        outer_path = Path(dir) / "outer.txt"
        all = (
            (outer, outer_path),
            (nested1, Path(dir) / "nested1.txt"),
            (nested2, Path(dir) / "nested2.txt"),
        )
        for text, path in all:
            with open(path, mode='w', encoding='utf-8') as f:
                f.write(strip_margin(text))

        with outer_path.open(mode="r", encoding="utf-8") as f:
            inc = Includer(
                f,
                before_include=before_include,
                after_include=after_include,
            )
            return inc.read()


def test_before_and_after_include(log: logging.Logger) -> None:
    """Test that both markers surround each (nested) included file."""
    expected = strip_margin(
        '''|Outer line 1
           |BEGIN
           |Nested 1 line 1
           |BEGIN
           |Nested 2 line 1
           |END
           |Nested 1 line 3
           |END
           |Outer line 3
           |'''
    )
    assert _expand_nested("BEGIN\n", "END\n") == expected


def test_before_include_only(log: logging.Logger) -> None:
    """Test that only the "before" marker is inserted."""
    expected = strip_margin(
        '''|Outer line 1
           |BEGIN
           |Nested 1 line 1
           |BEGIN
           |Nested 2 line 1
           |Nested 1 line 3
           |Outer line 3
           |'''
    )
    assert _expand_nested("BEGIN\n", None) == expected


def test_after_include_only(log: logging.Logger) -> None:
    """Test that only the "after" marker is inserted."""
    expected = strip_margin(
        '''|Outer line 1
           |Nested 1 line 1
           |Nested 2 line 1
           |END
           |Nested 1 line 3
           |END
           |Outer line 3
           |'''
    )
    assert _expand_nested(None, "END\n") == expected
