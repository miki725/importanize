"""Docstring here"""

# comment
# another comment
from __future__ import absolute_import, print_function, unicode_literals
import datetime
# my dates are better
import datetime as mydatetime
import datetime.parser
from os import path as ospath

import coverage  # in site-packages
import flake8 as lint  # in site-package

import bar  # common comment
import foo  # common comment
import foo as bar
import something  # with comment
import z
from a import b
from a.b import c, d
from other import (  # noqa rainbows haha
    # lots of happy things below
    and_rainbows,
    something,  # something comment
    something_else,
)
# standalone comment
from other.package.subpackage.module.submodule import (CONSTANT,  # noqa
                                                       Klass,
                                                       bar,
                                                       foo,
                                                       rainbows)
from package.subpackage.module.submodule import (CONSTANT,
                                                 Klass,
                                                 bar,
                                                 foo,
                                                 rainbows)
from z import *
from z import foo

from ..othermodule import rainbows
from .module import bar, foo


# stuff here
