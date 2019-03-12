from grizzled.text import strip_margin

def test_strip_margin():
    assert strip_margin('''|abc
                           |def
                           |ghi''') == 'abc\ndef\nghi'
    assert strip_margin('''|abc
                           |def
                           |ghi
                           ''') == 'abc\ndef\nghi\n'
    assert strip_margin('''|abc
                           |def
                           |ghi
                           |''') == 'abc\ndef\nghi\n'
    assert strip_margin('''|abc
                           |
                           |ghi
                           |''') == 'abc\n\nghi\n'
    assert strip_margin('''|abc

                           |ghi
                           |''') == 'abc\n\nghi\n'
    assert strip_margin('''|abc
                           oops
                           |ghi
                           |''') == 'abc\noops\nghi\n'
