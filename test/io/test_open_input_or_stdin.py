# Test program for the grizzled.io.open_input_or_stdin function

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

import re
from io import StringIO
from pathlib import Path
from typing import Self

import pytest

from grizzled.io import open_input_or_stdin

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CONTENTS = 'aaa\nbbb\nccc\n'

# ---------------------------------------------------------------------------
# Classes
# ---------------------------------------------------------------------------

class FakeStdin(StringIO):
    """
    Stand-in for sys.stdin. StringIO has no reconfigure() method, but
    open_input_or_stdin() calls it, so supply one that just records the
    encoding it was handed.
    """
    def __init__(self: Self, contents: str) -> None:
        super().__init__(contents)
        self.encoding_passed: str | None = None

    def reconfigure(self: Self, encoding: str | None = None) -> None:
        self.encoding_passed = encoding

# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_open_input_or_stdin_with_str_path(tmp_path: Path) -> None:
    """A string path is opened, read, and closed on exit."""
    path = tmp_path / 'input.txt'
    path.write_text(CONTENTS, encoding='utf-8')

    with open_input_or_stdin(str(path), encoding='utf-8') as f:
        assert f.read() == CONTENTS

    assert f.closed


def test_open_input_or_stdin_with_path_object(tmp_path: Path) -> None:
    """A Path is handled the same way as a string path."""
    path = tmp_path / 'input.txt'
    path.write_text(CONTENTS, encoding='utf-8')

    with open_input_or_stdin(path, encoding='utf-8') as f:
        assert list(f) == ['aaa\n', 'bbb\n', 'ccc\n']

    assert f.closed


def test_open_input_or_stdin_honors_encoding(tmp_path: Path) -> None:
    """The encoding parameter is passed through to open()."""
    contents = 'sûr\n'
    path = tmp_path / 'latin1.txt'
    path.write_bytes(contents.encode('iso-8859-1'))

    with open_input_or_stdin(path, encoding='iso-8859-1') as f:
        assert f.read() == contents

    # The same file, read as UTF-8, is not decodable.
    with (
        pytest.raises(UnicodeDecodeError),
        open_input_or_stdin(path, encoding='utf-8') as f,
    ):
        f.read()


def test_open_input_or_stdin_binary_mode(tmp_path: Path) -> None:
    """Mode 'rb' yields a binary stream, and the encoding is ignored."""
    path = tmp_path / 'input.txt'
    path.write_bytes(CONTENTS.encode('utf-8'))

    # The encoding is deliberately wrong for the file's contents: in binary
    # mode, it must not be applied at all.
    with open_input_or_stdin(path, encoding='iso-8859-1', mode='rb') as f:
        assert f.read() == CONTENTS.encode('utf-8')

    assert f.closed


@pytest.mark.parametrize('mode', ['rt', 'w', 'r+', 'a', 'rU', ''])
def test_open_input_or_stdin_bad_mode(tmp_path: Path, mode: str) -> None:
    """Only 'r' and 'rb' are supported; anything else is rejected."""
    path = tmp_path / 'input.txt'
    path.write_text(CONTENTS, encoding='utf-8')

    expected = re.escape(f'Unsupported mode: {mode}')
    with (
        pytest.raises(ValueError, match=expected),
        open_input_or_stdin(path, encoding='utf-8', mode=mode),
    ):
        pass

    # The rejection must happen before anything is written or truncated.
    assert path.read_text(encoding='utf-8') == CONTENTS


def test_open_input_or_stdin_nonexistent_file(tmp_path: Path) -> None:
    """A nonexistent path propagates the underlying error."""
    with (
        pytest.raises(FileNotFoundError),
        open_input_or_stdin(tmp_path / 'nope.txt', encoding='utf-8'),
    ):
        pass


def test_open_input_or_stdin_with_stdin(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    """A path of None yields standard input, reconfigured and left open."""
    fake_stdin = FakeStdin(CONTENTS)
    monkeypatch.setattr('sys.stdin', fake_stdin)

    with open_input_or_stdin(None, encoding='utf-8') as f:
        assert f is fake_stdin
        assert f.read() == CONTENTS

    assert fake_stdin.encoding_passed == 'utf-8'

    # We didn't open stdin, so we must not have closed it.
    assert not fake_stdin.closed


@pytest.mark.parametrize('mode', ['r', 'rb', 'bogus'])
def test_open_input_or_stdin_ignores_mode_for_stdin(
    monkeypatch: pytest.MonkeyPatch, mode: str
) -> None:
    """
    The mode parameter is ignored entirely when reading standard input:
    stdin is always yielded as the text stream it already is, and even an
    otherwise-unsupported mode is not rejected.
    """
    fake_stdin = FakeStdin(CONTENTS)
    monkeypatch.setattr('sys.stdin', fake_stdin)

    with open_input_or_stdin(None, encoding='utf-8', mode=mode) as f:
        assert f is fake_stdin
        assert f.read() == CONTENTS
