# Grizzled Python Utility Library

The [Grizzled Python Utility Library][] is a general-purpose Python library
with a variety of different modules and packages. It's roughly organized
into subpackages that group different kinds of utility functions and
classes.

Grizzled is copyright &copy; 2008-2017 by Brian M. Clapper and is released
under a BSD license.

**NOTE**: This package does not yet work on Python 3.

## Installing

The easiest way to install the library is via [pip](https://pip.pypa.io/):

```
pip install grizzled-python
```

## Installing from source

Clone this repo, and do the usual:

```
git clone git@github.com:bmc/grizzled-python.git
cd grizzled-python
python setup.py install
```

## Running unit tests

Unit tests are written with [Nose](http://pythontesting.net/framework/nose/nose-introduction/).

Install Nose:

```
pip install nose
```

Then, from the top-level directory, just run:

```
nosetests
```

[Grizzled Python Utility Library]: http://software.clapper.org/grizzled-python/
