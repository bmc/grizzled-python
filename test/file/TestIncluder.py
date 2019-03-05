import os
from tempfile import TemporaryDirectory
import codecs
import logging
from grizzled.file.includer import *
from grizzled.os import working_directory

def _stripmargin(s: str, margin: str = '|'):
    """Similar to Scala's StringOps.stripmargin() function."""
    res = []
    for line in s.split('\n'):
        line = line.lstrip()
        if len(line) == 0:
            # Be forgiving: Empty line, with no margin char.
            res.append("")
            continue

        if line[0] != margin:
            # Be forgiving: No margin char.
            res.append(line)
            continue

        res.append(line[1:])

    return '\n'.join(res)

class TestIncluder(object):
    def __init__(self):
        pass

    def setup(self):
        self.log = logging.getLogger('test')

    def test_simple(self):
        outer = '''|First non-blank line.
                   |Second non-blank line.
                   |%include "inner.txt"
                   |Last line.
                   |'''
        inner = '''|Inner line 1
                   |Inner line 2
                   |'''
        expected = _stripmargin(
            '''|First non-blank line.
               |Second non-blank line.
               |Inner line 1
               |Inner line 2
               |Last line.
               |'''
        )
        with TemporaryDirectory() as dir:
            outer_path = os.path.join(dir, "outer.txt")
            all = (
                (outer, outer_path),
                (inner, os.path.join(dir, "inner.txt")),
            )
            for text, path in all:
                self.log.debug(f'writing "{path}"')
                with codecs.open(path, mode='w', encoding='utf-8') as f:
                    f.write(_stripmargin(text))

            inc = Includer(outer_path)
            lines = [line for line in inc]
            res = ''.join(lines)
            self._log_text_file('res', res)
            self._log_text_file('expected', expected)
            assert res == expected

    def test_nested(self):
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
        expected = _stripmargin(
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
                    f.write(_stripmargin(text))

            inc = Includer(outer_path)
            lines = [line for line in inc]
            res = ''.join(lines)
            self._log_text_file('res', res)
            self._log_text_file('expected', expected)
            assert res == expected

    def test_overflow(self):
        outer = '''|First non-blank line.
                   |Second non-blank line.
                   |%include "outer.txt"
                   |Last line.
                   |'''
        with TemporaryDirectory() as dir:
            outer_path = os.path.join(dir, "outer.txt")
            with codecs.open(outer_path, mode='w', encoding='utf-8') as f:
                f.write(_stripmargin(outer))

            try:
                Includer(outer_path, max_nest_level=10)
                assert False, "Expected max-nesting exception"
            except MaxNestingExceededError as e:
                print(e)

    def _log_text_file(self, prefix: str, text: str) -> None:
        self.log.debug(f'{prefix}:\n---\n{text}\n---')

if __name__ == '__main__':
    TestIncluder().test_simple()
