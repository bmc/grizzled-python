"""
This module contains various Python decorators.
"""

__docformat__ = "markdown"

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

from typing import Optional

# ---------------------------------------------------------------------------
# Exports
# ---------------------------------------------------------------------------

__all__ = ['deprecated', 'unimplemented']

# ---------------------------------------------------------------------------
# Decorators
# ---------------------------------------------------------------------------

def deprecated(since: Optional[str] = None, message: Optional[str] = None):
    """
    Decorator for marking a function deprecated. Generates a warning on
    standard output if the function is called.

    Usage:

        from grizzled.decorators import deprecated

        class MyClass(object):

            @deprecated()
            def oldMethod(self):
                pass

    Given the above declaration, the following code will cause a
    warning to be printed (though the method call will otherwise succeed):

        obj = MyClass()
        obj.oldMethod()

    You may also specify a `since` argument, used to display a deprecation
    message with a version stamp (e.g., 'deprecated since ...'):

        from grizzled.decorators import deprecated

        class MyClass(object):

            @deprecated(since='1.2')
            def oldMethod(self):
                pass

    **Parameters**

    - `since` (`str`): version stamp, or `None` for none
    - `message` (`str`): optional additional message to print
    """
    def decorator(func):
        if since is None:
            buf = 'Method {} is deprecated.'.format(func.__name__)
        else:
            buf = 'Method {} has been deprecated since version {}.'.format(
                  func.__name__, since
            )

        if message:
            buf += ' ' + message

        def wrapper(*__args, **__kw):
            import warnings
            warnings.warn(buf, category=DeprecationWarning, stacklevel=2)
            return func(*__args,**__kw)

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

        from grizzled.decorators import unimplemented

        class ReadOnlyDict(dict):

            @unimplemented
            def __setitem__(self, key, value):
                pass
    """
    def wrapper(*__args, **__kw):
        raise NotImplementedError(
	    'Method or function "{}" is not implemented'.format(
                func.__name__
            )
	)
    wrapper.__name__ = func.__name__
    wrapper.__dict__ = func.__dict__
    wrapper.__doc__ = func.__doc__
    return wrapper
