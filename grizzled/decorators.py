# $Id$

"""
This module contains various Python decorators.
"""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

from grizzled.exception import ExceptionWithMessage

# ---------------------------------------------------------------------------
# Exports
# ---------------------------------------------------------------------------

__all__ = ['deprecated', 'abstract', 'UnimplementedMethodError']

# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class UnimplementedMethodError(ExceptionWithMessage):
    """
    Thrown to indicate an unimplemented abstract method.
    """
    pass

# ---------------------------------------------------------------------------
# Decorators
# ---------------------------------------------------------------------------

def deprecated(since=None):
    """
    Decorator for marking a function deprecated. Generates a warning on
    standard output if the function is called.

    Usage::

        from grizzled.decorators import deprecated

        class MyClass(object):

            @deprecated()
            def oldMethod(self):
                pass

    Given the above declaration, the following code will cause a
    warning to be printed (though the method call will otherwise succeed)::

        obj = MyClass()
        obj.oldMethod()

    You may also specify a C{since} argument, used to display a deprecation
    message with a version stamp (e.g., 'deprecated since ...')::

        from grizzled.decorators import deprecated

        class MyClass(object):

            @deprecated(since='1.2')
            def oldMethod(self):
                pass

    @type since:  string
    @param since: version stamp, or C{None} for none
    """
    def decorator(func):
        if since == None:
            message = 'Method %s is deprecated.' % func.__name__
        else:
            message = 'Method %s has been deprecated since version %s.' %\
                      (func.__name__, since)

        def wrapper(*__args, **__kw):
            import warnings
            warnings.warn(message, category=DeprecationWarning, stacklevel=2)
            return func(*__args,**__kw)

        wrapper.__name__ = func.__name__
        wrapper.__dict__ = func.__dict__
        wrapper.__doc__ = func.__doc__
        return wrapper

    return decorator

def abstract(func):
    """
    Decorator for marking a function abstract. Throws an
    L{UnimplementedMethodError} if an abstract method is called.

    Usage::

        from grizzled.decorators import abstract

        class MyAbstractClass(object):

            @abstract
            def abstractMethod(self):
                pass

        class NotReallyConcrete(MyAbstractClass):
            # Class doesn't define abstractMethod().

    Given the above declaration, the following code will cause an
    L{UnimplementedMethodError}::

        obj = NotReallyConcrete()
        obj.abstractMethod()
    """
    def wrapper(*__args, **__kw):
        raise UnimplementedMethodError('Missing required %s() method' %\
                                       func.__name__)
    wrapper.__name__ = func.__name__
    wrapper.__dict__ = func.__dict__
    wrapper.__doc__ = func.__doc__
    return wrapper


# ---------------------------------------------------------------------------
# Main program, for testing
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    @deprecated()
    def func1(a):
        pass

    @deprecated(since='1.2')
    def func2():
        pass

    func1(100)
    func2()

    class Foo(object):
        @abstract
        def foo(self):
            pass

    class Bar(Foo):
        pass

    b = Bar()
    try:
        b.foo()
        assert False
    except UnimplementedMethodError, ex:
        import sys
        print ex.message
