# Nose program for testing grizzled.file classes/functions

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

from grizzled.text import str2bool
import pytest

def test_good_strings():
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

def test_bad_strings():
    for s in ('foo', 'bar', 'xxx', 'yyy', ''):
        with pytest.raises(ValueError):
            str2bool(s)
