# $Id$

"""
A dummy database driver, useful for testing.
"""

BINARY = 0
NUMBER = 1
STRING = 2
DATETIME = 3
ROWID = 4

class DummyCursor(object):
    def close(self):
        pass

    def execute(self, statement, parameters=None):
        self.rowcount = 0
        self.description = ""
        return None

    def fetchone(self):
        raise ValueError, "No results"

    def fetchall(self):
        raise ValueError, "No results"

    def fetchmany(self, n):
        raise ValueError, "No results"

class DummyDB(object):

    def __init__(self):
        pass

    def cursor(self):
        return DummyCursor()

    def commit(self):
        pass

    def rollback(self):
        pass

    def close(self):
        pass
