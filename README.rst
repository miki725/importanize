=============================
Importanize (import organize)
=============================

.. image:: https://badge.fury.io/py/importanize.png
    :target: http://badge.fury.io/py/importanize

.. image:: https://travis-ci.org/miki725/importanize.png?branch=master
    :target: https://travis-ci.org/miki725/importanize

.. image:: https://coveralls.io/repos/miki725/importanize/badge.png?branch=master
    :target: https://coveralls.io/r/miki725/importanize?branch=master

Utility for organizing Python imports using PEP8 or custom rules

* Free software: MIT license
* GitHub: https://github.com/miki725/importanize

Installing
----------

You can install ``importanize`` using pip::

    $ pip install importanize

Why?
----

I think imports are important in Python. I also think PEP8 is awesome
(if you disagree, read some PHP) and there are many tools to help
developers reformat code to match PEP8. There are however fewer tools
for organizing imports either by following PEP8 or custom rules.
There is `isort <http://isort.readthedocs.org/en/latest/>`_
(which unfortunately I found out about after writing this lib)
however it seems to do lots of magic to determine which packages
are 3rd party, local packages, etc. I wanted the imports configuration
to be simple and explicit.
This is where ``importanize`` comes in. It allows to organize
Python imports using PEP8 or your custom rules. Read on for
more information.

Using
-----

Using ``importanize`` is super easy. Just run::

    $ importanize file_to_organize.py

That will re-format all imports in the given file.
As part of the default configuration, ``importanize`` will try
it's best to organize imports to follow PEP8 however that is a rather
challenging task, since it is difficult to determine all import groups
as suggested by `PEP8 <http://legacy.python.org/dev/peps/pep-0008/#imports>`_:

1) standard library imports
2) related third party imports
3) local application/library specific imports

To help ``importanize`` distinguish between different import groups in most
cases it would be recommended to use custom config file::

    $ importanize file_to_organize.py config.json

Config file is simply a ``json`` file like this::

    {
        "exclude": [
            "path/to/file",
            "path/to/files/ignore_*.py"
        ],
        "formatter": "grouped",
        "groups": [
            {
                "type": "stdlib"
            },
            {
                "type": "sitepackages"
            },
            {
                "type": "remainder"
            },
            {
                "type": "packages",
                "packages": [
                    "my_favorite_package"
                ]
            },
            {
                "type": "local"
            }
        ]
    }

Default config looks something like::

    {
        "groups": [
            {
                "type": "stdlib"
            },
            {
                "type": "sitepackages"
            },
            {
                "type": "remainder"
            },
            {
                "type": "local"
            }
        ]
    }

Currently the only required key is ``"groups"`` which must be an array
of group definitions. ``importanize`` will use these group definitions
to organize imports and will output import groups in the same order
as defined in the config file. These are the supported group types:

* ``stdlib`` - standard library imports including ``__future__``
* ``sitepackages`` - imports coming from the ``site-packages`` directory
* ``local`` - local imports which start with ``"."``. for example
  ``from .foo import bar``
* ``packages`` - if this group is specified, additional key ``packages``
  is required within import group definition which should list
  all Python packages (root level) which should be included in that group::

      {
          "type": "packages",
          "packages": ["foo", "bar"]
      }

* ``remaining`` - all remaining imports which did not satisfy requirements
  of all other groups will go to this group.

You can use the config file by specifying it in the ``importanize``
command as shown above however you can also create an ``.importanizerc``
file and commit that to your repository. As a matter of fact,
you can see the
`.importanizerc <https://github.com/miki725/importanize/blob/master/.importanizerc>`_
config file used for the importanize repository itself.

You can also choose the formatter used to organize long multiline imports.
Currently, there are two formatters available:

* ``grouped`` (default)
* ``inline-grouped``

It can be set using the formatter config value, or the formatter option, for
example::

    $ importanize --formatter=inline-group --print tests/test_data/input.txt


Finally, you can see all other available ``importanize`` options::

    $ importanize --help

Example
-------

Here is a before and after using the default formatter(on hypothetical file):

Before
~~~~~~

::

    from __future__ import unicode_literals, print_function
    import os.path as ospath
    import datetime
    from package.subpackage.module.submodule import CONSTANT, Klass, foo, bar, rainbows
    from .module import foo, bar
    from ..othermodule import rainbows

After
~~~~~

::

    from __future__ import print_function, unicode_literals
    import datetime
    from os import path as ospath

    from package.subpackage.module.submodule import (
        CONSTANT,
        Klass,
        bar,
        foo,
        rainbows,
    )

    from ..othermodule import rainbows
    from .module import bar, foo

Here is what ``importanize`` did:

* alphabetical sort, even inside import line (look at ``__future__``)
* normalized ``import .. as ..`` into ``from .. import .. as ..``
* broke long import (>80 chars) which has more than one import
  into multiple lines
* reordered some imports (e.g. local imports ``..`` should be before ``.``)

Testing
-------

To run the tests you need to install testing requirements first::

    $ make install

Then to run tests, you can use ``nosetests`` or simply use Makefile command::

    $ nosetests -sv
    # or
    $ make test
