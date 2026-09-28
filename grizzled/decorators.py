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

__all__ = [
    "deprecated",
    "read_only",
    "unimplemented",
    "ReadOnlyObjectError",
]

# ---------------------------------------------------------------------------
# Type variables
# ---------------------------------------------------------------------------

P = ParamSpec("P")
R = TypeVar("R")
T = TypeVar("T", bound=type)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Instance attribute used by @read_only to record that an object has
# finished initializing and is now frozen. Classes that use __slots__
# must include this name in their __slots__.

READ_ONLY_FROZEN_ATTR = "_grizzled_read_only_frozen"

# Class attribute used to mark a class as already decorated, so that
# applying the decorator twice to the same class is harmless.

_READ_ONLY_MARKER = "_grizzled_read_only_decorated"

# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class ReadOnlyObjectError(AttributeError):
    """
    Thrown by classes decorated with `read_only`, to indicate an attempt
    to set or delete a field of a frozen object.
    """

    def __init__(self, field_name: str, message: str):
        """
        Initialize a new `ReadOnlyObjectError`.

        :param field_name: Name of the field that was being modified
        :param message: Exception message
        """
        super().__init__(message)
        self.field_name = field_name


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


def read_only(cls: T) -> T:
    """
    Class decorator that makes instances of a class read-only (frozen) once
    `__init__()` has finished running. This is roughly the equivalent of
    `@dataclass(frozen=True)`, but it works on ordinary classes: the decorated
    class needs no field annotations, and it can define its own `__init__()`,
    which is free to assign to `self` as usual.

    Usage:

    ```python

    from grizzled.decorators import read_only

    @read_only
    class Point:
        def __init__(self, x, y):
            self.x = x
            self.y = y

    p = Point(1, 2)
    p.x = 10    # raises ReadOnlyObjectError
    del p.y     # raises ReadOnlyObjectError
    ```

    Any attempt to set or delete an attribute of a fully constructed
    instance—including an attribute that doesn't already exist—raises a
    `ReadOnlyObjectError`. Unlike a wrapper object, the decorator changes the
    class itself, so `type()`, `isinstance()` and all special methods
    (`__len__()`, `__getitem__()`, `__repr__()`, etc.) continue to behave
    normally.

    Some caveats:

    - Freezing is shallow, exactly as it is for a frozen dataclass. For
      example, if a class has a mutable field called `items` that references a
      list, the contents of that list can still be modified, even though
      `items` itself cannot be bound to something else. This is also consistent
      with how `@dataclass(frozen=True)` works.
    - A class that uses `__slots__` must include
      `decorators.READ_ONLY_FROZEN_ATTR` in its `__slots__`, since the
      decorator records the frozen state in an instance attribute.
    - An instance is frozen only when the `__init__()` of the decorated class
      returns *and* the instance is of exactly that class. A subclass is
      therefore free to initialize itself after calling `super().__init__()`;
      to freeze the subclass's instances, decorate the subclass, too.
    - Applying the decorator to the same class more than once is a no-op.

    :param cls: The class to make read-only
    :return: The same class, modified in place
    :raises ReadOnlyObjectError: (from instances) on attempted modification
    """
    if cls.__dict__.get(_READ_ONLY_MARKER, False):
        return cls

    wrapped_init: Callable[..., None] = cls.__init__

    @functools.wraps(wrapped_init)
    def __init__(self: Any, *args: Any, **kwargs: Any) -> None:
        """
        Run the original `__init__()`, which is free to assign to
        `self`, and then freeze the object. The object is frozen only
        if it is exactly an instance of the decorated class, so that an
        undecorated subclass can still initialize itself after calling
        `super().__init__()`.

        :param args: positional arguments for the original `__init__()`
        :param kwargs: keyword arguments for the original `__init__()`
        """
        wrapped_init(self, *args, **kwargs)
        if type(self) is cls:
            object.__setattr__(self, READ_ONLY_FROZEN_ATTR, True)

    def frozen(self: Any) -> bool:
        """
        Determine whether an object has finished initializing and is
        now read-only. The marker attribute is missing, rather than
        `False`, while `__init__()` is still running.

        :return: `True` if the object is frozen, `False` if it is still
            under construction
        """
        return getattr(self, READ_ONLY_FROZEN_ATTR, False)

    def refuse(self: Any, name: str, verb: str) -> NoReturn:
        """
        Reject an attempt to modify a frozen object.

        :param name: the name of the field being modified
        :param verb: what the caller was trying to do to the field,
            for the error message (e.g., "set")
        :raises ReadOnlyObjectError: always
        """
        raise ReadOnlyObjectError(
            name,
            f'Attempt to {verb} field "{name}" of read-only '
            f"{type(self).__name__} object",
        )

    def __setattr__(self: Any, name: str, value: Any) -> None:
        """
        Set a field, as long as the object is still under construction.
        Note that this refuses new fields as well as existing ones: a
        frozen object's set of fields is fixed.

        :param name: the name of the field to set
        :param value: the value to give the field
        :raises ReadOnlyObjectError: if the object is frozen
        """
        if frozen(self):
            refuse(self, name, "set")

        object.__setattr__(self, name, value)

    def __delattr__(self: Any, name: str) -> None:
        """
        Delete a field, as long as the object is still under
        construction.

        :param name: the name of the field to delete
        :raises ReadOnlyObjectError: if the object is frozen
        """
        if frozen(self):
            refuse(self, name, "delete")

        object.__delattr__(self, name)

    # These assignments install the functions in the class, for its
    # instances to use. Type checkers read "cls.__setattr__" as the bound
    # method of the class object itself, though, so an unbound function
    # appears to have one parameter too many. Assigning through an
    # untyped alias says that this is a deliberate patch of the class.

    patched: Any = cls
    patched.__init__ = __init__
    patched.__setattr__ = __setattr__
    patched.__delattr__ = __delattr__
    setattr(cls, _READ_ONLY_MARKER, True)
    return cls
