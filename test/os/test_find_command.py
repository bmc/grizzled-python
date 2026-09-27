# Nose program for testing grizzled.io PushbackFile class

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

from io import StringIO

from grizzled.os import find_command


def test_find_command() -> None:
    """Test the find_command function."""
    assert find_command("python") is not None
    assert find_command("python", path=None) is not None
    assert find_command("python", path="") is not None
    assert find_command("python", path=[]) is None
    assert find_command("foobarbaz") is None

