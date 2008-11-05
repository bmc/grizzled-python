# $Id$

"""
SQL Server extended database driver.
"""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

import os
import sys

from grizzled.db.base import DBDriver, Error, Warning

# ---------------------------------------------------------------------------
# Exports
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Classes
# ---------------------------------------------------------------------------

class SQLServerDriver(DBDriver):
    """DB Driver for Microsoft SQL Server, using the pymssql DB API module."""

    def get_import(self):
        import pymssql
        return pymssql

    def get_display_name(self):
        return 'SQL Server'

    def do_connect(self,
                   host='localhost',
                   port=None,
                   user='',
                   password='',
                   database='default'):
        dbi = self.get_import()
        self.db_name = database
        if port == None:
            port = '1433'
        return dbi.connect(host='%s:%s' % (host, port),
                           user=user,
                           password=password,
                           database=database)

    def get_tables(self, cursor):
        cursor.execute("select name from %s..sysobjects where xtype = 'U'" %
                       self.db_name)
        table_names = []
        rs = cursor.fetchone()
        while rs is not None:
            table_names += [rs[0]]
            rs = cursor.fetchone()

        return table_names

    def get_table_metadata(self, table, cursor):
        self._ensure_valid_table(cursor, table)
        dbi = self.get_import()
        cursor.execute("SELECT column_name, data_type, " \
                       "character_maximum_length, numeric_precision, " \
                       "numeric_scale, is_nullable "\
                       "FROM information_schema.columns WHERE "\
                       "LOWER(table_name) = '%s'" % table)
        rs = cursor.fetchone()
        results = []
        while rs is not None:
            is_nullable = False
            if rs[5] == 'YES':
                is_nullable = True
            results += [(rs[0], rs[1], rs[2], rs[3], rs[4], is_nullable)]
            rs = cursor.fetchone()
        return results

    def get_index_metadata(self, table, cursor):
        self._ensure_valid_table(cursor, table)
        dbi = self.get_import()
        cursor.execute("EXEC sp_helpindex '%s'" % table)
        rs = cursor.fetchone()
        results_by_name = {}
        while rs is not None:
            name = rs[0]
            description = rs[1]
            columns = rs[2].split(', ')
            results_by_name[name] = (name, columns, description)
            rs = cursor.fetchone()

        names = results_by_name.keys()
        names.sort()
        result = []
        for name in names:
            result += [results_by_name[name]]

        return result
