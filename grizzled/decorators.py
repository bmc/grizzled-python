"""
This module contains various Python decorators.
"""

__docformat__ = "markdown"

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

import functools
from typing import Any, Callable, NoReturn, ParamSpec, TypeVar

# ---------------------------------------------------------------------------
# Exports
# ---------------------------------------------------------------------------

__all__ = ["deprecated", "unimplemented"]

# ---------------------------------------------------------------------------
# Type variables
# ---------------------------------------------------------------------------

P = ParamSpec("P")
R = TypeVar("R")

# ---------------------------------------------------------------------------
# Decorators
# ---------------------------------------------------------------------------


def deprecated(
    since: str | None = None, message: str | None = None
) -> Callable[..., Any]:
    """
    Decorator for marking a function deprecated. Generates a warning on
    standard output if the function is called.

    Usage:

    ```python
    from grizzled.decorators import deprecated

    class MyClass(object):
        @deprecated()
        def oldMethod(self):
            pass

    Given the above declaration, the following code will cause a
    warning to be printed (though the method call will otherwise succeed):

    ```python
    obj = MyClass()
    obj.oldMethod()
    ```

    You may also specify a `since` argument, used to display a deprecation
    message with a version stamp (e.g., 'deprecated since ...'):

    ```python
    from grizzled.decorators import deprecated

    class MyClass(object):
        @deprecated(since='1.2')
        def oldMethod(self):
            pass
    ```

    :param since: version stamp, or `None` for none
    :param message: optional additional message to print
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        if since is None:
            buf = f"Method {func.__name__} is deprecated."
        else:
            buf = f"Method {func.__name__} has been deprecated since version {since}."

        if message:
            buf += " " + message

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            import warnings

            warnings.warn(buf, category=DeprecationWarning, stacklevel=2)
            return func(*args, **kwargs)

        return wrapper

    return decorator


def unimplemented(func: Callable[P, R]) -> Callable[P, R]:
    """
    Decorator for marking a function or method unimplemented. Throws a
    `NotImplementedError` if called.

    Usage:

    ```python
    from grizzled.decorators import unimplemented

    class ReadOnlyDict(dict):

        @unimplemented
        def __setitem__(self, key, value):
            pass
    ```
    """

    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> NoReturn:
        raise NotImplementedError(
            f'Method or function "{func.__name__}" is not implemented'
        )

    return wrapper
