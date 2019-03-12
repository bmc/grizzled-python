from grizzled.misc import bitcount

def test_bitcount():
    data = [
    # value      expected
    (1000,         518),
    (2,            1),
    (3,            2),
    (10,           2),
    (0x00ff,       8),
    (0x00efef00ac, 118361618),
    ]
    for n, expected in data:
        v = bitcount(n)
        assert v == expected, 'Expected {}, got {}'.format(expected, v)
