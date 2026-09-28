# Nose program for testing grizzled.io PushbackFile class

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------


import logging
from contextlib import contextmanager
from os import environ
from typing import Generator

from grizzled.os import (
    DEFAULT_TERMINAL_HEIGHT,
    DEFAULT_TERMINAL_WIDTH,
    ENV_COLUMNS,
    ENV_LINES,
    get_terminal_size,
)

log = logging.getLogger("test_get_terminal_size")

@contextmanager
def temp_env(env_sub: dict[str, str | None]) -> Generator[None]:
    original_environ = environ.copy()

    for key, value in env_sub.items():
        if value is None:
            if key in environ:
                del environ[key]
        else:
            environ[key] = value

        log.info(f"Temporary environment set: {key}={environ.get(key)}")
    try:
        yield
    finally:
        environ.clear()
        environ.update(original_environ)

def test_get_terminal_size() -> None:
    """Test the get_terminal_size function."""

    def do_test(
        expected_height: int | None = None,
        expected_width: int | None = None,
        fd: int | None = None,
    ) -> None:
        size = get_terminal_size(fd=fd)
        assert isinstance(size, tuple)
        assert len(size) == 2
        columns, rows = size
        log.info(f"Terminal size: columns={columns}, rows={rows}")
        assert all(isinstance(dim, int) for dim in size)
        assert columns > 0
        assert rows > 0
        if expected_width is not None:
            assert columns == expected_width
        if expected_height is not None:
            assert rows == expected_height


    log.info("Testing get_terminal_size with default file descriptor.")
    do_test()

    log.info("Testing get_terminal_size with fd=2")
    do_test(fd=2)

    log.info("Testing get_terminal_size with /dev/tty")
    with open("/dev/tty") as f:
        do_test(fd=f.fileno())

    log.info(
        "Testing get_terminal_size with /dev/null, which should fall "
        f"back to {ENV_COLUMNS} and {ENV_LINES} environment variables."
    )
    cols, lines = (100, 43)
    with (temp_env({ENV_COLUMNS: str(cols), ENV_LINES: str(lines)}),
          open("/dev/null") as f):
        do_test(fd=f.fileno(), expected_width=cols, expected_height=lines)

    log.info(f"Testing get_terminal_size with bad value for {ENV_COLUMNS}")
    with (temp_env({ENV_COLUMNS: "invalid", ENV_LINES: str(lines)}),
          open("/dev/null") as f):
        do_test(fd=f.fileno(),
                expected_width=DEFAULT_TERMINAL_WIDTH,
                expected_height=lines)

    log.info(f"Testing get_terminal_size with bad value for {ENV_LINES}")
    with (temp_env({ENV_COLUMNS: str(cols), ENV_LINES: "invalid"}),
          open("/dev/null") as f):
        do_test(fd=f.fileno(),
                expected_width=cols,
                expected_height=DEFAULT_TERMINAL_HEIGHT)

    log.info("Testing get_terminal_size with no environment variables set.")
    with (temp_env({ENV_COLUMNS: None, ENV_LINES: None}),
          open("/dev/null") as f):
        do_test(fd=f.fileno(),
                expected_width=DEFAULT_TERMINAL_WIDTH,
                expected_height=DEFAULT_TERMINAL_HEIGHT)

    log.info("Testing with negative values for environment variables.")
    with (temp_env({ENV_COLUMNS: "-100", ENV_LINES: "-43"}),
          open("/dev/null") as f):
        do_test(fd=f.fileno(),
                expected_width=DEFAULT_TERMINAL_WIDTH,
                expected_height=DEFAULT_TERMINAL_HEIGHT)
