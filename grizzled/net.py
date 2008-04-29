# $Id$

"""
Network-related methods and classes.
"""
# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

from __future__ import absolute_import

import urlparse
import shutil
import tempfile
import urllib2
import logging
import os

# ---------------------------------------------------------------------------
# Exports
# ---------------------------------------------------------------------------

__all__ = ['download']

# ---------------------------------------------------------------------------
# Globals
# ---------------------------------------------------------------------------

log = logging.getLogger('grizzled.net')

# ---------------------------------------------------------------------------
# Classes
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Functions
# ---------------------------------------------------------------------------

def download(url, directory=None, bufsize=8192):
    """
    Download the specified URL to a directory. This module properly handles
    HTTP authentication for URLs like this one::

        https://user:password@localhost:8080/foo/bar/baz.tgz

    Note, however, that user/password authentication is only supported for
    "http" and "https" URLs.

    @type url:  str
    @param url: The URL to download

    @type directory:  str
    @param directory: The directory to receive the downloaded file. If this
                      parameter is omitted, C{urlDownload()} will create a
                      temporary directory to contain the file.
                      
    @type bufsize:  int
    @param bufsize: buffer size to use when reading URL.

    @rtype:  tuple
    @return: A C{(downloadedFile, downloadDirectory)} tuple
    """
    pieces = urlparse.urlparse(url)
    path = pieces.path
    if not directory:
        directory = tempfile.mkdtemp(prefix='download')

    outputPath = os.path.join(directory, os.path.basename(path))

    # Handle user/password explicitly.

    if pieces.scheme.startswith('http') and pieces.username:
        # Initialize basic HTTP authentication for this URL.
        # See http://aspn.activestate.com/ASPN/docs/ActivePython/2.5/howto/urllib2/index.html
        #
        # NOTE: This is necessary because urllib doesn't handle URLs like
        # http://user:password@host:port/...

        # Get the user name and password from the URL.
        user, password = pieces.username, pieces.password

        netloc = pieces.hostname
        if pieces.port:
            pieces.hostname += ':%d' % pieces.port
        newPieces = (pieces.scheme, netloc, pieces.path, pieces.query, 
                     pieces.params, pieces.fragment)
        url = urlparse.urlunparse(newPieces)
        log.debug('Installing authorization handler for URL %s' % url)
        passwordMgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
        passwordMgr.add_password(realm=None,
                                 uri=url,
                                 user=user,
                                 passwd=password)
        authHandler = urllib2.HTTPBasicAuthHandler(passwordMgr)
        opener = urllib2.build_opener(authHandler)
        opener.open(url)
        urllib2.install_opener(opener)

    log.debug('Downloading "%s" to "%s"' % (url, directory))
    shutil.copyfileobj(urllib2.urlopen(url), open(outputPath, 'wb'), bufsize)

    return (directory, outputPath)
