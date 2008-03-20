# $Id$
#
# Nose program for testing grizzled.config.Configuration

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

import sys
print ' '.join(sys.argv)

from grizzled.config import (Configuration, NoVariableError)
from cStringIO import StringIO
import os
import tempfile
import atexit

# ---------------------------------------------------------------------------
# Globals
# ---------------------------------------------------------------------------

CONFIG1 = """
[section1]
foo = bar
bar = ${foo}
bar2 = ${section1:foo}
"""

CONFIG2 = """
[section1]
foo = bar
bar = ${foo}

[section2]
foo = ${section1:foo}
bar = ${env:SOME_ENV_VAR}
"""

CONFIG_ORDER_TEST = """
[z]
foo = bar
bar = ${foo}

[y]
foo = ${z:foo}
bar = ${z:bar}

[a]
foo = 1
bar = 2

[z2]
foo = ${z:foo}
bar = ${z:bar}
"""

# ---------------------------------------------------------------------------
# Classes
# ---------------------------------------------------------------------------

class TestParser(object):

    def testSubstitute1(self):
        config = Configuration()
        config.readfp(StringIO(CONFIG1))
        assert config.hasSection('section1')
        assert not config.hasSection('section2')
        assert not config.hasSection('foo')
        assert not config.hasSection('bar')
        assert not config.hasSection('bar2')
        assert config.hasOption('section1', 'foo')
        assert config.hasOption('section1', 'bar')
        assert config.hasOption('section1', 'bar2')
        assert config.get('section1', 'foo') == 'bar'
        assert config.get('section1', 'bar') == 'bar'
        assert config.get('section1', 'bar2') == 'bar'

    def testSubstitute2(self):
        os.environ['SOME_ENV_VAR'] = 'test_test_test'
        config = Configuration()
        config.readfp(StringIO(CONFIG2))
        assert config.hasSection('section1')
        assert config.hasSection('section2')
        assert not config.hasSection('foo')
        assert not config.hasSection('bar')
        assert not config.hasSection('bar2')
        assert config.hasOption('section1', 'foo')
        assert config.hasOption('section1', 'bar')
        assert not config.hasOption('section1', 'bar2')
        assert config.hasOption('section2', 'foo')
        assert config.hasOption('section2', 'bar')
        assert config.get('section1', 'foo') == 'bar'
        assert config.get('section1', 'bar') == 'bar'
        assert config.get('section2', 'foo') == 'bar'
        assert config.get('section2', 'bar') == os.environ['SOME_ENV_VAR']

    def testInclude(self):
        fd, tempPath = tempfile.mkstemp(suffix='.cfg')

        def unlinkTemp(path):
            try:
                os.unlink(path)
            except:
                pass

        atexit.register(unlinkTemp, tempPath)
        fp = os.fdopen(fd, "w")
        print >> fp, '[section3]\nbaz = somevalue\n'
        fp.close()

        s = '%s\n\n%%include "%s"\n' % (CONFIG2, tempPath)

        os.environ['SOME_ENV_VAR'] = 'test_test_test'
        config = Configuration()
        config.readfp(StringIO(s))
        assert config.hasSection('section1')
        assert config.hasSection('section2')
        assert config.hasSection('section3')
        assert not config.hasSection('foo')
        assert not config.hasSection('bar')
        assert not config.hasSection('bar2')
        assert config.hasOption('section1', 'foo')
        assert config.hasOption('section1', 'bar')
        assert not config.hasOption('section1', 'bar2')
        assert config.hasOption('section2', 'foo')
        assert config.hasOption('section2', 'bar')
        assert config.hasOption('section3', 'baz')
        assert config.get('section1', 'foo') == 'bar'
        assert config.get('section1', 'bar') == 'bar'
        assert config.get('section2', 'foo') == 'bar'
        assert config.get('section2', 'bar') == os.environ['SOME_ENV_VAR']
        assert config.get('section3', 'baz') == 'somevalue'

    def testOrdering(self):
        config = Configuration(useOrderedSections=True)
        config.readfp(StringIO(CONFIG_ORDER_TEST))
        assert config.hasSection('a')
        assert config.hasSection('y')
        assert config.hasSection('z')
        sections = config.sections()
        assert len(sections) == 4
        assert sections[0] == 'z'
        assert sections[1] == 'y'
        assert sections[2] == 'a'
        assert sections[3] == 'z2'

    def testBadSubstitution(self):
        cfgString = """
[foo]
var1 = ${bar}
"""
        import sys
        from grizzled.io import AutoFlush
        sys.stdout = AutoFlush(sys.stdout)
        config = Configuration(strictSubstitution=False)
        config.readfp(StringIO(cfgString))
        config.write(sys.stdout)

        try:
            var1 = config.get('foo', 'var1', optional=True)
            assert var1 == None, 'Expected empty variable value'
        except:
            raise

        config = Configuration(strictSubstitution=True)
        try:
            config.readfp(StringIO(cfgString))
            assert False, 'Expected an exception'
        except NoVariableError:
            pass
        except:
            assert False, 'Unexpected exception'
        
