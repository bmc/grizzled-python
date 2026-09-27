# Nose program for testing grizzled.io PushbackFile class

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

from io import StringIO

from grizzled.io import PushbackFile


def test_pushback():
    inputString = """abc
def
ghi
"""
    f = StringIO(inputString)
    pb = PushbackFile(f)

    s = pb.readline()
    print(s)
    assert s == 'abc\n'
    pb.pushback(s)
    s = pb.readline()
    print(s)
    assert s == 'abc\n'
    s = pb.read(1)
    print(s)
    assert s == 'd'
    s = pb.readline()
    print(s)
    assert s == 'ef\n'
    s = pb.read(-1)
    print(s)
    assert s == 'ghi\n'
    s = pb.readline()
    assert s == ''
    pb.pushback('foobar')
    s = pb.readline()
    print(s)
    assert s == 'foobar'
