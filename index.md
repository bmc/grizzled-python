---
title: The Grizzled Python Utility Library
layout: withTOC
---

## Introduction

The Grizzled Python Utility Library is a general-purpose [Python][] library
with a variety of different modules and packages. It's roughly organized
into subpackages that group different kinds of utility functions and
classes. For a sampling of what's available, see the API documentation.

Grizzled Python is under continual development, so check back regularly.

## Getting and installing Grizzled Python

### Installing via EasyInstall

Because Grizzled Python is available via [PyPI][], if you have
[EasyInstall][] installed on your system, installing the library is as easy
as running this command (usually as `root` or the system administrator):

    easy_install grizzled

### Installing from source

You can also install Grizzled Python from source. Either download the
source (as a zip or tarball) from
<http://github.com/bmc/grizzled-python/downloads>, or make a local
read-only clone of the [GitHub repository][] using one of the following
commands:

    $ git clone git://github.com/bmc/grizzled-python.git
    $ git clone http://github.com/bmc/grizzled-python.git

Once you have a local `grizzled-python` source directory, change your
working directory to the source directory, and type:

    python setup.py install

To install it somewhere other than the default location (such as in your
home directory) type:

    python setup.py install --prefix=$HOME

## Documentation

Please see the [*epydoc*][]-generated [API documentation][] for
documentation on the individual classes and modules in the Grizzled Python
Utility Library.

## Copyright and License

The Grizzled Python Utility Library is copyright &copy; 2008-2010
[Brian M. Clapper][] is released under a [BSD license][license]. See the
accompanying [license][] file.

## Patches

I gladly accept patches from their original authors. Feel free to email
patches to me or to fork the [GitHub repository][] and send me a pull
request. Along with any patch you send:

* Please state that the patch is your original work.
* Please indicate that you license the work to the Grizzled Python Library
  project under a [BSD License][license].

[license]: license.html
[*epydoc*]: http://epydoc.sourceforge.net/
[Python]: http://www.python.org/
[API Documentation]: epydoc/
[Brian M. Clapper]: mailto:bmc@clapper.org
[EasyInstall]: http://peak.telecommunity.com/DevCenter/EasyInstall
[PyPI]: http://pypi.python.org/pypi
[GitHub repository]: http://github.com/bmc/grizzled-python
