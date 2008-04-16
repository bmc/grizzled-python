#!/usr/bin/env python
#
# $Id$
# ---------------------------------------------------------------------------

"""
Provides a front-end to the Python standard C{optparse} module. The
C{CommandLineParser} class makes two changes to the standard behavior.

  - The output for the '-h' option is slightly different.
  - A bad option causes the parser to generate the entire usage output,
    not just an error message.

It also provides a couple extra utility modules.
"""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

from optparse import OptionParser
import sys

# ---------------------------------------------------------------------------
# Exports
# ---------------------------------------------------------------------------

__all__ = ['CommandLineParser']

# ---------------------------------------------------------------------------
# Classes
# ---------------------------------------------------------------------------

class CommandLineParser(OptionParser):
    """Custom version of command line option parser."""

    def __init__(self, *args, **kw):
        """ Create a new instance. """

        OptionParser.__init__(self, *args, **kw)

        # I like my help option message better than the default...

        self.remove_option('-h')
        self.add_option('-h', '--help', action='help',
                        help='Show this message and exit.')

    def addOption(self, *args, **kw):
        """
        Front-end to C{add_option()}. Exists solely for Camel-case
        consistency.
        """
        return self.add_option(*args, **kw)

    def addOptions(self, optionList):
        """
        Front-end to C{add_option()}. Exists solely for Camel-case
        consistency.
        """
        return self.add_options(optionList)

    def parseArgs(self, args):
        """
        Front-end to C{parse_args()}. Exists solely for Camel-case
        consistency.
        """
        return self.parse_args(args)

    def showUsage(self, msg=None):
        """
        Force the display of the usage message.

        @type msg:  string
        @param msg: If not set the None (the default), this message will
                    be displayed before the usage message.
        """
        if msg != None:
            print >> sys.stderr, msg
        self.print_help(sys.stderr)
        sys.exit(2)

    def error(self, msg):
        """
        Overrides parent C{OptionParser} class's C{error} message and
        forces the full usage message on error.
        """
        sys.stderr.write("%s: error: %s\n" % (self.get_prog_name(), msg))
        self.showUsage()

