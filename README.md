# Grizzled Python Utility Library

![Travis CI](https://api.travis-ci.org/bmc/grizzled-python.svg?branch=master)

The [Grizzled Python Utility Library][] is a general-purpose Python library
with a variety of different modules and packages. It's roughly organized
into subpackages that group different kinds of utility functions and
classes.

Grizzled Python is copyright &copy; 2008-2019 by Brian M. Clapper and 
is released under a BSD license.

**NOTE**: As of version 2.0.0, Grizzled Python no longer supports Python 2.
Use an older version (e.g., 1.1.0) if you want to use it on Python 2.
Grizzled Python now supports Python 3.6 or better.

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
python setup.py test
```

[Grizzled Python Utility Library]: http://software.clapper.org/grizzled-python/
