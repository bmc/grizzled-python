"""
`grizzled.collections.dict` contains some useful dictionary classes
that extend the behavior of the built-in Python `dict` type.
"""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

from __future__ import annotations

import sys
from collections.abc import Callable, Iterable, Iterator
from typing import TYPE_CHECKING, Any, Protocol, Self, runtime_checkable

if TYPE_CHECKING:
    # The standard library type stubs declare `dict.keys()`,
    # `dict.values()` and `dict.items()` as returning these view types, so
    # any override of those methods in a `dict` subclass has to use the same
    # return types. (Otherwise, type checkers such as pyright and Pylance
    # flag the overrides as incompatible.) These names aren't part of the
    # public runtime API, so they're imported for type-checking only.
    from _collections_abc import dict_items, dict_keys, dict_values

# ---------------------------------------------------------------------------
# Exports
# ---------------------------------------------------------------------------

__all__ = ["LRUDict"]

# ---------------------------------------------------------------------------
# Internal types
# ---------------------------------------------------------------------------


@runtime_checkable
class _SupportsKeysAndGetItem(Protocol):
    """
    Structural type for any object with `keys()` and `__getitem__()`
    methods. `dict.update()` (and `dict.__or__()`, and friends) accept such
    objects, in addition to iterables of key/value pairs, so the `LRUDict`
    versions of those methods have to accept them, too.
    """

    def keys(self: Self) -> Iterable[Any]: ...

    def __getitem__(self: Self, key: Any, /) -> Any: ...


# What `update()`, `__or__()`, etc., accept.
_UpdateSource = _SupportsKeysAndGetItem | Iterable[tuple[Any, Any]]

# ---------------------------------------------------------------------------
# Public Classes
# ---------------------------------------------------------------------------

# Implementation note:
#
# Each entry in the LRUDict dictionary is an LRUListEntry. Basically,
# we maintain two structures:
#
# 1. A linked list of dictionary entries, in order of recency.
# 2. A dictionary of those linked list items.
#
# When accessing or updating an entry in the dictionary, the logic
# is more or less like the following "get" scenario:
#
# - Using the key, get the LRUListEntry from the dictionary.
# - Extract the value from the LRUListEntry, to return to the caller.
# - Move the LRUListEntry to the front of the recency queue.
#
# Since the values stored in the underlying `dict` are LRUListEntry
# objects, not the caller's values, every inherited `dict` method that
# exposes or stores values has to be overridden.


class LRUListEntry:
    """
    An entry in a least-recently-used (LRU) linked list.
    """

    def __init__(self: Self, key: Any, value: Any):
        """
        Initialize an LRU list entry with the given key and value.

        :param key: The key associated with this entry.
        :param value: The value associated with this entry.
        """
        self.key: Any = key
        self.value: Any = value
        self.next: LRUListEntry | None = None
        self.previous: LRUListEntry | None = None

    def __hash__(self) -> int:
        """Return the hash of the key associated with this entry."""
        return hash(self.key)

    def __str__(self) -> str:
        """Return a string representation of the LRU list entry."""
        return f"({self.key}, {self.value})"

    def __repr__(self) -> str:
        """Return a detailed string representation of the LRU list entry."""
        return str(self)


class LRUList:
    """
    A least-recently-used (LRU) linked list.
    """

    def __init__(self: Self) -> None:
        """Initialize an empty LRU list."""
        self.head: LRUListEntry | None = None
        self.tail: LRUListEntry | None = None
        self.size = 0

    def __del__(self: Self) -> None:
        """Destructor for the LRU list. Clears all entries."""
        self.clear()

    def __str__(self: Self) -> str:
        """Return a string representation of the LRU list."""
        return "[" + ", ".join([str(tup) for tup in self.items()]) + "]"

    def __repr__(self: Self) -> str:
        """Return a detailed string representation of the LRU list."""
        return f"{self.__class__.__name__}:{self}"

    def __len__(self: Self) -> int:
        """Return the number of entries in the LRU list."""
        return self.size

    def __iter__(self: Self) -> Iterator[Any]:
        """Return an iterator over the keys of the LRU list."""
        entry = self.head
        while entry:
            yield entry.key
            entry = entry.next

    def __reversed__(self: Self) -> Iterator[Any]:
        """Return an iterator over the keys of the LRU list in reverse order."""
        entry = self.tail
        while entry:
            yield entry.key
            entry = entry.previous

    def keys(self: Self) -> list[Any]:
        """Return a list of the keys in the LRU list."""
        return list(self)

    def items(self: Self) -> list[tuple[Any, Any]]:
        """Return a list of the (key, value) pairs in the LRU list."""
        return list(self.iteritems())

    def values(self: Self) -> list[Any]:
        """Return a list of the values in the LRU list."""
        return list(self.itervalues())

    def iteritems(self: Self) -> Iterator[tuple[Any, Any]]:
        entry = self.head
        while entry:
            yield (entry.key, entry.value)
            entry = entry.next

    def iterkeys(self: Self) -> Iterator[Any]:
        """Return an iterator over the keys of the LRU list."""
        return iter(self)

    def itervalues(self: Self) -> Iterator[Any]:
        """Return an iterator over the values of the LRU list."""
        entry = self.head
        while entry:
            yield entry.value
            entry = entry.next

    def clear(self: Self) -> None:
        """Remove all entries from the LRU list."""
        while self.head:
            cur = self.head
            next_entry = self.head.next
            cur.next = cur.previous = cur.key = cur.value = None
            self.head = next_entry

        self.tail = None
        self.size = 0

    def remove(self: Self, entry: LRUListEntry) -> None:
        """Remove a specific entry from the LRU list."""
        if entry.next:
            entry.next.previous = entry.previous

        if entry.previous:
            entry.previous.next = entry.next

        if entry is self.head:
            self.head = entry.next

        if entry is self.tail:
            self.tail = entry.previous

        entry.next = entry.previous = None
        self.size -= 1
        assert self.size >= 0

    def remove_tail(self: Self) -> LRUListEntry | None:
        """
        Remove and return the tail entry of the LRU list, or None if the list
        is empty.
        """
        result = self.tail

        if result:
            self.remove(result)

        return result

    def add_to_head(self: Self, entry: LRUListEntry | tuple[Any, Any]) -> None:
        """Add an entry to the head of the LRU list."""
        if isinstance(entry, tuple):
            key, value = entry
            entry = LRUListEntry(key, value)
        else:
            entry.next = entry.previous = None

        if self.head:
            assert self.tail
            entry.next = self.head
            self.head.previous = entry
            self.head = entry

        else:
            assert not self.tail
            self.head = self.tail = entry

        self.size += 1

    def move_to_head(self: Self, entry: LRUListEntry) -> None:
        """Move a specific entry to the head of the LRU list."""
        self.remove(entry)
        self.add_to_head(entry)


class LRUDict(dict[Any, Any]):
    """
    `LRUDict` is a dictionary of a fixed maximum size that enforces a least
    recently used discard policy. When the dictionary is full (i.e., contains
    the maximum number of entries), any attempt to insert a new entry causes
    one of the least recently used entries to be discarded.

    **Note**:

    - Setting or updating a key in the dictionary refreshes the corresponding
      value, making it "new" again, even if it replaces the existing value with
      itself.
    - Retrieving a value from the dictionary also refreshes the entry.
    - Iterating over the contents of the dictionary (via ``in`` or ``items()``
      or any other similar method) does *not* affect the recency of the
      dictionary's contents.
    - Iteration order is most recently used to least recently used.
      `reversed()` yields the entries in the opposite order.
    - `keys()`, `values()` and `items()` return dictionary views, as they do
      for a built-in `dict`. However, since the views have to be built from
      the recency queue, they're views onto a *snapshot* of the dictionary's
      contents, taken at the time of the call; they don't track subsequent
      changes to the `LRUDict`.
    - This implementation is *not* thread-safe.

    An `LRUDict` also supports the concept of *removal listeners*. Removal
    listeners are functions that are notified when objects are removed from
    the dictionary. Removal listeners can be:

    - _eject only_ listeners, meaning they're only notified when objects are
      ejected from the cache to make room for new objects, or
    - _removal_ listeners, meaning they're notified whenever an object is
      removed for *any* reason, including via `del`.
    """

    def __init__(
        self: Self, source: _UpdateSource | None = None, /, **kw: Any
    ):
        """
        Initialize an `LRUDict` that will hold, at most, `max_capacity` items.
        Attempts to insert more than `max_capacity` items in the dictionary
        will cause the least-recently used entries to drop out of the
        dictionary.

        :param source: Initial contents for the dictionary, either as a mapping
            or an iterable of key/value pairs. The items are inserted in the
            order in which they are encountered, so the last one inserted is
            the most recently used.
        :param max_capacity (int): The maximum size of the dictionary
        :param kw: Any other keyword arguments are added to the dictionary as
            key/value pairs, exactly as they are by `dict`.
        """
        dict.__init__(self)
        self.__max_capacity: int = kw.pop("max_capacity", sys.maxsize)
        self.__removal_listeners: dict[
            Callable, tuple[bool, tuple[Any, ...]]
        ] = {}
        self.__lru_queue = LRUList()

        if source is not None:
            self.update(source)

        if kw:
            self.update(kw)

    def __del__(self: Self) -> None:
        """
        Destructor for the `LRUDict`. Clears the dictionary to ensure that
        all removal listeners are notified and resources are released.
        """
        self.clear()

    def get_max_capacity(self: Self) -> int:
        """
        Get the maximum capacity of the dictionary.

        :return: The maximum capacity of the dictionary
        """
        return self.__max_capacity

    def set_max_capacity(self: Self, new_capacity: int) -> None:
        """
        Set or change the maximum capacity of the dictionary. Reducing
        the size of a dictionary with items already in it might result
        in items being evicted.

        :param new_capacity: the new maximum capacity
        """
        self.__max_capacity = new_capacity
        if len(self) > new_capacity:
            self._clear_to(new_capacity)

    max_capacity = property(
        get_max_capacity,
        set_max_capacity,
        doc="The maximum capacity. Can be reset at will.",
    )

    def add_ejection_listener(
        self: Self, listener: Callable, *args: Any
    ) -> None:
        """
        Add an ejection listener to the dictionary. The listener function
        should take at least two parameters: the key and value being removed.
        It can also take additional parameters, which are passed through
        unmodified.

        An ejection listener is only notified when objects are ejected from
        the cache to make room for new objects; more to the point, an ejection
        listener is never notified when an object is removed from the cache
        manually, via use of the ``del`` operator.

        :param listener: The function to call when an item is ejected
        :param args: Additional arguments to pass to the listener function
        """
        self.__removal_listeners[listener] = (True, args)

    def add_removal_listener(
        self: Self, listener: Callable, *args: Any
    ) -> None:
        """
        Add a removal listener to the dictionary. The listener function should
        take at least two parameters: the key and value being removed. It can
        also take additional parameters, which are passed through unmodified.

        A removal listener is notified when objects are ejected from the cache
        to make room for new objects *and* when objects are manually deleted
        from the cache.

        :param listener: The function to call when an item is removed
        :param args: Additional arguments to pass to the listener function
        """
        self.__removal_listeners[listener] = (False, args)

    def remove_listener(self: Self, listener: Callable) -> bool:
        """
        Remove the specified removal or ejection listener from the list of
        listeners.

        :param listener: The function to remove from the list of listeners
        :return: `True` if the function was found and removed, `False` otherwise
        """
        try:
            del self.__removal_listeners[listener]
            return True
        except KeyError:
            return False

    def clear_listeners(self: Self) -> None:
        """
        Clear all removal and ejection listeners from the list of listeners.
        """
        for key in list(self.__removal_listeners.keys()):
            del self.__removal_listeners[key]

    def __setitem__(self: Self, key: Any, value: Any) -> None:
        """
        Set the value associated with the given key in the dictionary.

        :param key: The key to set
        :param value: The value to associate with the key
        """
        self.__put(key, value)

    def __getitem__(self: Self, key: Any) -> Any:
        """
        Get the value associated with the given key in the dictionary.

        :param key: The key to look up
        :return: The value associated with the key
        """
        lru_entry = dict.__getitem__(self, key)
        self.__lru_queue.move_to_head(lru_entry)
        return lru_entry.value

    def __delitem__(self: Self, key: Any) -> None:
        """
        Delete the value associated with the given key from the dictionary.

        :param key: The key to delete
        """
        lru_entry = dict.__getitem__(self, key)
        self.__lru_queue.remove(lru_entry)
        dict.__delitem__(self, key)
        self._notify_listeners(False, [(lru_entry.key, lru_entry.value)])

    def __str__(self: Self) -> str:
        """
        Return a string representation of the dictionary.

        :return: A string representing the dictionary
        """
        contents = ", ".join(
            [f"{key!r}: {value!r}" for key, value in self.items()]
        )
        return "{" + contents + "}"

    def __repr__(self: Self) -> str:
        """
        Return a string representation of the dictionary suitable for debugging.

        :return: A string representing the dictionary
        """
        return str(self)

    def __eq__(self: Self, other: object) -> bool:
        # The values in the underlying dict are LRUListEntry objects, so
        # dict.__eq__() would compare the wrappers, not the values. Compare
        # the actual contents, instead. Recency is not part of equality.
        if isinstance(other, LRUDict):
            return self._snapshot() == other._snapshot()
        if isinstance(other, dict):
            return self._snapshot() == other

        return NotImplemented

    def __iter__(self: Self) -> Iterator[Any]:
        return iter(self.__lru_queue)

    def __reversed__(self: Self) -> Iterator[Any]:
        return reversed(self.__lru_queue)

    def __or__(self: Self, other: _UpdateSource) -> LRUDict:
        result = self.copy()
        result.update(other)
        return result

    def __ror__(self: Self, other: _UpdateSource) -> LRUDict:
        """
        Right-hand operand of the `|` operator when the left-hand operand is
        not an `LRUDict`.

        :param other: The mapping or iterable of key-value pairs to update from
        :return: A new `LRUDict` containing the combined contents
        """
        result = LRUDict(other, max_capacity=self.__max_capacity)
        result.update(self._snapshot())
        return result

    def __ior__(self: Self, other: _UpdateSource) -> LRUDict:
        """
        In-place update of the dictionary with another mapping or iterable of
        key-value pairs.

        :param other: The mapping or iterable of key-value pairs to update from
        :return: The updated dictionary (self)
        """
        self.update(other)
        return self

    def clear(self: Self) -> None:
        """
        Clear all items from the dictionary.
        """
        self._clear_to(0)

    def copy(self: Self) -> LRUDict:
        """
        Make a shallow copy of this dictionary. The copy has the same maximum
        capacity and the same recency ordering as this dictionary, but it does
        *not* inherit this dictionary's removal and ejection listeners.

        :return: A shallow copy of the dictionary with the same maximum
            capacity and recency order
        """
        result = LRUDict(max_capacity=self.__max_capacity)
        # Insert least recently used first, so that the copy ends up with
        # the same recency order as the original.
        for key, value in reversed(self.items()):
            result[key] = value

        return result

    def get(self: Self, key: Any, default: Any = None) -> Any:
        """
        Get the value associated with a key, refreshing the entry's recency if
        the key is present.

        :param key: The key to look up
        :param default: The value to return if the key is not present
        :return: The value associated with `key`, or `default` if there is
            none.
        """
        try:
            return self[key]
        except KeyError:
            return default

    def setdefault(self: Self, key: Any, default: Any = None) -> Any:
        """
        Get the value associated with a key, inserting `default` (and
        returning it) if the key isn't already present. Either way, the
        entry ends up as the most recently used one.

        :param key: The key to look up
        :param default: The value to insert if the key isn't present
        :return: The existing value for `key`, or `default` if it was inserted
        """
        try:
            return self[key]
        except KeyError:
            self[key] = default
            return default

    def keys(self: Self) -> dict_keys[Any, Any]:
        """
        Get a view of the keys in the dictionary, in most recently used to
        least recently used order. The view is a view onto a snapshot of the
        dictionary's contents; see the class documentation.

        :return: A view of the keys in the dictionary, in most recently used to
            least recently used order.
        """
        return self._snapshot().keys()

    def items(self: Self) -> dict_items[Any, Any]:
        """
        Get a view of the key/value pairs in the dictionary, in most recently
        used to least recently used order. The view is a view onto a snapshot
        of the dictionary's contents; see the class documentation.

        :return: A view of the key/value pairs in the dictionary, in most
            recently used to least recently used order.
        """
        return self._snapshot().items()

    def values(self: Self) -> dict_values[Any, Any]:
        """
        Get a view of the values in the dictionary, in most recently used to
        least recently used order. The view is a view onto a snapshot of the
        dictionary's contents; see the class documentation.

        :return: A view of the values in the dictionary, in most recently used
            to least recently used order.
        """
        return self._snapshot().values()

    def iteritems(self: Self) -> Iterator[tuple[Any, Any]]:
        """
        Get an iterator over the key/value pairs in the dictionary, in most
        recently used to least recently used order.

        :return: An iterator over the key/value pairs in the dictionary, in
            most recently used to least recently used order.
        """
        return iter(self.__lru_queue.items())

    def iterkeys(self: Self) -> Iterator[Any]:
        """
        Get an iterator over the keys in the dictionary, in most recently used
        to least recently used order.

        :return: An iterator over the keys in the dictionary, in most recently
        used to least recently used order.
        """
        return iter(self.__lru_queue.keys())

    def itervalues(self: Self) -> Iterator[Any]:
        """
        Get an iterator over the values in the dictionary, in most recently
        used to least recently used order.

        :return: An iterator over the values in the dictionary, in most
            recently used to least recently used order.
        """
        return iter(self.__lru_queue.values())

    def update(self: Self, other: _UpdateSource = (), /, **kw: Any) -> None:
        """
        Update the dictionary with the key/value pairs from `other`,
        overwriting existing keys. Returns nothing.

        `update()` accepts either a mapping (or any object with `keys()` and
        `__getitem__()` methods) or an iterable of key/value pairs (as tuples
        or other iterables of length two). If keyword arguments are specified,
        the dictionary is then updated with those key/value pairs, e.g.,
        `d.update(red=1, blue=2)`.

        Keywords arguments take precedence. Thus, in:

            d.update({'red': 1}, red=2)

        the value `2` will be associated with key `red`.

        :param other: The mapping or iterable of key/value pairs to update the
            dictionary with.
        :param kw: Additional key/value pairs to update the dictionary with.
        """
        pairs: Iterable[tuple[Any, Any]]
        if isinstance(other, _SupportsKeysAndGetItem):
            keys = other.keys()
            pairs = [(key, other[key]) for key in keys]
        else:
            pairs = other

        for key, value in pairs:
            self[key] = value

        for key, value in kw.items():
            self[key] = value

    def pop(self: Self, key: Any, default: Any = None) -> Any:
        """
        "Pop" (i.e., retrieve and remove) the specified key from the
        dictionary.

        :param key: The key to remove.
        :param default: The default to return if the key is not found. If
            `None`, a `KeyError` is raised.
        :return: The value associated with `key`, or `default` if the key is
            not found. If `default` is `None`, a `KeyError` is raised.
        :raises KeyError: If the key is not found and `default` is `None`.
        """
        try:
            result = self[key]
            del self[key]

        except KeyError:
            if default is None:
                raise

            result = default

        return result

    def popitem(self: Self) -> tuple[Any, Any]:
        """
        Pops the least recently used recent key/value pair from the
        dictionary.

        :return: The least recently used `(key, value)` pair, as a tuple.
        :raises KeyError: If the dictionary is empty.
        """
        if len(self) == 0:
            raise KeyError("Attempted popitem() on empty dictionary")

        lru_entry = self.__lru_queue.remove_tail()
        assert lru_entry is not None
        dict.__delitem__(self, lru_entry.key)
        return lru_entry.key, lru_entry.value

    def _snapshot(self: Self) -> dict[Any, Any]:
        # A plain dict copy of the contents, in most recently used to least
        # recently used order. Does not affect recency.
        return dict(self.__lru_queue.items())

    def __put(self: Self, key: Any, value: Any) -> None:
        try:
            lru_entry = dict.__getitem__(self, key)

            # Replacing an existing value with a new one. Move the entry
            # to the head of the list.

            lru_entry.value = value
            self.__lru_queue.move_to_head(lru_entry)

        except KeyError:
            # Not there. Have to add a new one. Clear out the cruft first.
            # Preserve one of the entries we're clearing, to avoid
            # reallocation.

            lru_entry = self._clear_to(self.max_capacity - 1)
            if lru_entry:
                lru_entry.key, lru_entry.value = key, value
            else:
                lru_entry = LRUListEntry(key, value)
            self.__lru_queue.add_to_head(lru_entry)

        dict.__setitem__(self, key, lru_entry)

    def _clear_to(self: Self, size: int) -> LRUListEntry | None:
        old_tail = None
        while len(self.__lru_queue) > size:
            old_tail = self.__lru_queue.remove_tail()
            assert old_tail
            key, value = old_tail.key, old_tail.value
            dict.__delitem__(self, key)
            self._notify_listeners(True, [(key, value)])

        assert len(self.__lru_queue) <= size
        assert len(self) == len(self.__lru_queue)
        return old_tail

    def _notify_listeners(
        self: Self, ejecting: bool, key_value_pairs: Iterable[tuple[Any, Any]]
    ) -> None:
        if self.__removal_listeners:
            for key, value in key_value_pairs:
                for func, func_data in list(self.__removal_listeners.items()):
                    on_eject_only, args = func_data
                    if (not on_eject_only) or ejecting:
                        func(key, value, *args)
