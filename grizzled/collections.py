#!/usr/bin/env python
#
# $Id$
# ---------------------------------------------------------------------------

"""
``grizzled.collections`` provides some useful Python collection classes.
"""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Exports
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Public Classes
# ---------------------------------------------------------------------------

class OrderedDict(dict):
    """
    ``OrderedDict`` is a simple ordered dictionary. The ``keys()``,
    ``items()``, ``__iter__()``, and other methods all return the keys in the
    order they were added to the dictionary. Note that re-adding a key (i.e.,
    replacing a key with a new value) does not change the original order.

    An ``OrderedDict`` object is instantiated with exactly the same parameters
    as a ``dict`` object. The methods it provides are identical to those in
    the ``dict`` type and are not documented here.
    """
    def __init__(self, *args, **kw):
        dict.__init__(self, *args, **kw)
        self.__orderedKeys = []
        self.__keyPositions = {}

    def __setitem__(self, key, value):
        try:
            index = self.__keyPositions[key]
        except KeyError:
            index = len(self.__orderedKeys)
            self.__orderedKeys += [key]
            self.__keyPositions[key] = index

        dict.__setitem__(self, key, value)

    def __delitem__(self, key):
        index = self.__keyPositions[key]
        del self.__orderedKeys[index]
        del self.__keyPositions[key]
        dict.__delitem__(self, key)

    def __iter__(self):
        for key in self.__orderedKeys:
            yield key

    def __str__(self):
        s = '{'
        sep = ''
        for k, v in self.iteritems():
            s += sep
            if type(k) == str:
                s += "'%s'" % k
            else:
                s += str(k)

            s += ': '
            if type(v) == str:
                s += "'%s'" % v
            else:
                s += str(v)
            sep = ', '
        s += '}'
        return s
    
    def keys(self):
        return self.__orderedKeys

    def items(self):
        return [(key, self[key]) for key in self.__orderedKeys]

    def values(self):
        return [self[key] for key in self.__orderedKeys]

    def iteritems(self):
        for key in self.__orderedKeys:
            yield (key, self[key])

    def iterkeys(self):
        for key in self.__orderedKeys:
            yield key

    def update(self, d):
        for key, value in d.iteritems():
            self[key] = value

    def pop(self, key, default=None):
        try:
            result = self[key]
            del self[key]

        except KeyError:
            if not default:
                raise

            result = default

        return result

    def popitem(self):
        key, value = dict.popitem(self)
        del self[key]
        return (key, value)
