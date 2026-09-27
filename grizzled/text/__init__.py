"""
The `grizzled.text` package contains text-related classes and modules.
"""


__docformat__ = "markdown"

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

import itertools
from io import StringIO
from typing import TextIO

# ---------------------------------------------------------------------------
# Exports
# ---------------------------------------------------------------------------

__all__ = ['hexdump', 'strip_margin']

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

REPEAT_FORMAT = '*** Repeated %d times'

# ---------------------------------------------------------------------------
# Functions
# ---------------------------------------------------------------------------

def strip_margin(s: str, margin_char: str = '|') -> str:
    """
    Akin to Scala's stripMargin() method on string, this function takes a
    multiline string and strips leading white space up to a margin character.
    It allows you to express multiline strings like this:

    ```python
    s = '''|line 1
           |line 2
            |line 3
        '''
    ```

    Then, calling strip_margin on the string results in:

    ```python
    '''line 1
    line 2
    line 3
    '''
    ```

    :param s: The multiline string to strip.
    :param margin_char: The margin character, defaulting to '|'. Must be a
        single character.
    :return: The stripped string.
    """
    assert len(margin_char) == 1
    def fix_line(line: str) -> str:
        adj = ''.join(itertools.dropwhile(lambda c: c in [' ', '\t'], line))
        if (len(adj) > 0) and (adj[0] == margin_char):
            return adj[1:]
        else:
            return adj

    return '\n'.join(map(fix_line, s.split('\n')))


def hexdump(source: str | TextIO,
            out: TextIO,
            width: int = 16,
            start: int = 0,
            limit: int | None = None,
            show_repeats: bool = False) -> None:
    """
    Produce a "standard" hexdump of the specified string or file-like
    object. The output consists of a series of lines like this::

        000000: 72 22 22 22 4f  53 20 72 6f 75  r'''OS rou
        00000a: 74 69 6e 65 73  20 66 6f 72 20  tines for
        000014: 4d 61 63 2c 20  4e 54 2c 20 6f  Mac, NT, o
        00001e: 72 20 50 6f 73  69 78 20 64 65  r Posix de
        000028: 70 65 6e 64 69  6e 67 20 6f 6e  pending on
        000032: 20 77 68 61 74  20 73 79 73 74   what syst
        00003c: 65 6d 20 77 65  27 72 65 20 6f  em we're o
        000046: 6e 2e 0a 0a 54  68 69 73 20 65  n...This e

    The output width (i.e., the number of decoded characters shown on a
    line) can be controlled with the `width` parameter.

    Adjacent repeated lines are collapsed by default. For example::

        000000: 00 00 00 00 00  00 00 00 00 00  ..........
        *** Repeated 203 times
        0007f8: 72 22 22 22 4f  53 20 72 6f 75  r'''OS rou

    This behavior can be disabled via the `show_repeats` parameter.

    :param source: The object whose contents are to be dumped in hex. The
        object can be a string or a file-like object.
    :param out: Where to dump the hex output
    :param width: The number of dumped characters per line
    :param start: Offset within `input` where reading should begin
    :param limit: Total number of bytes to dump. Defaults to everything from
        `start` to the end.
    :param show_repeats: `False` to collapse repeated output lines, `True` to
        dump all lines, even if they're repeats.
    """

    def ascii(b: int) -> str:
        """Determine how to show a byte in ascii."""
        if 32 <= b <= 126:
            return chr(b)
        else:
            return '.'

    pos = 0
    ascii_map = [ ascii(c) for c in range(256) ]

    lastbuf = ''
    lastline = ''
    repeat_count = 0

    space_col = width // 2 if width > 4 else -1

    if type(source) is str:
        source = StringIO(source)

    assert isinstance(source, TextIO)
    if start:
        source.seek(start)
        pos = start

    hex_field_width = (width * 3) + 1

    total_read = 0
    while True:
        to_read = min(limit - total_read, width) if limit else width

        buf = source.read(to_read)
        length = len(buf)
        total_read += length
        if length == 0:
            if repeat_count and (not show_repeats):
                if repeat_count > 1:
                    print(REPEAT_FORMAT % (repeat_count - 1), file=out)
                elif repeat_count == 1:
                    print(lastline, file=out)
                print(lastline, file=out)
            break

        else:
            show_buf = True

            if buf == lastbuf:
                repeat_count += 1
                show_buf = False
            else:
                if repeat_count and (not show_repeats):
                    if repeat_count == 1:
                        print(lastline, file=out)
                    else:
                        print(REPEAT_FORMAT % (repeat_count - 1), file=out)
                    repeat_count = 0

            # Build output line.
            hex = ""
            asc = ""
            for i in range(length):
                c = buf[i]
                if i == space_col:
                    hex = hex + " "
                hex = f"{hex}{ord(c):02x} "
                asc = asc + ascii_map[ord(c)]

            line = f"{pos:06x}: {hex:<{hex_field_width}} {asc}"

            if show_buf:
                print(line, file=out)

            pos = pos + length
            lastbuf = buf
            lastline = line


def str2bool(s: str) -> bool:
    """
    Convert a string to a boolean value. The supported conversions are:

    - `"false"` -> `False`
    - `"true"` -> `True`
    - `"f"` -> `False`
    - `"t"` -> `True`
    - `"0"` -> `False`
    - `"1"` -> `True`
    - `"n"` -> `False`
    - `"y"` -> `True`
    - `"no"` -> `False`
    - `"yes"` -> `True`
    - `"off"` -> `False`
    - `"on"` -> `True`

    Strings are compared in a case-blind fashion.

    **Note**: This function is not currently localizable.

    :param s: The string to convert to boolean
    :return: The corresponding boolean value
    :raises ValueError: unrecognized boolean string
    """
    try:
        return {'false' : False,
                'true'  : True,
                'f'     : False,
                't'     : True,
                '0'     : False,
                '1'     : True,
                'no'    : False,
                'yes'   : True,
                'y'     : False,
                'n'     : True,
                'off'   : False,
                'on'    : True}[s.lower()]
    except KeyError:
        raise ValueError(f'Unrecognized boolean string: "{s}"') from None
