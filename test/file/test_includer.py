import codecs
import logging
import os
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from grizzled.file.includer import Includer, MaxNestingExceededError
from grizzled.text import strip_margin


@pytest.fixture
def log():
    return logging.getLogger('test')


def test_simple(log):
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
            with codecs.open(path, mode='w', encoding='utf-8') as f:
                f.write(strip_margin(text))

        with outer_path.open(mode="r", encoding="utf-8") as f:
            inc = Includer(f)
            lines = [line for    line in inc]
            res = ''.join(lines)
            assert res == expected

def test_nested(log):
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
            with codecs.open(path, mode='w', encoding='utf-8') as f:
                f.write(strip_margin(text))

        with Path(outer_path).open(mode="r", encoding="utf-8") as f:
            inc = Includer(f)
            lines = [line for line in inc]
            res = ''.join(lines)
            assert res == expected

def test_overflow(log):
    outer = '''|First non-blank line.
               |Second non-blank line.
               |%include "outer.txt"
               |Last line.
               |'''
    with TemporaryDirectory() as dir:
        outer_path = os.path.join(dir, "outer.txt")
        with codecs.open(outer_path, mode='w', encoding='utf-8') as f:
            f.write(strip_margin(outer))

        try:
            with Path(outer_path).open(mode="r", encoding="utf-8") as f:
                Includer(f, max_nest_level=10)
            raise AssertionError("Expected max-nesting exception")
        except MaxNestingExceededError as e:
            print(e)
