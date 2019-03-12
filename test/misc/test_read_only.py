"""
Tester.
"""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

from grizzled.misc import ReadOnly, ReadOnlyObjectError
import pytest

class Something(object):
    def __init__(self, a=1, b=2):
        self.a = a
        self.b = b

@pytest.fixture
def readonly_something():
    something = Something(10, 20)
    assert something.a == 10
    assert something.b == 20

    something.a += 1
    assert something.a == 11

    return ReadOnly(something)

def test_class_attr(readonly_something):
    assert readonly_something.__class__ is Something

def test_is_instance(readonly_something):
    assert isinstance(readonly_something, Something)

def test_access_1(readonly_something):
    with pytest.raises(ReadOnlyObjectError):
        readonly_something.a += 1

def test_access_2(readonly_something):
    with pytest.raises(ReadOnlyObjectError):
        readonly_something.a = 200

