"""
Tester.
"""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

import inspect
import warnings
from collections.abc import Generator
from contextlib import contextmanager
from typing import Self

import pytest

from grizzled.decorators import deprecated

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


@contextmanager
def captured() -> Generator[list[warnings.WarningMessage]]:
    """
    Capture every warning raised within the block, bypassing the warning
    filters that would otherwise show a given warning only once.

    :return: a list that receives the captured warnings
    """
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        yield caught


def message_from(caught: list[warnings.WarningMessage]) -> str:
    """
    Extract the text of the single warning that was captured.

    :param caught: the captured warnings
    :return: the text of the one and only warning
    """
    assert len(caught) == 1
    return str(caught[0].message)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_warning_is_issued_on_call() -> None:
    """Test that calling a deprecated function issues a
    DeprecationWarning."""

    @deprecated()
    def old_function() -> None:
        pass

    with pytest.warns(DeprecationWarning):
        old_function()


def test_decoration_alone_is_silent() -> None:
    """Test that merely decorating a function doesn't warn. The warning
    belongs to the call, not the declaration."""
    with captured() as caught:

        @deprecated(since="1.2", message="Use new_function() instead.")
        def old_function() -> None:
            pass

    assert caught == []


def test_default_message() -> None:
    """Test the wording when neither `since` nor `message` is given."""

    @deprecated()
    def old_function() -> None:
        pass

    with captured() as caught:
        old_function()

    assert message_from(caught) == "Method old_function is deprecated."


def test_since_message() -> None:
    """Test the wording when `since` is given."""

    @deprecated(since="1.2")
    def old_function() -> None:
        pass

    with captured() as caught:
        old_function()

    assert message_from(caught) == (
        "Method old_function has been deprecated since version 1.2."
    )


def test_extra_message_is_appended() -> None:
    """Test that `message` is appended to the default wording."""

    @deprecated(message="Use new_function() instead.")
    def old_function() -> None:
        pass

    with captured() as caught:
        old_function()

    assert message_from(caught) == (
        "Method old_function is deprecated. Use new_function() instead."
    )


def test_since_and_message_together() -> None:
    """Test that `since` and `message` combine."""

    @deprecated(since="2.0", message="Use new_function() instead.")
    def old_function() -> None:
        pass

    with captured() as caught:
        old_function()

    assert message_from(caught) == (
        "Method old_function has been deprecated since version 2.0. "
        "Use new_function() instead."
    )


def test_empty_message_is_not_appended() -> None:
    """Test that an empty `message` doesn't leave a trailing space."""

    @deprecated(message="")
    def old_function() -> None:
        pass

    with captured() as caught:
        old_function()

    assert message_from(caught) == "Method old_function is deprecated."


def test_return_value_is_passed_through() -> None:
    """Test that the deprecated function still returns its value."""

    @deprecated()
    def old_function() -> str:
        return "result"

    with captured():
        assert old_function() == "result"


def test_arguments_are_forwarded() -> None:
    """Test that positional arguments, keyword arguments and defaults
    all reach the wrapped function."""

    @deprecated()
    def old_function(a: int, b: int, c: int = 3) -> tuple[int, int, int]:
        return (a, b, c)

    with captured():
        assert old_function(1, 2) == (1, 2, 3)
        assert old_function(1, b=2, c=30) == (1, 2, 30)
        assert old_function(*[1, 2], **{"c": 30}) == (1, 2, 30)


def test_exceptions_propagate() -> None:
    """Test that the wrapper doesn't swallow the function's
    exceptions."""

    @deprecated()
    def old_function() -> None:
        raise ValueError("boom")

    with captured(), pytest.raises(ValueError, match="boom"):
        old_function()


def test_metadata_is_preserved() -> None:
    """Test that functools.wraps keeps the wrapped function's identity
    and signature."""

    @deprecated()
    def old_function(a: int, b: int = 2) -> None:
        """Original docstring."""

    assert old_function.__name__ == "old_function"
    assert old_function.__doc__ == "Original docstring."
    assert list(inspect.signature(old_function).parameters) == ["a", "b"]


def test_warning_is_attributed_to_the_caller() -> None:
    """Test that stacklevel=2 blames the calling line, rather than a
    line inside the decorator, which is what makes the warning useful."""

    @deprecated()
    def old_function() -> None:
        pass

    frame = inspect.currentframe()
    assert frame is not None

    with captured() as caught:
        call_line = frame.f_lineno + 1
        old_function()

    assert caught[0].filename == __file__
    assert caught[0].lineno == call_line


def test_every_call_warns() -> None:
    """Test that the warning isn't issued only once per function."""

    @deprecated()
    def old_function() -> None:
        pass

    with captured() as caught:
        for _ in range(3):
            old_function()

    assert len(caught) == 3


def test_separately_decorated_functions_do_not_share_a_message() -> None:
    """Test that each decorated function closes over its own message."""

    @deprecated(since="1.0")
    def first() -> None:
        pass

    @deprecated(since="2.0")
    def second() -> None:
        pass

    with captured() as caught:
        first()
        second()

    assert str(caught[0].message) == (
        "Method first has been deprecated since version 1.0."
    )
    assert str(caught[1].message) == (
        "Method second has been deprecated since version 2.0."
    )


def test_works_on_methods() -> None:
    """Test that the decorator works on methods, and names the method."""

    class Something:
        @deprecated(since="1.2")
        def old_method(self: Self) -> str:
            return "result"

    something = Something()

    with captured() as caught:
        assert something.old_method() == "result"

    assert message_from(caught) == (
        "Method old_method has been deprecated since version 1.2."
    )
