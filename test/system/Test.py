# $Id$
#
# Nose program for testing grizzled.sys classes/functions

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

from __future__ import absolute_import

import sys
from grizzled.system import *

# ---------------------------------------------------------------------------
# Globals
# ---------------------------------------------------------------------------

VERSIONS = [('2.5.1', 0x020501f0),
            ('1.5',   0x010500f0),
            ('2.6',   0x020600f0),
            ('2.4.3', 0x020403f0)]

# ---------------------------------------------------------------------------
# Classes
# ---------------------------------------------------------------------------

class TestSys(object):

    def testVersionConversions(self):
        for s, i in VERSIONS:
            yield self.doOneVersionConversionTest, s, i
            
    def doOneVersionConversionTest(self, string_version, binary_version):
        h = python_version(string_version)
        s = python_version_string(binary_version)
        assert h == binary_version
        assert s == string_version
        
    def testCurrentVersion(self):
        ensure_version(sys.hexversion)
        ensure_version(python_version_string(sys.hexversion))
        major, minor, patch, final, rem = sys.version_info
        binary_version = python_version('%d.%d.%d' % (major, minor, patch))
        
        
            

 
