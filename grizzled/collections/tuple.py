"""
``grizzled.collections.tuple`` contains some useful tuple-related classes
and functions.
"""
__docformat__ = "restructuredtext en"

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

from operator import itemgetter as _itemgetter
from keyword import iskeyword as _iskeyword
import sys as _sys

# ---------------------------------------------------------------------------
# Exports
# ---------------------------------------------------------------------------

__all__ = ['namedtuple']

# ---------------------------------------------------------------------------
# Public Functions
# ---------------------------------------------------------------------------

def namedtuple(typename, fieldnames, verbose=False):
    """
    Returns a new subclass of tuple with named fields. If running under Python
    2.6 or newer, this function is nothing more than an alias for the
    standard Python ``collections.namedtuple()`` function. Otherwise,
    this function is a local implementation, adapted from an
    `ActiveState namedtuple recipe`_.
    
    .. _ActiveState namedtuple recipe: http://code.activestate.com/recipes/500261/

    Usage:
    
    .. python::

        Point = namedtuple('Point', 'x y')
        p0 = Point(10, 20)
        p1 = Point(11, y=22)
        p2 = Point(x=1, y=2)
        print p2[0]          # prints 1
        print p1[1]          # prints 22
        x, y = p0            # x=10, y=20
        print p0.x           # prints 10
        d = p2._asdict()     # convert to dictionary
        print d['x']         # prints 1
        
    :Parameters:
        typename : str
            Name for the returned class
            
        fieldnames : str or sequence
            A single string with each field name separated by whitespace and/or 
            commas (e.g., 'x y' or 'x, y'). Alternatively, ``fieldnames`` can 
            be a sequence of strings such as ['x', 'y'].

        verbose : bool
            If ``True``, the class definition will be printed to standard 
            output before being returned

    :rtype: class
    :return: The named tuple class
    
    :raise ValueError: Bad parameters
    """
    return _namedtuple(typename, fieldnames, verbose=verbose)

# ---------------------------------------------------------------------------
# Private
# ---------------------------------------------------------------------------

def _local_namedtuple(typename, fieldnames, verbose=False):
    # Parse and validate the field names. Validation serves two purposes,
    # generating informative error messages and preventing template injection
    # attacks.

    if isinstance(fieldnames, basestring):
        # names separated by whitespace and/or commas
        fieldnames = fieldnames.replace(',', ' ').split()

    fieldnames = tuple(map(str, fieldnames))
    for name in (typename,) + fieldnames:
        if not min(c.isalnum() or c=='_' for c in name):
            raise ValueError('Type names and field names can only contain '
                             'alphanumeric characters and underscores: %r' % name)

        if _iskeyword(name):
            raise ValueError('Type names and field names cannot be a keyword: '
                             '%r' % name)

        if name[0].isdigit():
            raise ValueError('Type names and field names cannot start with a '
                             'number: %r' % name)

    seen_names = set()
    for name in fieldnames:
        if name.startswith('_'):
            raise ValueError('Field names cannot start with an underscore: '
                             '%r' % name)
        if name in seen_names:
            raise ValueError('Encountered duplicate field name: %r' % name)

        seen_names.add(name)

    # Create and fill-in the class template

    numfields = len(fieldnames)
    argtxt = repr(fieldnames).replace("'", "")[1:-1]   # tuple repr without parens or quotes
    reprtxt = ', '.join('%s=%%r' % name for name in fieldnames)
    dicttxt = ', '.join('%r: t[%d]' % (name, pos) for pos, name in enumerate(fieldnames))
    template = '''class %(typename)s(tuple):
        '%(typename)s(%(argtxt)s)' \n
        __slots__ = () \n
        _fields = %(fieldnames)r \n
        def __new__(cls, %(argtxt)s):
            return tuple.__new__(cls, (%(argtxt)s)) \n
        @classmethod
        def _make(cls, iterable, new=tuple.__new__, len=len):
            'Make a new %(typename)s object from a sequence or iterable'
            result = new(cls, iterable)
            if len(result) != %(numfields)d:
                raise TypeError('Expected %(numfields)d arguments, got %%d' %% len(result))
            return result \n
        def __repr__(self):
            return '%(typename)s(%(reprtxt)s)' %% self \n
        def _asdict(t):
            'Return a new dict which maps field names to their values'
            return {%(dicttxt)s} \n
        def _replace(self, **kwds):
            'Return a new %(typename)s object replacing specified fields with new values'
            result = self._make(map(kwds.pop, %(fieldnames)r, self))
            if kwds:
                raise ValueError('Got unexpected field names: %%r' %% kwds.keys())
            return result \n\n''' % locals()
    for i, name in enumerate(fieldnames):
        template += '        %s = property(itemgetter(%d))\n' % (name, i)

    if verbose:
        print template

    # Execute the template string in a temporary namespace
    namespace = dict(itemgetter=_itemgetter)
    try:
        exec template in namespace
    except SyntaxError, e:
        raise SyntaxError(e.message + ':\n' + template)

    result = namespace[typename]

    # For pickling to work, the __module__ variable needs to be set to the
    # frame where the named tuple is created. Bypass this step in enviroments
    # where sys._getframe is not defined (Jython for example).

    if hasattr(_sys, '_getframe') and _sys.platform != 'cli':
        result.__module__ = _sys._getframe(1).f_globals['__name__']

    return result

# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------

if _sys.hexversion >= 0x2060000:
    import collections
    _namedtuple = collections.namedtuple
else:
    _namedtuple = _local_namedtuple
