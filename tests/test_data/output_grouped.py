"""Docstring here"""

from __future__ import print_function, unicode_literals
import datetime
from os import path as ospath

import coverage  # in site-packages
import flake8 as lint  # in site-package

import something  # with comment
import z
from a import b
from a.b import c, d
from other import (  # noqa
    # lots of happy things below
    and_rainbows,
    something,  # something comment
    something_else,
)
from other.package.subpackage.module.submodule import (  # noqa
    CONSTANT,
    Klass,
    bar,
    foo,
    rainbows,
)
from package.subpackage.module.submodule import (
    CONSTANT,
    Klass,
    bar,
    foo,
    rainbows,
)
from z import *
from z import foo

from ..othermodule import rainbows
from .module import bar, foo


# stuff here
