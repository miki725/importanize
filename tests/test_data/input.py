"""Docstring here"""

# comment
# another comment
from __future__ import unicode_literals, print_function


import os.path as ospath
import datetime
from package.subpackage.module.submodule import CONSTANT, Klass, foo, bar, rainbows
import datetime.parser

#my dates are better
import datetime as mydatetime
from .module import foo, bar
from ..othermodule import rainbows
from a import b
from a.b import c
import flake8 as lint  # in site-package
from a.b import d

import foo, bar # common comment
import z
from z import *
import coverage  # in site-packages
from z import foo

import datetime.parser
import foo as\
bar
import something # with comment
# standalone comment
from other.package.subpackage.module.submodule import CONSTANT, Klass, foo, bar, rainbows, rainbows # noqa
from other import(
    something, # something comment
    something_else,# noqa
    #lots of happy things below
    and_rainbows
    # rainbows
)# haha

# stuff here
