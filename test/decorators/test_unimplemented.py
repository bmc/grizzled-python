"""
Tester.
"""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

from typing import Self

import pytest

from grizzled.decorators import unimplemented

# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_unimplemented_function() -> None:
    """Test that an unimplemented function raises NotImplementedError."""

    @unimplemented
    def my_func() -> None:
        pass

    with pytest.raises(NotImplementedError):
        my_func()

def test_unimplemented_method() -> None:
    """Test that an unimplemented method raises NotImplementedError."""

    class MyClass:
        @unimplemented
        def my_method(self: Self) -> None:
            pass

    obj = MyClass()
    with pytest.raises(NotImplementedError):
        obj.my_method()
