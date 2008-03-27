# $Id$

'''
Introduction
============

Based on the standard Python C{ConfigParser} module, this module provides
an enhanced configuration parser capabilities. C{Configuration} is a drop-in
replacement for C{ConfigParser}.

A configuration file is broken into sections, and each section is
introduced by a section name in brackets. For example::

    [main]
    installationDirectory=/usr/local/foo
    programDirectory: /usr/local/foo/programs

    [search]
    searchCommand: find /usr/local/foo -type f -name "*.class"

    [display]
    searchFailedMessage=Search failed, sorry.


Section Name Syntax
===================

A section name can consist of alphabetics, numerics, underscores and
periods. There can be any amount of whitespace before and after the
brackets in a section name; the whitespace is ignored.

Variable Syntax
===============

Each section contains zero or more variable settings.

 - Similar to a Java C{Properties} file, the variables are specified as
   name/value pairs, separated by an equal sign ("=") or a colon (":").
 - Variable names are case-sensitive and may contain alphabetics, numerics,
   underscores and periods (".").
 - Variable values may contain anything at all. Leading whitespace in the
   value is skipped. The way to include leading whitespace in a value is
   escape the whitespace characters with backslashes.

Variable Substitution
=====================

A variable value can interpolate the values of other variables, using a
variable substitution syntax. The general form of a variable reference is
C{$E{lb}sectionName:varNameE{rb}}.

  - I{sectionName} is the name of the section containing the variable to
    substitute; if omitted, it defaults to the current section.
  - I{varName} is the name of the variable to substitute.

Default values
--------------

You can also specify a default value for a variable, using this syntax::

    ${foo?default}
    ${section:foo?default}

That is, the sequence "C{?default}" after a variable name specifies the
default value if the variable has no value. (Normally, if a variable has
no value, it is replaced with an empty string.) Defaults can be useful,
for instance, to allow overrides from the environment. The following example
defines a log file directory that defaults to "/tmp", unless environment
variable LOGDIR is set to a non-empty value::

    logDirectory: ${env:LOGDIR?/var/log}

Special section names
---------------------

The section names "env", and "program" are reserved for special
pseudosections.

The C{env} pseudosection
~~~~~~~~~~~~~~~~~~~~~~~~

The "env" pseudosection is used to interpolate values from the environment.
On UNIX systems, for instance, C{$E{lb}env:HOMEE{rb}} substitutes home
directory of the current user. On some versions of Windows,
C{$E{lb}env:USERNAMEE{rb}} will substitute the name of the user.

Note: On UNIX systems, environment variable names are typically
case-sensitive; for instance, C{$E{lb}env:USERE{rb}} and
C{$E{lb}env:userE{rb}} refer to different environment variables. On Windows
systems, environment variable names are typically case-insensitive;
C{$E{lb}env:USERNAMEE{rb}} C{$E{lb}env:usernameE{rb}} are equivalent.

The C{program} pseudosection
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The "program" pseudosection is a placeholder for various special variables
provided by the Configuration class. Those variables are:

  - B{C{cwd}}: The current working directory. Thus, C{$E{lb}program:cwdE{rb}}
    will substitute the working directory, using the appropriate system-specific
    file separator (e.g., "/" on Unix, "\\" on Windows).
  - B{C{name}}: The calling program name. Equivalent to the Python expression
    C{os.path.basename(sys.argv[0])}
  - B{C{now}}: The current time, formatted using the C{time.strftime()} format
    C{"%Y-%m-%d %H:%M:%S"} (e.g., "2008-03-03 16:15:27")

Includes
--------

A special include directive permits inline inclusion of another
configuration file. The include directive takes two forms::

    %include "path"
    %include "URL"

For example::

    %include "/home/bmc/mytools/common.cfg"
    %include "http://configs.example.com/mytools/common.cfg"

The included file may contain any content that is valid for this parser. It
may contain just variable definitions (i.e., the contents of a section,
without the section header), or it may contain a complete configuration
file, with individual sections.

Note: Attempting to include a file from itself, either directly or
indirectly, will cause the parser to throw an exception.

Replacing C{ConfigParser}
=========================

You can use this class anywhere you would use the standard Python
C{ConfigParser} class. Thus, to change a piece of code to use enhanced
configuration, you might change this::

    import ConfigParser

    config = ConfigParser.SafeConfigParser()
    config.read(configPath)

to this::

    from grizzled.config import Configuration

    config = Configuration()
    config.read(configPath)


Sometimes, however, you have to use an API that expects a path to a
configuration file that can I{only} be parsed with the (unenhanced)
C{ConfigParser} class. In that case, you simply use the
L{C{preprocess()}<preprocess>} method::

    import logging
    from grizzled import config

    logging.config.fileConfig(config.preprocess(pathToConfig))
'''

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

import ConfigParser
import logging
import string
import os
import time
import sys
import re

from grizzled.exception import ExceptionWithMessage

__all__ = ['Configuration', 'preprocess',
           'NoOptionError', 'NoSectionError', 'NoVariableError']

# ---------------------------------------------------------------------------
# Globals
# ---------------------------------------------------------------------------

log = logging.getLogger('grizzled.config')
NoOptionError = ConfigParser.NoOptionError
NoSectionError = ConfigParser.NoSectionError

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Used with _ConfigDict

SECTION_OPTION_DELIM = r':'

# Section name pattern
SECTION_NAME_PATTERN = r'([_.a-zA-Z][_.a-zA-Z0-9]+)'

# Pattern of an identifier local to a section.
VARIABLE_NAME_PATTERN = r'([_a-zA-Z][_a-zA-Z0-9]+)(\?[^}]+)?'

# Pattern of an identifier matched by our version of string.Template.
# Intended to match:
#
#     ${section:option}         variable 'option' in section 'section'
#     ${section:option?default} variable 'option' in section 'section', default
#                               value 'default'
#     ${option}                 variable 'option' in the current section
#     ${option?default}         variable 'option' in the current section,
#                               default value 'default'
VARIABLE_REF_PATTERN = SECTION_NAME_PATTERN + SECTION_OPTION_DELIM +\
                       VARIABLE_NAME_PATTERN +\
                       r'|' +\
                       VARIABLE_NAME_PATTERN

# Simple variable reference
SIMPLE_VARIABLE_REF_PATTERN = r'\$\{' + VARIABLE_NAME_PATTERN + '\}'

# Special sections
ENV_SECTION = 'env'
PROGRAM_SECTION = 'program'

# ---------------------------------------------------------------------------
# Classes
# ---------------------------------------------------------------------------

# Use odict if it's available. Otherwise, use a simpler mock-up.
try:
    from odict import OrderedDict as _SectionDict

except ImportError:
    class _SectionDict(dict):
        def __init__(self):
            self.__orderedKeys = []
            dict.__init__(self)

        def __setitem__(self, key, value):
            if not (key in self.__orderedKeys):
                self.__orderedKeys += [key]
            return dict.__setitem__(self, key, value)

        def keys(self):
            return self.__orderedKeys


class NoVariableError(ExceptionWithMessage):
    """
    Thrown when a configuration file attempts to substitute a nonexistent
    variable, and the C{Configuration} object was instantiated with
    C{strictSubstitution} set to C{True}.
    """
    pass

class Configuration(ConfigParser.SafeConfigParser):
    """
    Configuration file parser. See the module documentation for details.
    """

    def __init__(self,
                 defaults=None,
                 permitIncludes=True,
                 useOrderedSections=False,
                 strictSubstitution=False):
        """
        Construct a new C{Configuration} object.

        @type defaults:  dict
        @param defaults: dictionary of default values

        @type permitIncludes:  boolean
        @param permitIncludes: whether or not to permit includes

        @type useOrderedSections:  boolean
        @param useOrderedSections: whether or not to use an ordered dictionary
                                   for the section names. If C{True}, then
                                   a call to L{C{sections()}<sections>} will
                                   return the sections in the order they were
                                   encountered in the file. If C{False}, the
                                   order is based on the hash keys for the
                                   sections' names.

        @type strictSubstitution:  boolean
        @param strictSubstitution: If C{true}, then throw an exception if
                                   attempting to substitute a non-existent
                                   variable. Otherwise, simple substitute an
                                   empty value.
        """
        ConfigParser.SafeConfigParser.__init__(self, defaults)
        self.__permitIncludes = permitIncludes
        self.__useOrderedSections = useOrderedSections
        self.__strictSubstitution = strictSubstitution

        if useOrderedSections:
            self._sections = _SectionDict()

    def defaults(self):
        """
        Returns the instance-wide defaults.

        @rtype:  dictionary
        @return: the instance-wide defaults, or None if there aren't any
        """
        return ConfigParser.SafeConfigParser.defaults(self)

    def sections(self):
        """
        Get the list of available sections, not include C{DEFAULT}.
        It's not really useful to call this method before calling
        L{C{read()}<read>} or L{C{readfp()}<readfp>}.

        @rtype:  list
        @return: list of available sections, or None
        """
        return ConfigParser.SafeConfigParser.sections(self)

    def add_section(self, section):
        """
        Add a section named I{section} to the instance. If a section by the
        given name already exists, C{DuplicateSectionError} is raised. 

        Also callable as L{C{addSection()}<addSection>}. This version of
        the function exists for compatibility with C{ConfigParser}; it
        simply calls L{C{addSection()}<addSection>}.

        @type section:  string
        @param section: name of section to add

        @raise DuplicateSectionError: section already exists
        """
        ConfigParser.SafeConfigParser.add_section(self, section)

    def addSection(self, section):
        """
        Add a section named I{section} to the instance. If a section by the
        given name already exists, C{DuplicateSectionError} is raised.

        @type section:  string
        @param section: name of section to add

        @raise DuplicateSectionError: section already exists
        """
        self.add_section(section)

    def has_section(self, section):
        """
        Determine whether a section exists in the configuration. Ignores
        the C{DEFAULT} section.

        Also callable as L{C{hasSection()}<hasSection>}. This version of
        the function exists for compatibility with C{ConfigParser}; it
        simply calls L{C{hasSection()}<hasSection>}.

        @type section:  string
        @param section: name of section

        @rtype:  boolean
        @return: C{True} if the section exists in the configuration, C{False}
                 if not.
        """
        return self.hasSection(section)

    def hasSection(self, section):
        """
        Determine whether a section exists in the configuration. Ignores
        the C{DEFAULT} section.

        @type section:  string
        @param section: name of section

        @rtype:  boolean
        @return: C{True} if the section exists in the configuration, C{False}
                 if not.
        """
        return ConfigParser.SafeConfigParser.has_section(self, section)

    def options(self, section):
        """
        Get a list of options available in the specified section.

        @type section:  string
        @param section: name of section

        @rtype:  list
        @return: list of available options. May be empty.

        @raise ConfigParser.NoSectionError: no such section
        """
        return ConfigParser.SafeConfigParser.options(self, section)

    def has_option(self, section, option):
        """
        Determine whether a section has a specific option.

        Also callable as L{C{hasOption()}<hasOption>}. This version of
        the function exists for compatibility with C{ConfigParser}; it
        simply calls L{C{hasOption()}<hasOption>}.

        @type section:  string
        @param section: name of section

        @type option:   string
        @param option:  option to check

        @rtype:  boolean
        @return: C{True} if the section exists in the configuration and
                 has the specified option, C{False} if not.
        """
        return hasOption(section, option)

    def hasOption(self, section, option):
        """
        Determine whether a section exists in the configuration. Ignores
        the C{DEFAULT} section.

        @type section:  string
        @param section: name of section

        @rtype:  boolean
        @return: C{True} if the section exists in the configuration, C{False}
                 if not.
        """
        return ConfigParser.SafeConfigParser.has_option(self, section, option)

    def read(self, filenames):
        """
        Attempt to read and parse a list of filenames or URLs, returning a
        list of filenames or URLs which were successfully parsed. If
        I{filenames} is a string or Unicode string, it is treated as a
        single filename or URL. If a file or URL named in filenames cannot
        be opened, that file will be ignored. This is designed so that you
        can specify a list of potential configuration file locations (for
        example, the current directory, the user's home directory, and some
        system-wide directory), and all existing configuration files in the
        list will be read. If none of the named files exist, the
        C{Configuration} instance will contain an empty dataset. An
        application which requires initial values to be loaded from a file
        should load the required file or files using C{readfp()} before
        calling C{read()} for any optional files::

            import Configuration
            import os

            config = Configuration.Configuration()
            config.readfp(open('defaults.cfg'))
            config.read(['site.cfg', os.path.expanduser('~/.myapp.cfg')])

        @type filenames:  list or string
        @param filenames: list of file names or URLs, or string for one
                          filename or URL

        @rtype:  list
        @return: list of successfully parsed filenames or URLs
        """
        if isinstance(filenames, basestring):
            filenames = [filenames]

        newFilenames = []
        for filename in filenames:
            try:
                self.__preprocess(filename, filename)
                newFilenames += [filename]
            except IOError:
                log.exception('Error reading "%s"' % filename)

        return newFilenames

    def readfp(self, fp, filename=None):
        '''
        Read and parse configuration data from a file or file-like object.
        (Only the C{readline()} moethod is used.)

        @type fp:        fp
        @param fp:       File-like object with a C{readline()} method

        @type filename:  string
        @param filename: Name associated with C{fp}, for error messages.
                         If omitted or C{None}, then C{fp.name} is used.
                         If C{fp} has no C{name} attribute, then
                         C{"<???">} is used.
        '''
        self.__preprocess(fp, filename)

    def get(self, section, option, optional=False):
        """
        Get an option from a section.

        @type section:  string
        @param section: name of section

        @type option:   string
        @param option:  name of option

        @type optional:  boolean
        @param optional: C{True} to return None if the option doesn't
                         exist. C{False} to throw an exception if the option
                         doesn't exist.

        @rtype:  string
        @return: the option

        @raise ConfigParser.NoSectionError: no such section
        @raise ConfigParser.NoOptionError:  no such option in the section
        """
        def doGet(section, option):
            val = ConfigParser.SafeConfigParser.get(self, section, option)
            if len(val.strip()) == 0:
                raise ConfigParser.NoOptionError(option, section)
            return val

        if optional:
            return self.__getOptional(doGet, section, option)
        else:
            return doGet(section, option)

    def getint(self, section, option, optional=False):
        """
        Convenience method that coerces the result of a call to
        L{C{get()}<get>} to an C{int}.

        @type section:  string
        @param section: name of section

        @type option:   string
        @param option:  name of option

        @type optional:  boolean
        @param optional: C{True} to return None if the option doesn't
                         exist. C{False} to throw an exception if the option
                         doesn't exist.

        @rtype:  int
        @return: the option value

        @raise ConfigParser.NoSectionError: no such section
        @raise ConfigParser.NoOptionError:  no such option in the section
        """
        def doGet(section, option):
            return ConfigParser.SafeConfigParser.getint(self, section, option)

        if optional:
            return self.__getOptional(doGet, section, option)
        else:
            return doGet(section, option)

    def getfloat(self, section, option, optional=False):
        """
        Convenience method that coerces the result of a call to
        L{C{get()}<get>} to a C{float}.

        @type section:  string
        @param section: name of section

        @type optional:  boolean
        @param optional: C{True} to return None if the option doesn't
                         exist. C{False} to throw an exception if the option
                         doesn't exist.

        @type option:   string
        @param option:  name of option

        @rtype:  float
        @return: the option value

        @raise ConfigParser.NoSectionError: no such section
        @raise ConfigParser.NoOptionError:  no such option in the section
        """
        def doGet(section, option):
            return ConfigParser.SafeConfigParser.getfloat(self, section, option)

        if optional:
            return self.__getOptional(doGet, section, option)
        else:
            return doGet(section, option)

    def getboolean(self, section, option, optional=False):
        '''
        Convenience method that coerces the result of a call to
        L{C{get()}<get>} to a boolean. Accepted boolean values are "1",
        "yes", "true", and "on", which cause this method to return True,
        and "0", "no", "false", and "off", which cause it to return False.
        These string values are checked in a case-insensitive manner. Any
        other value will cause it to raise C{ValueError}.

        @type section:  string
        @param section: name of section

        @type option:   string
        @param option:  name of option

        @type optional:  boolean
        @param optional: C{True} to return None if the option does not
                         exist. C{False} to throw an exception if the option
                         does not exist.

        @rtype:  boolean
        @return: the option value (C{True} or C{False})

        @raise ConfigParser.NoSectionError: no such section
        @raise ConfigParser.NoOptionError: no such option in the section
        @raise ValueError: non-boolean value encountered
        '''
        def doGet(section, option):
            return ConfigParser.SafeConfigParser.getboolean(self,
                                                            section,
                                                            option)

        if optional:
            return self.__getOptional(doGet, section, option)
        else:
            return doGet(section, option)

    def getlist(self, section, option, sep=None, optional=False):
        '''
        Convenience method that coerces the result of a call to
        L{C{get()}<get>} to a list. The value is split using the
        separator(s) specified by the C{sep} argument. A C{sep} value
        of C{None} uses white space. The result is a list of string values.

        @type section:  string
        @param section: name of section

        @type option:   string
        @param option:  name of option

        @type optional:  boolean
        @param optional: C{True} to return None if the option does not
                         exist. C{False} to throw an exception if the option
                         does not exist.

        @rtype:  list
        @return: the option value as a list, or C{None}

        @raise ConfigParser.NoSectionError: no such section
        @raise ConfigParser.NoOptionError: no such option in the section
        @raise ValueError: non-boolean value encountered
        '''
        def doGet(section, option):
            value = ConfigParser.SafeConfigParser.get(self, section, option)
            return value.split(sep)

        if optional:
            return self.__getOptional(doGet, section, option)
        else:
            return doGet(section, option)

    def items(self, section):
        """
        Get all items in a section.

        @type section:  string
        @param section: the section name

        @rtype:  list
        @return: a list of (I{name}, I{value}) tuples for each option in
                 in I{section}

        @raise ConfigParser.NoSectionError: no such section
        """
        return ConfigParser.SafeConfigParser.items(self, section)

    def set(self, section, option, value):
        """
        If the given section exists, set the given option to the specified
        value; otherwise raise C{NoSectionError}.

        @type section:  string
        @param section: name of section

        @type option:   string
        @param option:  name of option

        @type value:    string
        @param value:   The value to set

        @raise ConfigParser.NoSectionError: no such section
        """
        ConfigParser.SafeConfigParser.set(self, section, option, value)

    def write(self, fileobj):
        """
        Write a representation of the configuration to the specified
        file-like object. This output can be parsed by a future
        C{read()} call.

        NOTE: Includes and variable references are I{not} reconstructed.
        That is, the configuration data is written in I{expanded} form.

        @type fileobj:  file-like object
        @param fileobj: where to write the configuration
        """
        ConfigParser.SafeConfigParser.write(self, fileobj)

    def remove_section(self, section):
        """
        Remove a section named I{section} from the instance. If a section by the
        given name does not exist, C{NoSectionError} is raised. 

        Also callable as L{C{removeSection()}<removeSection>}. This version of
        the function exists for compatibility with C{ConfigParser}; it
        simply calls L{C{removeSection()}<removeSection>}.

        @type section:  string
        @param section: name of section to remove

        @raise NoSectionError: no such section
        """
        self.removeSection(section)

    def removeSection(self, section):
        """
        Remove a section named I{section} from the instance. If a section
        by the given name does not exist, C{NoSectionError} is raised.

        @type section:  string
        @param section: name of section to remove

        @raise NoSectionError: no such section
        """
        ConfigParser.SafeConfigParser.remove_section(self, section)

    def optionxform(self, optionName):
        """
        Transforms the option name I{optionName} as found in an input file
        or as passed in by client code to the form that should be used in
        the internal structures. The default implementation returns a
        lower-case version of I{optionName}; subclasses may override this
        or client code can set an attribute of this name on instances to
        affect this behavior. Setting this to C{str()}, for example, would
        make option names case sensitive.
        """
        return str(optionName)

    def __getOptional(self, func, section, option):
        try:
            return func(section, option)
        except ConfigParser.NoOptionError:
            return None
        except ConfigParser.NoSectionError:
            return None

    def __preprocess(self, fp, name):
        
        try:
            fp.name
        except AttributeError:
            try:
                fp.name = name
            except TypeError:
                # Read-only. Oh, well.
                pass
            except AttributeError:
                # Read-only. Oh, well.
                pass

        if self.__permitIncludes:
            # Preprocess includes.
            from grizzled.file import includer
            tempFile = includer.preprocess(fp)
            fp = tempFile

        # Parse the resulting file into a local ConfigParser instance.

        parsedConfig = ConfigParser.SafeConfigParser()

        if self.__useOrderedSections:
            parsedConfig._sections = _SectionDict()

        parsedConfig.optionxform = str
        parsedConfig.read(fp)

        # Process the variable substitutions.

        self.__normalizeVariableReferences(parsedConfig)
        self.__substituteVariables(parsedConfig)

    def __normalizeVariableReferences(self, sourceConfig):
        """
        Convert all section-local variable references (i.e., those that don't
        specify a section) to fully-qualified references. Necessary for
        recursive references to work.
        """
        simpleVarRefRe = re.compile(SIMPLE_VARIABLE_REF_PATTERN)
        for section in sourceConfig.sections():
            for option in sourceConfig.options(section):
                value = sourceConfig.get(section, option, raw=True)
                oldValue = value
                match = simpleVarRefRe.search(value)
                while match:
                    value = value[0:match.start(1)] +\
                            section +\
                            SECTION_OPTION_DELIM +\
                            value[match.start(1):]
                    match = simpleVarRefRe.search(value)

                sourceConfig.set(section, option, value)

    def __substituteVariables(self, sourceConfig):
        mapping = _ConfigDict(sourceConfig, self.__strictSubstitution)
        for section in sourceConfig.sections():
            mapping.section = section
            self.addSection(section)
            for option in sourceConfig.options(section):
                value = sourceConfig.get(section, option, raw=True)

                # Repeatedly substitute, to permit recursive references

                previousValue = ''
                while value != previousValue:
                    previousValue = value
                    value = _ConfigTemplate(value).safe_substitute(mapping)

                self.set(section, option, value)

class _ConfigTemplate(string.Template):
    """
    Subclass of string.Template that handles our configuration variable
    reference syntax.
    """
    idpattern = VARIABLE_REF_PATTERN


class _ConfigDict(dict):
    """
    Dictionary that knows how to dereference variables within a parsed config.
    Only used internally.
    """
    idPattern = re.compile(VARIABLE_REF_PATTERN)
    def __init__(self, parsedConfig, strictSubstitution):
        self.__config = parsedConfig
        self.__strictSubstitution = strictSubstitution
        self.section = None

    def __getitem__(self, key):
        try:
            # Match against the ID regular expression. (If the match fails,
            # it's a bug, since we shouldn't be in here unless it does.)

            match = self.idPattern.search(key)
            assert(match)

            # Now, get the value.

            default = None
            if SECTION_OPTION_DELIM in key:
                if match.group(3):
                    default = self.__extractDefault(match.group(3))

                section = match.group(1)
                option = match.group(2)
            else:
                section = self.section
                default = None
                option = match.group(3)
                if match.group(4):
                    default = self.__extractDefault(match.group(3))

            result = self.__valueFromSection(section, option)

        except KeyError:
            result = default

        except ConfigParser.NoSectionError:
            result = default

        except ConfigParser.NoOptionError:
            result = default

        if not result:
            if self.__strictSubstitution:
                raise NoVariableError, 'No such variable: "%s"' % key
            else:
                result = ''

        return result

    def __extractDefault(self, s):
        default = s
        if default:
            default = default[1:]  # strip leading '?'
            if len(default) == 0:
                default = None

        return default

    def __valueFromSection(self, section, option):
        result = None
        if section == 'env':
            result = os.environ[option]
            if len(result) == 0:
                raise KeyError

        elif section == 'program':
            if option == 'cwd':
                result = os.getcwd()
            elif option == 'now':
                result = time.strftime('%Y-%m-%d %H:%M:%S')
            elif option == 'name':
                result = os.path.basename(sys.argv[0])
            else:
                raise KeyError, option

        else:
            result = self.__config.get(section, option)

        return result

# ---------------------------------------------------------------------------
# Functions
# ---------------------------------------------------------------------------

def preprocess(fileOrURL, defaults=None):
    """
    This function preprocesses a file or URL for a configuration file,
    processing all includes and substituting all variables. It writes a new
    configuration file to a temporary file (or specified output file). The
    new configuration file can be read by a standard C{ConfigParser}
    object. Thus, this method is useful when you have an extended
    configuration file that must be passed to a function or object that can
    only read a standard C{ConfigParser} file.

    For example, here's how you might use the Python C{logging} API with an
    extended configuration file::

        from grizzled.config import Configuration
        import logging

        logging.config.fileConfig(Configuration.preprocess('/path/to/config')

    @type fileOrURL:  string
    @param fileOrURL: file or URL

    @type defaults:   dictionary
    @param defaults:  Defaults to pass through to the config parser

    @rtype: string
    @return: Path to a temporary file containing the expanded configuration.
             The file will be deleted when the program exits, though the caller
             is free to delete it sooner.
    """
    import tempfile
    import atexit

    def unlink(path):
        try:
            os.unlink(path)
        except:
            pass

    parser = Configuration(useOrderedSections=True)
    parser.read(fileOrURL)
    fd, path = tempfile.mkstemp(suffix='.cfg')
    atexit.register(unlink, path)
    parser.write(os.fdopen(fd, "w"))
    return path
    

# ---------------------------------------------------------------------------
# Main program (for testing)
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    import sys

    format = '%(asctime)s %(name)s %(levelname)s %(message)s'
    logging.basicConfig(level=logging.DEBUG, format=format)

    configFile = sys.argv[1]
    config = Configuration()
    config.read(configFile)

    if len(sys.argv) > 2:
        for var in sys.argv[2:]:
            (section, option) = var.split(':')
            val = config.get(section, option, optional=True)
            print '%s=%s' % (var, val)
    else:
        config.write(sys.stdout)
