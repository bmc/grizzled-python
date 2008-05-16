# $Id$

"""
Introduction
============

The C{db} module is a DB API wrapper. It provides a DB API-compliant API
that wraps real underlying DB API drivers, simplifying some non-portable
operations like C{connect()} and providing some new operations.

Some drivers come bundled with this package. Others can be added on the fly.

Getting the List of Drivers
===========================

To get a list of all drivers currently registered with this module, use the
get_driver_names() method::

    import db

    for driver_name in db.get_driver_names():
        print driver_name

Currently, this module provides the following bundled drivers::

    ======================================================================
    Driver Name, as passed                           underlying Python
    to db.get_driver()          Database             DB API Module
    ======================================================================
    dummy                       None (a dummy,       db.DummyDB
                                no-op driver,
                                useful for testing)
    ----------------------------------------------------------------------
    mysql                       MySQL                MySQLdb
    ----------------------------------------------------------------------
    oracle                      Oracle               cx_Oracle
    ----------------------------------------------------------------------
    postgresql                  PostgreSQL           psycopg2
    ----------------------------------------------------------------------
    sqlserver                   Microsoft SQL Server pymssql
    ----------------------------------------------------------------------
    sqlite                      SQLite 3             pysqlite
    ======================================================================

To use a given driver, you must have the corresponding Python DB API module
installed on your system.


Adding a Driver
===============

It's possible to add a new driver to the list of drivers supplied by this
module. To do so:

 1. The driver class must extend db.DBDriver and provide the appropriate
    methods. See examples in this module.
 2. The driver's module (or the calling program) must register the driver
    with this module by calling db.add_driver()


DB API Factory Functions
========================

The C{Binary()}, C{Date()}, C{DateFromTicks()}, C{Time()},
C{TimeFromTicks()}, C{Timestamp()} and C{TimestampFromTicks()} DB API
functions can be found in the DB class. Thus, to make a string into a BLOB
with this API, you use::

    driver = db.get_driver(driver_name)
    db = driver.connect(...)
    blob = db.Binary(some_string)
"""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

from grizzled.exception import ExceptionWithMessage
from grizzled.decorators import abstract, deprecated
import dummydb

# ---------------------------------------------------------------------------
# Exports
# ---------------------------------------------------------------------------

__all__ = ['get_driver', 'add_driver', 'get_driver_names', 'DBDriver',
           'DB', 'Cursor', 'DBError', 'Error', 'Warning', 'apilevel',
           'threadsafety', 'paramstyle']

# ---------------------------------------------------------------------------
# Globals
# ---------------------------------------------------------------------------

drivers = { 'dummy'      : 'DummyDriver',
            'mysql'      : 'MySQLDriver',
            'postgresql' : 'PostgreSQLDriver',
            'sqlserver'  : 'SQLServerDriver',
            'sqlite'     : 'SQLite3Driver',
            'oracle'     : 'OracleDriver' }

apilevel = '2.0'
threadsafety = '1'
paramstyle = None

# ---------------------------------------------------------------------------
# Functions
# ---------------------------------------------------------------------------

@deprecated(since='0.4', message='Use add_driver()')
def addDriver(key, driver_class, force=False):
    add_driver(key, driver_class, force)

def add_Driver(key, driver_class, force=False):
    """
    Add a driver class to the list of drivers.

    @type key:   string
    @param key:  the key, also used as the driver's name

    @type driver_class:  C{DBDriver} subclass
    @param driver_class: The driver class

    @type force:  boolean
    @param force: C{True} to force registration of the driver, even if
                  there's an existing driver with the same key. C{False}
                  to throw an exception if there's an existing driver
                  with the same key.
    """
    try:
        className = drivers[key]
    except KeyError:
        if not force:
            raise ValueError, 'A DB driver named "%d" is already installed' %\
                  key

    drivers[key] = driver_class.__name__

@deprecated(since='0.4', message='Use get_drivers()')
def getDrivers():
    return get_drivers()

def get_drivers():
    """
    Get the list of drivers currently registered with this API.
    The result is a list of DBDriver subclasses. Note that these are
    classes, not instances. Once way to use the resulting list is as
    follows::

        for driver in db.get_drivers():
            print driver.__doc__

    @rtype:  list
    @return: list of C{DBDriver} class names
    """
    return drivers.values()

@deprecated(since='0.4', message='Use get_driver_names()')
def getDriverNames():
    return get_driver_names()

def get_driver_names():
    """
    Get the list of driver names currently registered with this API.
    Each of the returned names may be used as the first parameter to
    the L{C{get_driver()}<get_driver>} function.
    """
    return drivers.keys()

@deprecated(since='0.4', message='Use get_driver()')
def getDriver(driver_name):
    return get_driver(driver_name)

def getDriver(driver_name):
    """
    Get the DB API object for the specific database type. The list of
    legal database types are available by calling
    L{C{get_driver_names()}<get_driver_names>}.

    @type driver_name:  str
    @param driver_name: name of driver

    @return: the instantiated driver

    @raise ValueError: Unknown driver name
    """
    try:
        class_name = drivers[driver_name]
        exec 'd = %s()' % class_name
        return d
    except KeyError:
        raise ValueError, 'Unknown driver name: "%s"' % driver_name

# ---------------------------------------------------------------------------
# Classes
# ---------------------------------------------------------------------------

class DBError(ExceptionWithMessage):
    """
    Base class for all DB exceptions.
    """
    pass

class Error(DBError):
    """Thrown to indicate an error in the C{db} module."""
    pass

class Warning(DBError):
    """Thrown to indicate an error in the C{db} module."""
    pass

class Cursor(object):
    """
    Class for DB cursors returned by the C{DB.cursor()} method. This class
    conforms to the Python DB cursor interface, including the following
    attributes:

    B{C{description}}

    A read-only attribute that is a sequence of 7-item tuples, one per
    column in the last query executed::

        (name, typecode, displaysize, internalsize, precision, scale)

    B{C{rowcount}}

    A read-only attribute that specifies the number of rows
    fetched in the last query, or -1 if unknown
    """

    def __init__(self, cursor, driver):
        """
        Create a new Cursor object, wrapping the underlying real DB API
        cursor.

        @param cursor: the real DB API cursor object
        @param driver: the driver that is creating this object
        """
        self.__cursor = cursor
        self.__driver = driver
        self.__description = None
        self.__rowcount = -1

    def __get_description(self):
        return self.__description

    description = property(__get_description,
                           doc='The description field. See class docs.')

    def __get_rowcount(self):
        return self.__rowcount

    rowcount = property(__get_rowcount,
                        doc='Number of rows from last query, or -1')

    def close(self):
        """
        Close the cursor.

        @raise Warning: Non-fatal warning
        @raise Error:   Error; unable to close
        """
        dbi = self.__driver.get_import()
        try:
            return self.__cursor.close()
        except dbi.Warning, val:
            raise Warning(val)
        except dbi.Error, val:
            raise Error(val)

    def execute(self, statement, parameters=None):
        """
        Execute a SQL statement string with the given parameters.
        'parameters' is a sequence when the parameter style is
        'format', 'numeric' or 'qmark', and a dictionary when the
        style is 'pyformat' or 'named'. See DB.paramstyle()

        @type statement:  string
        @param statement: the SQL statement to execute

        @type parameters:  list
        @param parameters: parameters to use, if the statement is
                           parameterized

        @raise Warning: Non-fatal warning
        @raise Error:   Error
        """
        dbi = self.__driver.get_import()
        try:
            result = self.__cursor.execute(statement, parameters)
            self.__rowcount = self.__cursor.rowcount
            self.__description = self.__cursor.description
            return result
        except dbi.Warning, val:
            raise Warning(val)
        except dbi.Error, val:
            raise Error(val)

    def executemany(self, statement, *parameters):
        """
        Execute a SQL statement once for each item in the given parameters.

        @type statement:  string
        @param statement: SQL statement to be executed

        @type parameters:  sequence
        @param parameters: a sequence of sequences when the parameter style
                           is 'format', 'numeric' or 'qmark', and a sequence
                           of dictionaries when the style is 'pyformat' or
                           'named'.

        @raise Warning: Non-fatal warning
        @raise Error:   Error
        """
        dbi = self.__driver.get_import()
        try:
            result = self.__cursor.executemany(statement, *parameters)
            self.__rowcount = self.__cursor.rowcount
            self.__description = self.__cursor.description
            return result
        except dbi.Warning, val:
            raise Warning(val)
        except dbi.Error, val:
            raise Error(val)

    executeMany = executemany

    def fetchone(self):
        """
        Returns the next result set row from the last query, as a sequence
        of tuples. Raises an exception if the last statement was not a query.

        @rtype:  tuple
        @return: Next result set row

        @raise Warning: Non-fatal warning
        @raise Error:   Error
        """
        dbi = self.__driver.get_import()
        try:
            return self.__cursor.fetchone()
        except dbi.Warning, val:
            raise Warning(val)
        except dbi.Error, val:
            raise Error(val)

    def fetchall(self):
        """
        Returns all remaining result rows from the last query, as a sequence
        of tuples. Raises an exception if the last statement was not a query.

        @rtype:  list of tuples
        @return: List of rows, each represented as a tuple

        @raise Warning: Non-fatal warning
        @raise Error:   Error
        """
        dbi = self.__driver.get_import()
        try:
            return self.__cursor.fetchall()
        except dbi.Warning, val:
            raise Warning(val)
        except dbi.Error, val:
            raise Error(val)

    fetchAll = fetchall

    def fetchmany(self, n):
        """
        Returns up to n remaining result rows from the last query, as a
        sequence of tuples. Raises an exception if the last statement was
        not a query.

        @type n:  int
        @param n: maximum number of result rows to get

        @rtype:  list of tuples
        @return: List of rows, each represented as a tuple

        @raise Warning: Non-fatal warning
        @raise Error:   Error
        """
        dbi = self.__driver.get_import()
        try:
            self.__cursor.fetchmany(n)
        except dbi.Warning, val:
            raise Warning(val)
        except dbi.Error, val:
            raise Error(val)

    fetchMany = fetchmany

    @deprecated(since='0.4', message='Use get_table_metadata')
    def get_table_metadata(self, table):
        return self.get_table_metadata(table)

    def get_table_metadata(self, table):
        """
        Get the metadata for a table. Returns a list of tuples, one for
        each column. Each tuple consists of the following::

           (column_name, type_string, max_char_size, precision, scale, nullable)

        The tuple elements have the following meanings.

         - B{C{column_name}}: the name of the column
         - B{C{type_string}}: the column type, as a string
         - B{C{max_char_size}}: maximum size for a character field, or C{None}
         - B{C{precision}}: precision, for a numeric field, or C{None}
         - B{C{scale}}: scale, for a numeric field, or C{None}
         - B{C{nullable}}: C{True} or C{False}

        The data may come from the DB API's C{cursor.description} field, or
        it may be richer, coming from a direct SELECT against
        database-specific tables.

        This default implementation uses the DB API's C{cursor.description}
        field. Subclasses are free to override this method to produce their
        own version that uses other means.

        @raise Warning: Non-fatal warning
        @raise Error:   Error
        """
        # Default implementation
        dbi = self.__driver.get_import()
        try:
            return self.__driver.get_table_metadata(table, self.__cursor)
        except dbi.Warning, val:
            raise Warning(val)
        except dbi.Error, val:
            raise Error(val)

    @deprecated(since='0.4', message='Use get_index_metadata')
    def get_index_metadata(self, table):
        return self.get_index_metadata(table)

    def get_index_metadata(self, table):
        """
        Get the metadata for the indexes for a table. Returns a list of
        tuples, one for each index. Each tuple consists of the following::

            (index_name, [index_columns], description)

        The tuple elements have the following meanings.

         - B{C{index_name}}: the index name
         - B{C{index_columns}}: a list of column names
         - B{C{description}}: index description, or C{None}

        @rtype:  list of tuples
        @return: the list of tuples, or C{None} if not supported in the
                 underlying database

        @raise Warning: Non-fatal warning
        @raise Error:   Error
        """
        dbi = self.__driver.get_import()
        try:
            return self.__driver.get_index_metadata(table, self.__cursor)
        except dbi.Warning, val:
            raise Warning(val)
        except dbi.Error, val:
            raise Error(val)

class DB(object):
    """
    The object returned by a call to C{DBDriver.connect()}. C{DB} wraps the
    real database object returned by the underlying Python DB API module's
    C{connect()} method.
    """
    def __init__(self, db, driver):
        """
        Create a new DB object.

        @param db: the underlying Python DB API database object

        @type driver:  C{DBDriver}
        @param driver: the driver (i.e., the subclass of DBDriver) that
                       created the 'db' object
        """
        self.__db = db
        self.__driver = driver
        dbi = driver.get_import()
        for attr in ['BINARY', 'NUMBER', 'STRING', 'DATETIME', 'ROWID']:
            try:
                exec 'self.%s = dbi.%s' % (attr, attr)
            except AttributeError:
                exec 'self.%s = 0' % attr

    def paramstyle(self):
        """
        Get the parameter style for the underlying DB API module. The
        result of this method call corresponds exactly to the underlying
        DB API module's 'paramstyle' attribute. It will have one of the
        following values:

        'format'

        The parameter marker is '%s', as in string formatting.
        A query looks like this::

            c.execute('SELECT * FROM Foo WHERE Bar=%s', [x])

        'named'

        The parameter marker is :name, and parameters are named.
        A query looks like this::

            c.execute('SELECT * FROM Foo WHERE Bar=:x', {'x':x})

        'numeric'

        The parameter marker is :n, giving the parameter's number
        (starting at 1). A query looks like this::

            c.execute('SELECT * FROM Foo WHERE Bar=:1', [x])

        'pyformat'

        The parameter marker is %(name)s, and parameters are named. A query
        looks like this::

            c.execute('SELECT * FROM Foo WHERE Bar=%(x)s', {'x':x})

        'qmark'

        The parameter is ?. A query looks like this::

            c.execute('SELECT * FROM Foo WHERE Bar=?', [x])
        """

    def Binary(self, string):
        """
        Returns an object representing the given string of bytes as a BLOB.

        This method is equivalent to the module-level C{Binary()} method in
        an underlying DB API-compliant module.

        @type string:  str
        @param string: the string to convert to a BLOB

        @rtype:  object
        @return: the corresponding BLOB
        """
        return self.__driver.get_import().Binary(string)

    def Date(self, year, month, day):
        """
        Returns an object representing the specified date.

        This method is equivalent to the module-level C{Date()} method in
        an underlying DB API-compliant module.

        @param year:  the year
        @param month: the month
        @param day:   the day of the month

        @return: an object containing the date
        """
        return self.__driver.get_import().Date(year, month, day)

    def DateFromTicks(self, secs):
        """
        Returns an object representing the date I{secs} seconds after the
        epoch. For example::

            import time

            d = db.DateFromTicks(time.time())

        This method is equivalent to the module-level C{DateFromTicks()}
        method in an underlying DB API-compliant module.

        @type secs:  int
        @param secs: the seconds from the epoch

        @return: an object containing the date
        """
        return self.__driver.get_import().Date(year, month, day)

    def Time(self, hour, minute, second):
        """
        Returns an object representing the specified time.

        This method is equivalent to the module-level C{Time()} method in an
        underlying DB API-compliant module.

        @param hour:    the hour of the day
        @param minute:  the minute within the hour. 0 <= C{minute} <= 59
        @param second:  the second within the minute. 0 <= C{second} <= 59

        @return: an object containing the time
        """
        return self.__driver.get_import().Time(hour, minute, second)

    def TimeFromTicks(self, secs):
        """
        Returns an object representing the time 'secs' seconds after the
        epoch. For example::

            import time

            d = db.TimeFromTicks(time.time())

        This method is equivalent to the module-level TimeFromTicks()
        method in an underlying DB API-compliant module.

        @type secs:  int
        @param secs: the seconds from the epoch

        @return: an object containing the time
        """
        return self.__driver.get_import().Date(year, month, day)

    def Timestamp(self, year, month, day, hour, minute, second):
        """
        Returns an object representing the specified time.

        This method is equivalent to the module-level C{Timestamp()} method
        in an underlying DB API-compliant module.

        @param year:  the year
        @param month: the month
        @param day:   the day of the month
        @param hour:    the hour of the day
        @param minute:  the minute within the hour. 0 <= C{minute} <= 59
        @param second:  the second within the minute. 0 <= C{second} <= 59

        @return: an object containing the timestamp
        """
        return self.__driver.get_import().Timestamp(year, month, day,
                                                   hour, minute, second)

    def TimestampFromTicks(self, secs):
        """
        Returns an object representing the date and time 'secs' seconds
        after the epoch. For example::

            import time

            d = db.TimestampFromTicks(time.time())

        This method is equivalent to the module-level TimestampFromTicks()
        method in an underlying DB API-compliant module.

        @type secs:  int
        @param secs: the seconds from the epoch

        @return: an object containing the timestamp
        """
        return self.__driver.get_import().Date(year, month, day)

    def cursor(self):
        """
        Get a cursor suitable for accessing the database. The returned object
        conforms to the Python DB API cursor interface.

        @return: the cursor

        @raise Warning: Non-fatal warning
        @raise Error:   Error
        """
        dbi = self.__driver.get_import()
        try:
            return Cursor(self.__db.cursor(), self.__driver)
        except dbi.Warning, val:
            raise Warning(val)
        except dbi.Error, val:
            raise Error(val)

    def commit(self):
        """
        Commit the current transaction.

        @raise Warning: Non-fatal warning
        @raise Error:   Error
        """
        dbi = self.__driver.get_import()
        try:
            self.__db.commit()
        except dbi.Warning, val:
            raise Warning(val)
        except dbi.Error, val:
            raise Error(val)

    def rollback(self):
        """
        Roll the current transaction back.

        @raise Warning: Non-fatal warning
        @raise Error:   Error
        """
        dbi = self.__driver.get_import()
        try:
            self.__db.rollback()
        except dbi.Warning, val:
            raise Warning(val)
        except dbi.Error, val:
            raise Error(val)

    def close(self):
        """
        Close the database connection.

        @raise Warning: Non-fatal warning
        @raise Error:   Error
        """
        dbi = self.__driver.get_import()
        try:
            self.__db.close()
        except dbi.Warning, val:
            raise Warning(val)
        except dbi.Error, val:
            raise Error(val)

class DBDriver(object):
    """
    Base class for all DB drivers.
    """

    @abstract
    def get_import(self):
        """
        Get a bound import for the underlying DB API module. All subclasses
        must provide an implementation of this method. Here's an example,
        assuming the real underlying Python DB API module is 'foosql'::

            def get_import(self):
                import foosql
                return foosql

        @return: a bound module
        """
        pass

    def __display_name(self):
        return self.get_display_name()

    @abstract
    def get_display_name(self):
        """
        Get the driver's name, for display. The returned name ought to be
        a reasonable identifier for the database (e.g., 'SQL Server',
        'MySQL'). All subclasses must provide an implementation of this
        method.

        @rtype:  str
        @return: the driver's displayable name
        """
        pass

    display_name = property(__display_name,
                            doc='get a displayable name for the driver')
    def connect(self,
                host='localhost',
                port=None,
                user=None,
                password='',
                database=None):
        """
        Connect to the underlying database. Subclasses should I{not}
        override this method. Instead, a subclass should override the
        L{C{do_connect()}<do_connect>} method.

        @type host:      str
        @param host:     the host where the database lives

        @type port:      int
        @param port:     the TCP port to use when connecting

        @type user:      str
        @param user:     the user to use when connecting

        @type password:  str
        @param password: the user to use when connecting

        @type database:  str
        @param database: the database to which to connect

        @rtype:  C{DB}
        @return: a C{DB} object representing the open database

        @raise Warning: Non-fatal warning
        @raise Error:   Error
        """
        dbi = self.get_import()
        try:
            self.__db = self.do_connect(host=host,
                                       port=port,
                                       user=user,
                                       password=password,
                                       database=database)
            return DB(self.__db, self)
        except dbi.Warning, val:
            raise Warning(val)
        except dbi.Error, val:
            raise Error(val)

    @abstract
    def do_connect(self,
                   host='localhost',
                   port=None,
                   user='',
                   password='',
                   database='default'):
        """
        Connect to the actual underlying database, using the driver.
        Subclasses must provide an implementation of this method. The
        method must return the result of the real DB API implementation's
        C{connect()} method. For instance::

            def do_connect():
                dbi = self.get_import()
                return dbi.connect(host=host, user=user, passwd=password,
                                   database=database)

        There is no need to catch exceptions; the C{DBDriver} class's
        C{connect()} method handles that.

        @type host:      str
        @param host:     the host where the database lives

        @type port:      int
        @param port:     the TCP port to use when connecting

        @type user:      str
        @param user:     the user to use when connecting

        @type password:  str
        @param password: the user to use when connecting

        @type database:  str
        @param database: the database to which to connect

        @rtype:  C{DB}
        @return: a C{DB} object representing the open database

        @raise Warning: Non-fatal warning
        @raise Error:   Error
        """
        pass

    def get_index_metadata(self, table, cursor):
        """
        Get the metadata for the indexes for a table. Returns a list of
        tuples, one for each index. Each tuple consists of the following::

            (indexName, [indexColumns], description)

        The tuple elements have the following meanings.

         - B{C{indexName}}: the index name
         - B{C{indexKeys}}: a list of column names
         - B{C{description}}: index description, or C{None}

        The default implementation of this method returns C{None}.

        @type table:  str
        @param table: table name

        @type cursor:  L{C{Cursor}<Cursor>}
        @param cursor: a C{Cursor} object from a recent query

        @rtype:  list of tuples
        @return: the list of tuples, or C{None} if not supported in the
                 underlying database

        @raise Warning: Non-fatal warning
        """
        return None

    def get_table_metadata(self, table, cursor):
        """
        Get the metadata for a table. Returns a list of tuples, one for
        each column. Each tuple consists of the following::

           (columnName, TypeString, maxCharSize, precision, scale, nullable)

        The tuple elements have the following meanings.

         - B{C{columnName}}: the name of the column
         - B{C{typeAsString}}: the column type, as a string
         - B{C{maxCharSize}}: maximum size for a character field, or C{None}
         - B{C{precision}}: precision, for a numeric field, or C{None}
         - B{C{scale}}: scale, for a numeric field, or C{None}
         - B{C{nullable}}: C{True} or C{False}

        The data may come from the DB API's C{cursor.description} field, or
        it may be richer, coming from a direct SELECT against
        database-specific tables.

        This default implementation uses the DB API's C{cursor.description}
        field. Subclasses are free to override this method to produce their
        own version that uses other means.

        @type table:  str
        @param table: table name

        @type cursor:  L{C{Cursor}<Cursor>}
        @param cursor: a C{Cursor} object from a recent query

        @raise Warning: Non-fatal warning
        @raise Error:   Error
        """
        dbi = self.get_import()
        cursor.execute('SELECT * FROM %s WHERE 1=0' % table)
        result = []
        for col in cursor.description:
            name = col[0]
            type = col[1]
            size = col[2]
            internalSize = col[3]
            precision = col[4]
            scale = col[5]
            nullable = col[6]

            sType = None
            try:
                if type == dbi.BINARY:
                    stype = 'blob'
                elif type == dbi.DATETIME:
                    stype = 'datetime'
                elif type == dbi.NUMBER:
                    stype = 'numeric'
                elif type == dbi.STRING:
                    sz = internalSize
                    if sz == None:
                        sz = size
                    elif sz <= 0:
                        sz = size

                    if sz == 1:
                        stype = 'char'
                    else:
                        stype = 'varchar'
                    size = sz
                elif type == dbi.ROWID:
                    stype = 'id'
            except AttributeError:
                stype = None

            if not sType:
                stype = 'unknown (type code=%s)' % str(type)

            result += [(name, stype, size, precision, scale, nullable)]

        return result

class MySQLDriver(DBDriver):
    """DB Driver for MySQL, using the MySQLdb DB API module."""

    def get_import(self):
        import MySQLdb
        return MySQLdb

    def get_display_name(self):
        return "MySQL"

    def do_connect(self,
                   host="localhost",
                   port=None,
                   user="sa",
                   password="",
                   database="default"):
        dbi = self.get_import()
        return dbi.connect(host=host, user=user, passwd=password, db=database)

    def get_index_metadata(self, table, cursor):
        dbi = self.get_import()
        cursor.execute('SHOW INDEX FROM %s' % table)
        rs = cursor.fetchone()
        result = []
        columns = {}
        descr = {}
        while rs != None:
            name = rs[2]
            try:
                columns[name]
            except KeyError:
                columns[name] = []

            columns[name] += [rs[4]]
            if rs[1] or (name.lower() == 'primary'):
                description = 'Unique'
            else:
                description = 'Non-unique'
            if rs[10] != None:
                description += ', %s index' % rs[10]
            descr[name] = description
            rs = cursor.fetchone()

        names = columns.keys()
        names.sort()
        for name in names:
            result += [(name, columns[name], descr[name])]

        return result

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
        if port == None:
            port = '1433'
        return dbi.connect(host='%s:%s' % (host, port),
                           user=user,
                           password=password,
                           database=database)

    def get_table_metadata(self, table, cursor):
        """Default implementation"""
        dbi = self.get_import()
        cursor.execute("SELECT column_name, data_type, " \
                       "character_maximum_length, numeric_precision, " \
                       "numeric_scale, is_nullable "\
                       "FROM information_schema.columns WHERE "\
                       "LOWER(table_name) = '%s'" % table)
        rs = cursor.fetchone()
        results = []
        while rs != None:
            is_nullable = False
            if rs[5] == 'YES':
                is_nullable = True
            results += [(rs[0], rs[1], rs[2], rs[3], rs[4], is_nullable)]
            rs = cursor.fetchone()
        return results

    def get_index_metadata(self, table, cursor):
        dbi = self.get_import()
        cursor.execute("EXEC sp_helpindex '%s'" % table)
        rs = cursor.fetchone()
        results_by_name = {}
        while rs != None:
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

class PostgreSQLDriver(DBDriver):
    """DB Driver for PostgreSQL, using the psycopg2 DB API module."""

    def get_import(self):
        import psycopg2
        return psycopg2

    def get_display_name(self):
        return "PostgreSQL"

    def do_connect(self,
                   host='localhost',
                   port=None,
                   user='',
                   password='',
                   database='default'):
        dbi = self.get_import()
        dsn = 'host=%s dbname=%s user=%s password=%s' %\
            (host, database, user, password)
        return dbi.connect(dsn=dsn)

    def get_index_metadata(self, table, cursor):
        dbi = self.get_import()
        # First, issue one query to get the list of indexes for the table.
        index_names = self.__getIndexNames(table, cursor)

        # Now we need two more queries: One to get the columns in the
        # index and another to get descriptive information.
        results = []
        for name in index_names:
            columns = self.__get_index_columns(name, cursor)
            desc = self.__get_index_description(name, cursor)
            results += [(name, columns, desc)]

        return results

    def __getIndexNames(self, table, cursor):
        # Adapted from the pgsql command "\d indexname", PostgreSQL 8.
        # (Invoking the pgsql command from -E shows the issued SQL.)

        sel = "SELECT n.nspname, c.relname as \"IndexName\", c2.relname " \
            "FROM pg_catalog.pg_class c " \
            "JOIN pg_catalog.pg_index i ON i.indexrelid = c.oid " \
            "JOIN pg_catalog.pg_class c2 ON i.indrelid = c2.oid " \
            "LEFT JOIN pg_catalog.pg_user u ON u.usesysid = c.relowner " \
            "LEFT JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace " \
            "WHERE c.relkind IN ('i','') " \
            "AND n.nspname NOT IN ('pg_catalog', 'pg_toast') " \
            "AND pg_catalog.pg_table_is_visible(c.oid) " \
            "AND c2.relname = '%s'" % table.lower()

        cursor.execute(sel)
        index_names = []
        rs = cursor.fetchone()
        while rs != None:
            index_names += [rs[1]]
            rs = cursor.fetchone()

        return index_names

    def __get_index_columns(self, index_name, cursor):
        # Adapted from the pgsql command "\d indexname", PostgreSQL 8.
        # (Invoking the pgsql command from -E shows the issued SQL.)

        sel = "SELECT a.attname, " \
            "pg_catalog.format_type(a.atttypid, a.atttypmod), " \
            "a.attnotnull " \
            "FROM pg_catalog.pg_attribute a, pg_catalog.pg_index i " \
            "WHERE a.attrelid in " \
            " (SELECT c.oid FROM pg_catalog.pg_class c " \
            "LEFT JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace " \
            " WHERE pg_catalog.pg_table_is_visible(c.oid) " \
            "AND c.relname ~ '^(%s)$') " \
            "AND a.attnum > 0 AND NOT a.attisdropped " \
            "AND a.attrelid = i.indexrelid " \
            "ORDER BY a.attnum" % index_name
        cursor.execute(sel)
        columns = []
        rs = cursor.fetchone()
        while rs != None:
            columns += [rs[0]]
            rs = cursor.fetchone()

        return columns

    def __get_index_description(self, index_name, cursor):
        sel = "SELECT i.indisunique, i.indisprimary, i.indisclustered, " \
            "a.amname, c2.relname, " \
            "pg_catalog.pg_get_expr(i.indpred, i.indrelid, true) " \
            "FROM pg_catalog.pg_index i, pg_catalog.pg_class c, " \
            "pg_catalog.pg_class c2, pg_catalog.pg_am a " \
            "WHERE i.indexrelid = c.oid AND c.relname ~ '^(%s)$' " \
            "AND c.relam = a.oid AND i.indrelid = c2.oid" % index_name
        cursor.execute(sel)
        desc = ''
        rs = cursor.fetchone()
        if rs != None:
            if str(rs[1]) == "True":
                desc += "(PRIMARY) "

            if str(rs[0]) == "True":
                desc += "Unique"
            else:
                desc += "Non-unique"

            if str(rs[2]) == "True":
                desc += ", clustered"
            else:
                desc += ", non-clustered"

            if rs[3] != None:
                desc += " %s" % rs[3]

            desc += ' index'

        if desc == '':
            desc = None

        return desc

class OracleDriver(DBDriver):
    """DB Driver for Oracle, using the cx_Oracle DB API module."""

    def get_import(self):
        import cx_Oracle
        return cx_Oracle

    def get_display_name(self):
        return "Oracle"

    def do_connect(self,
                   host='localhost',
                   port=None,
                   user='',
                   password='',
                   database='default'):
        dbi = self.get_import()
        return dbi.connect('%s/%s@%s' % (user, password, database))

class SQLite3Driver(DBDriver):
    """DB Driver for Oracle, using the cx_Oracle DB API module."""

    def get_import(self):
        import sqlite3
        return sqlite3

    def get_display_name(self):
        return "SQLite3"

    def do_connect(self,
                   host=None,
                   port=None,
                   user='',
                   password='',
                   database='default'):
        dbi = self.get_import()
        return dbi.connect(database=database)

class DummyDriver(DBDriver):
    """Dummy database driver, for testing."""

    def get_import(self):
        import dummydb
        return dummydb

    def get_display_name(self):
        return "Dummy"

    def do_connect(self,
                   host="localhost",
                   port=None,
                   user='',
                   password='',
                   database='default'):
        return dummydb.DummyDB()
