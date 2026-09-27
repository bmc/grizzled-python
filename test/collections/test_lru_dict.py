"""
Tester.
"""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

from typing import Any, Self

import pytest

from grizzled.collections import LRUDict

# ---------------------------------------------------------------------------
# Exports
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Classes
# ---------------------------------------------------------------------------

class TestLRUDict:

    def test_1(self: Self) -> None:
        lru = LRUDict(max_capacity=5)

        print("Adding 'a' and 'b'")
        lru['a'] = 'A'
        lru['b'] = 'b'
        print(lru)
        print(list(lru.keys()))
        assert list(lru.keys()) == ['b', 'a']
        assert list(lru.values()) == ['b', 'A']

        print("Adding 'c'")
        lru['c'] = 'c'
        print(lru)
        print(list(lru.keys()))
        assert list(lru.keys()) == ['c', 'b', 'a']

        print("Updating 'a'")
        lru['a'] = 'a'
        print(lru)
        print(list(lru.keys()))
        assert list(lru.keys()) == ['a', 'c', 'b']

        print("Adding 'd' and 'e'")
        lru['d'] = 'd'
        lru['e'] = 'e'
        print(lru)
        print(list(lru.keys()))
        assert list(lru.keys()) == ['e', 'd', 'a', 'c', 'b']

        print("Accessing 'b'")
        assert lru['b'] == 'b'
        print(lru)
        print(list(lru.keys()))
        assert list(lru.keys()) == ['b', 'e', 'd', 'a', 'c']

        print("Adding 'f'")
        lru['f'] = 'f'
        # Should knock 'c' out of the list
        print(lru)
        print(list(lru.keys()))
        assert list(lru.keys()) == ['f', 'b', 'e', 'd', 'a']

        def on_remove(key: Any, value: Any, the_list: list[Any]) -> None:
            print(f'on_remove("{key}")')
            the_list.append(key)

        print('Reducing capacity. Should result in eviction.')
        ejected = []
        lru.add_ejection_listener(on_remove, ejected)
        lru.max_capacity = 3
        ejected.sort()
        print(f'ejected={ejected}')
        assert ejected == ['a', 'd']
        print(list(lru.keys()))
        assert list(lru.keys()) == ['f', 'b', 'e']

        print('Testing popitem()')
        key, value = lru.popitem()
        print(lru)
        print(list(lru.keys()))
        assert key == 'e'
        assert list(lru.keys()) == ['f', 'b']

        print('Clearing dictionary')
        lru.clear_listeners()
        lru.clear()
        del lru

    def add_one(self: Self, lru: LRUDict, key: Any) -> None:
        lru[key] = key

    def test_big(self: Self) -> None:
        print('Putting 10000 entries in a new LRU cache')
        lru = LRUDict(max_capacity=10000)
        for i in range(0, lru.max_capacity):
            lru[i] = i

        assert len(lru) == lru.max_capacity
        print('Adding one more')
        assert len(lru) == lru.max_capacity
        print(next(iter(lru)))

    def test_views(self: Self) -> None:
        lru = LRUDict(max_capacity=3)
        lru['a'] = 'A'
        lru['b'] = 'B'

        # keys(), values() and items() return dict views, in most recently
        # used to least recently used order.
        assert list(lru.keys()) == ['b', 'a']
        assert list(lru.values()) == ['B', 'A']
        assert list(lru.items()) == [('b', 'B'), ('a', 'A')]
        assert len(lru.keys()) == 2
        assert 'a' in lru
        assert (lru.keys() | {'c'}) == {'a', 'b', 'c'}

        # Iterating doesn't change recency.
        assert list(lru) == ['b', 'a']
        assert list(reversed(lru)) == ['a', 'b']
        assert list(lru.keys()) == ['b', 'a']

        assert str(lru) == "{'b': 'B', 'a': 'A'}"
        assert repr(lru) == str(lru)

    def test_constructor_contents(self: Self) -> None:
        lru = LRUDict({'a': 1, 'b': 2}, max_capacity=5)
        assert list(lru.keys()) == ['b', 'a']
        assert lru.max_capacity == 5

        lru = LRUDict([('a', 1), ('b', 2)], c=3)
        assert list(lru.keys()) == ['c', 'b', 'a']

        # Initial contents are subject to the capacity limit, too.
        lru = LRUDict({'a': 1, 'b': 2, 'c': 3}, max_capacity=2)
        assert list(lru.keys()) == ['c', 'b']

    def test_get(self: Self) -> None:
        lru = LRUDict(max_capacity=3)
        lru['a'] = 'A'
        lru['b'] = 'B'

        # get() returns the value, and it refreshes the entry.
        assert lru.get('a') == 'A'
        assert list(lru.keys()) == ['a', 'b']
        assert lru.get('nonexistent') is None
        assert lru.get('nonexistent', 'default') == 'default'

    def test_setdefault(self: Self) -> None:
        lru = LRUDict(max_capacity=2)
        lru['a'] = 1

        assert lru.setdefault('b', 2) == 2
        assert lru.setdefault('a', 999) == 1
        assert list(lru.keys()) == ['a', 'b']

        # Inserting via setdefault() honors the capacity limit.
        assert lru.setdefault('c', 3) == 3
        assert list(lru.keys()) == ['c', 'a']
        assert len(lru) == 2

    def test_copy_and_equality(self: Self) -> None:
        lru = LRUDict(max_capacity=3)
        lru['a'] = 1
        lru['b'] = 2

        assert lru == {'a': 1, 'b': 2}
        assert lru == {'a': 1, 'b': 2}
        assert lru != {'a': 1}

        copy = lru.copy()
        assert copy == lru
        assert copy.max_capacity == lru.max_capacity
        assert list(copy.keys()) == list(lru.keys())

        copy['c'] = 3
        assert 'c' not in lru

    def test_or(self: Self) -> None:
        lru = LRUDict({'a': 1}, max_capacity=5)

        merged = lru | {'b': 2}
        assert isinstance(merged, LRUDict)
        assert merged == {'a': 1, 'b': 2}
        assert merged.max_capacity == 5
        assert lru == {'a': 1}

        merged = {'b': 2} | lru
        assert merged == {'a': 1, 'b': 2}

        lru |= {'b': 2}
        assert lru == {'a': 1, 'b': 2}
        assert list(lru.keys()) == ['b', 'a']

    def test_update(self: Self) -> None:
        lru = LRUDict(max_capacity=2)

        # A mapping, an iterable of pairs, and keywords all work, and all of
        # them honor the capacity limit.
        lru.update({'a': 1, 'b': 2, 'c': 3})
        assert list(lru.keys()) == ['c', 'b']

        lru.update([('d', 4)])
        assert list(lru.keys()) == ['d', 'c']

        lru.update({'e': 5}, e=6)
        assert lru['e'] == 6
        assert list(lru.keys()) == ['e', 'd']

        # Anything with keys() and __getitem__() is acceptable.
        class Mappingish:
            def keys(self: Self) -> list[str]:
                return ['x', 'y']

            def __getitem__(self, key: Any) -> str:
                return key.upper()

        lru = LRUDict()
        lru.update(Mappingish())
        assert lru == {'x': 'X', 'y': 'Y'}

    def test_listeners_get_values(self: Self) -> None:
        removed = []

        def on_remove(key: Any, value: Any, accumulator: list[Any]) -> None:
            accumulator.append((key, value))

        lru = LRUDict(max_capacity=2)
        lru.add_removal_listener(on_remove, removed)
        lru['a'] = 'A'
        lru['b'] = 'B'

        # Ejecting 'a' to make room for 'c' notifies the listener with the
        # ejected value, not None.
        lru['c'] = 'C'
        assert removed == [('a', 'A')]

        del lru['b']
        assert removed == [('a', 'A'), ('b', 'B')]

        assert lru.remove_listener(on_remove)
        assert not lru.remove_listener(on_remove)

    def test_pop(self: Self) -> None:
        lru = LRUDict(max_capacity=5)
        lru.update({'a': 1, 'b': 2})

        assert lru.pop('a') == 1
        assert lru == {'b': 2}
        assert lru.pop('a', 'default') == 'default'

        with pytest.raises(KeyError):
            lru.pop('a')

        assert lru.popitem() == ('b', 2)

        with pytest.raises(KeyError):
            lru.popitem()

    def test_is_a_dict(self: Self) -> None:
        lru = LRUDict(max_capacity=5)
        lru['a'] = 1

        assert isinstance(lru, dict)
        assert 'a' in lru
        assert len(lru) == 1

        lru2 = LRUDict.fromkeys(['a', 'b'], 0)
        assert isinstance(lru2, LRUDict)
        assert lru2 == {'a': 0, 'b': 0}
        assert list(lru2.keys()) == ['b', 'a']
