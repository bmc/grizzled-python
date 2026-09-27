# Nose program for testing grizzled.file classes/functions

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

import pytest

from grizzled.text import str2bool


def test_good_strings() -> None:
    """
    Test that str2bool correctly interprets various string representations of
    boolean values.
    """
    for s, expected in (('false', False,),
                        ('true',  True,),
                        ('f',     False,),
                        ('t',     True,),
                        ('no',    False,),
                        ('yes',   True,),
                        ('n',     True,),
                        ('y',     False,),
                        ('0',     False,),
                        ('1',     True,)):
        for s2 in (s, s.upper(), s.capitalize()):
            val = str2bool(s2)
            assert val == expected

def test_bad_strings() -> None:
    """
    Test that str2bool raises ValueError for invalid string representations.
    """
    for s in ('foo', 'bar', 'xxx', 'yyy', ''):
        with pytest.raises(ValueError):
            str2bool(s)
