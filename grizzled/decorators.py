"""
This module contains various Python decorators.
"""

__docformat__ = "markdown"

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Exports
# ---------------------------------------------------------------------------

__all__ = ["deprecated", "unimplemented"]

# ---------------------------------------------------------------------------
# Decorators
# ---------------------------------------------------------------------------


def deprecated(since: str | None = None, message: str | None = None):
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

    def decorator(func):
        if since is None:
            buf = f"Method {func.__name__} is deprecated."
        else:
            buf = f"Method {func.__name__} has been deprecated since version {since}."

        if message:
            buf += " " + message

        def wrapper(*__args, **__kw):
            import warnings

            warnings.warn(buf, category=DeprecationWarning, stacklevel=2)
            return func(*__args, **__kw)

        wrapper.__name__ = func.__name__
        wrapper.__dict__ = func.__dict__
        wrapper.__doc__ = func.__doc__
        return wrapper

    return decorator


def unimplemented(func):
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

    def wrapper(*__args, **__kw):
        raise NotImplementedError(
            f'Method or function "{func.__name__}" is not implemented'
        )

    wrapper.__name__ = func.__name__
    wrapper.__dict__ = func.__dict__
    wrapper.__doc__ = func.__doc__
    return wrapper
