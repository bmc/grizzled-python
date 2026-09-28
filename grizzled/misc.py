"""
Overview
========

The `grizzled.misc` module contains miscellanous functions and classes that
don't seem to fit well in other modules.
"""

__docformat__ = "markdown"

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Exports
# ---------------------------------------------------------------------------

__all__ = ["bitcount"]


# ---------------------------------------------------------------------------
# Public functions
# ---------------------------------------------------------------------------


def bitcount(num: int) -> int:
    """
    Count the number of bits in a numeric (integer or long) value. This
    method is adapted from the Hamming Weight algorithm, described (among
    other places) at http://en.wikipedia.org/wiki/Hamming_weight

    Works for up to 64 bits.

    :param num: The numeric value whose bits are to be counted
    :returns: The number of 1 bits in the binary representation of `num`
    """
    # Put count of each 2 bits into those 2 bits.
    num = num - ((num >> 1) & 0x5555555555555555)

    # Put count of each 4 bits into those 4 bits.
    num = (num & 0x3333333333333333) + ((num >> 2) & 0x3333333333333333)

    # Put count of each 8 bits into those 8 bits.
    num = (num + (num >> 4)) & 0x0F0F0F0F0F0F0F0F

    # Left-most bits.
    return int((num * 0x0101010101010101) >> 56)
