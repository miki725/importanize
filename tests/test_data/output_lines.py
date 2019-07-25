"""Docstring here"""

# comment
# another comment
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
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
from a.b import c
from a.b import d
from other import and_rainbows  # rainbows haha lots of happy things below
from other import something  # rainbows haha something comment
from other import something_else  # noqa rainbows haha
# standalone comment
from other.package.subpackage.module.submodule import CONSTANT
from other.package.subpackage.module.submodule import Klass
from other.package.subpackage.module.submodule import bar
from other.package.subpackage.module.submodule import foo
from other.package.subpackage.module.submodule import rainbows  # noqa
from package.subpackage.module.submodule import CONSTANT
from package.subpackage.module.submodule import Klass
from package.subpackage.module.submodule import bar
from package.subpackage.module.submodule import foo
from package.subpackage.module.submodule import rainbows
from z import *
from z import foo

from ..othermodule import rainbows
from .module import bar
from .module import foo


# stuff here
