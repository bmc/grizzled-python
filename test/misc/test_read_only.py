"""
Tester.
"""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

import pytest

from grizzled.misc import ReadOnly, ReadOnlyObjectError


class Something:
    """A simple class for testing ReadOnly wrapper."""
    def __init__(self, a=1, b=2):
        self.a = a
        self.b = b

@pytest.fixture
def readonly_something() -> ReadOnly:
    """Fixture that provides a ReadOnly-wrapped Something instance."""
    something = Something(10, 20)
    assert something.a == 10
    assert something.b == 20

    something.a += 1
    assert something.a == 11

    return ReadOnly(something)

def test_class_attr(readonly_something: ReadOnly) -> None:
    """Test that the __class__ attribute is correctly reported."""
    assert readonly_something.__class__ is Something

def test_is_instance(readonly_something: ReadOnly) -> None:
    """Test that isinstance works correctly with ReadOnly wrapper."""
    assert isinstance(readonly_something, Something)

def test_access_1(readonly_something: ReadOnly) -> None:
    """Test that modifying an attribute raises ReadOnlyObjectError."""
    with pytest.raises(ReadOnlyObjectError):
        readonly_something.a += 1

def test_access_2(readonly_something: ReadOnly) -> None:
    """Test that assigning to an attribute raises ReadOnlyObjectError."""
    with pytest.raises(ReadOnlyObjectError):
        readonly_something.a = 200

