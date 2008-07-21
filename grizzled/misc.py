#!/usr/bin/env python
#
# $Id$

# NOTE: Documentation is intended to be processed by epydoc and contains
# epydoc markup.

"""
Overview
========

The ``grizzled.misc`` module contains miscellanous functions and classes that
don't seem to fit well in other modules.
"""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

import logging

from grizzled.exception import ExceptionWithMessage

# ---------------------------------------------------------------------------
# Exports
# ---------------------------------------------------------------------------

__all__ = ['ReadOnly', 'ReadOnlyObjectError']

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

log = logging.getLogger('grizzled.misc')

# ---------------------------------------------------------------------------
# Public classes
# ---------------------------------------------------------------------------

class ReadOnlyObjectError(ExceptionWithMessage):
    """
    Thrown by ``ReadOnly`` to indicate an attempt to set a field.

    :IVariables:
        field_name : str
            name of the read-only field that could not be set

        message : str
            message to associated with the exception
    """
    def __init__(self, field_name, message):
        ExceptionWithMessage.__init__(self, message)
        self.field_name = field_name

class ReadOnly(object):
    """
    A ``ReadOnly`` object wraps another object and prevents all the contained
    object's fields from being written. Example use:

    .. python::

        from invitemedia.lang import ReadOnly

        config = IMConfigParser()
        config.read('/path/to/some/file')
        roConfig = ReadOnly(config)

    Any attempt to set fields within ``roConfig`` will cause a
    ``ReadOnlyObjectError`` to be raised.

    The ``__class__`` member of the instantiate ``ReadOnly`` class will be the
    class of the contained object, rather than ``ReadOnly``
    (``IMConfigParser`` in the example). Similarly, the ``isinstance()``
    built-in function will compare against the contained object's class.
    However, the ``type()`` built-in will return the ``ReadOnly`` class
    object.
    """
    def __init__(self, wrapped):
        """
        Create a new ``ReadOnly`` object that wraps the ``wrapped`` object
        and enforces read-only access to it.

        :Parameters:
            wrapped : object
                the object to wrap
        """
        self.wrapped = wrapped

    def __getattribute__(self, thing):
        wrapped = object.__getattribute__(self, 'wrapped')
        result = None
        if thing == 'wrapped':
            result = wrapped
        else:
            result = getattr(wrapped, thing)

        return result

    def __setattr__(self, thing, value):
        if thing == 'wrapped':
            object.__setattr__(self, thing, value)
        else:
            raise ReadOnlyObjectError(thing,
                                      'Attempt to access field "%s" of '
                                      'read-only %s object' %
                                      (thing, self.wrapped.__class__.__name__))

# ---------------------------------------------------------------------------
# Public functions
# ---------------------------------------------------------------------------

def str2bool(s):
    """
    Convert a string to a boolean. This function differs from the built-in
    ``bool()`` constructor in that it is more restrictive, accepting only
    a small set of well-defined legal inputs.

    Legal boolean strings are currently::

        on
        off
        yes
        no
        1
        0
        true
        false

    in any mixture of case.

    **Restrictions**: This function is not currently localized; it only
    recognizes English strings.

    :Parameters:
        s : str
            string to convert to boolean

    :rtype: bool
    :return: the corresponding ``True`` or ``False`` value.
    
    :raise ValueError: Bad boolean string
    """
BOOL_STRS = { "on"    : True,
              "off"   : False,
              "yes"   : True,
              "no"    : False,
              "1"     : True,
              "0"     : False,
              "true"  : True,
              "false" : False }

    s = s.lower()
    try:
        return BOOL_STRS[s]
    except KeyError:
        raise ValueError, 'Bad value "%s" for boolean string' % s
