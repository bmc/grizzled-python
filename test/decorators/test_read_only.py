"""
Tester.
"""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

import inspect

import pytest

from grizzled.decorators import (
    READ_ONLY_FROZEN_ATTR,
    ReadOnlyObjectError,
    read_only,
)


@read_only
class Something:
    """A simple read-only class, with dunders, for testing."""

    def __init__(self, a=1, b=2):
        self.a = a
        self.b = b

    def __len__(self) -> int:
        return self.a

    def __getitem__(self, key):
        return key

    def __repr__(self) -> str:
        return f"Something({self.a}, {self.b})"


@pytest.fixture
def something() -> Something:
    """Fixture that provides a frozen Something instance."""
    return Something(10, 20)


def test_init_assignments_are_allowed(something: Something) -> None:
    """Test that __init__ can still assign to self."""
    assert something.a == 10
    assert something.b == 20


def test_type_is_unchanged(something: Something) -> None:
    """Test that the decorator doesn't disturb the object's identity."""
    assert something.__class__ is Something
    assert type(something) is Something
    assert isinstance(something, Something)


def test_special_methods_still_work(something: Something) -> None:
    """Test that dunder methods are not hidden, as a proxy would hide
    them."""
    assert len(something) == 10
    assert something["x"] == "x"
    assert repr(something) == "Something(10, 20)"


def test_set_existing_field(something: Something) -> None:
    """Test that assigning to an existing attribute is refused."""
    with pytest.raises(ReadOnlyObjectError) as exc_info:
        something.a = 200

    assert exc_info.value.field_name == "a"
    assert something.a == 10


def test_modify_existing_field(something: Something) -> None:
    """Test that augmented assignment is refused."""
    with pytest.raises(ReadOnlyObjectError):
        something.a += 1

    assert something.a == 10


def test_set_new_field(something: Something) -> None:
    """Test that creating a new attribute is refused. A type checker
    rejects this statically, too; the runtime guard is what protects
    callers it can't see, such as setattr() and untyped code."""
    with pytest.raises(ReadOnlyObjectError) as exc_info:
        something.c = 30  # pyright: ignore[reportAttributeAccessIssue]

    assert exc_info.value.field_name == "c"
    assert not hasattr(something, "c")


def test_delete_field(something: Something) -> None:
    """Test that deleting an attribute is refused."""
    with pytest.raises(ReadOnlyObjectError) as exc_info:
        del something.a

    assert exc_info.value.field_name == "a"
    assert something.a == 10


def test_freezing_is_shallow() -> None:
    """Test that the contents of a mutable field can still be changed,
    as is also true of a frozen dataclass."""

    @read_only
    class Holder:
        def __init__(self):
            self.items = [1]

    holder = Holder()
    holder.items.append(2)
    assert holder.items == [1, 2]

    with pytest.raises(ReadOnlyObjectError):
        holder.items = []


def test_undecorated_subclass_is_mutable() -> None:
    """Test that a subclass that isn't itself decorated can initialize
    itself after calling super().__init__(), and stays mutable."""

    class Sub(Something):
        def __init__(self):
            super().__init__(1, 2)
            self.c = 3

    sub = Sub()
    assert sub.c == 3

    sub.a = 100
    assert sub.a == 100


def test_decorated_subclass_is_frozen() -> None:
    """Test that decorating a subclass freezes its instances, without
    breaking its call to super().__init__()."""

    @read_only
    class Sub(Something):
        def __init__(self):
            super().__init__(1, 2)
            self.c = 3

    sub = Sub()
    assert (sub.a, sub.b, sub.c) == (1, 2, 3)

    with pytest.raises(ReadOnlyObjectError):
        sub.c = 4

    with pytest.raises(ReadOnlyObjectError):
        sub.a = 4


def test_slots_class() -> None:
    """Test that a class using __slots__ can be frozen, as long as it
    makes room for the frozen marker."""

    @read_only
    class Slotted:
        __slots__ = ("a", READ_ONLY_FROZEN_ATTR)

        def __init__(self, a):
            self.a = a

    slotted = Slotted(5)
    assert slotted.a == 5

    with pytest.raises(ReadOnlyObjectError):
        slotted.a = 6


def test_class_with_no_init() -> None:
    """Test that a class that doesn't define __init__ is still frozen."""

    @read_only
    class Empty:
        pass

    with pytest.raises(ReadOnlyObjectError):
        Empty().a = 1  # pyright: ignore[reportAttributeAccessIssue]


def test_double_decoration_is_harmless() -> None:
    """Test that decorating a class twice doesn't doubly wrap
    __init__."""

    @read_only
    @read_only
    class Twice:
        def __init__(self):
            self.a = 1

    twice = Twice()
    assert twice.a == 1

    with pytest.raises(ReadOnlyObjectError):
        twice.a = 2


def test_init_is_faithfully_wrapped() -> None:
    """Test that the wrapped __init__ keeps the original's identity and
    signature, and that arguments reach it unmolested."""
    assert Something.__init__.__name__ == "__init__"
    assert list(inspect.signature(Something).parameters) == ["a", "b"]

    by_keyword = Something(b=200)
    assert (by_keyword.a, by_keyword.b) == (1, 200)
