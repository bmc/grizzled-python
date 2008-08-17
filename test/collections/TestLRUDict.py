# $Id$

"""
Tester.
"""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

from grizzled.collections import LRUDict

# ---------------------------------------------------------------------------
# Exports
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Classes
# ---------------------------------------------------------------------------

class TestLRUDict(object):

    def test1(self):
        lru = LRUDict(5)

        print "Adding 'a' and 'b'"
        lru['a'] = 'A'
        lru['b'] = 'b'
        print lru
        print lru.keys()
        assert lru.keys() == ['b', 'a']
        assert lru.values() == ['b', 'A']

        print "Adding 'c'"
        lru['c'] = 'c'
        print lru
        print lru.keys()
        assert lru.keys() == ['c', 'b', 'a']

        print "Updating 'a'"
        lru['a'] = 'a'
        print lru
        print lru.keys()
        assert lru.keys() == ['a', 'c', 'b']

        print "Adding 'd' and 'e'"
        lru['d'] = 'd'
        lru['e'] = 'e'
        print lru
        print lru.keys()
        assert lru.keys() == ['e', 'd', 'a', 'c', 'b']

        print "Accessing 'b'"
        assert lru['b'] == 'b'
        print lru
        print lru.keys()
        assert lru.keys() == ['b', 'e', 'd', 'a', 'c']

        print "Adding 'f'"
        lru['f'] = 'f'
        # Should knock 'c' out of the list
        print lru
        print lru.keys()
        assert lru.keys() == ['f', 'b', 'e', 'd', 'a']
