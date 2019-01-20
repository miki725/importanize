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

    ❯❯❯ pip install importanize

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

Example
-------

Before
++++++

::

    ❯❯❯ cat tests/test_data/input_readme.py
    from __future__ import unicode_literals, print_function
    import os.path as ospath
    from package.subpackage.module.submodule import CONSTANT, Klass, foo, bar, rainbows
    import datetime
    from .module import foo, bar
    from ..othermodule import rainbows

After
+++++

::

    ❯❯❯ cat tests/test_data/input_readme.py | importanize
    from __future__ import absolute_import, print_function, unicode_literals
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

``importanize`` did:

* alphabetical sort, even inside import line (look at ``__future__``)
* normalized ``import .. as ..`` into ``from .. import .. as ..``
* broke long import (>80 chars) which has more than one import
  into multiple lines
* reordered some imports (e.g. local imports ``..`` should be before ``.``)

Using
-----

Using ``importanize`` is super easy. Just run::

    ❯❯❯ importanize file_to_organize.py

That will re-format all imports in the given file.
As part of the default configuration, ``importanize`` will try
it's best to organize imports to follow PEP8 however that is a rather
challenging task, since it is difficult to determine all import groups
as suggested by `PEP8 <http://legacy.python.org/dev/peps/pep-0008/#imports>`_:

1) standard library imports
2) related third party imports
3) local application/library specific imports

Configuration
-------------

To help ``importanize`` distinguish between different import groups in most
cases it would be recommended to use custom config file::

    ❯❯❯ importanize file_to_organize.py --config=config.json

Alternatively ``importanize`` attempts to find configuration in couple of
default files:

* ``.importanizerc``
* ``setup.cfg``
* ``importanize.ini``

As a matter of fact you can see the config file for the importanize
repository itself at
`setup.cfg <https://github.com/miki725/importanize/blob/master/setup.cfg>`_.

Additionally multiple configurations are supported within a single repository
via sub-configurations.
Simply place any of supported config files ``.importanizerc``, ``setup.cfg``
or ``importanize.ini`` within a sub-folder and all imports will be
reconfigured under that folder.

Configuration Options
+++++++++++++++++++++

:``groups``:
    List of import group definition.
    ``importanize`` will use these group definitions
    to organize imports and will output import groups in the same order
    as defined. Supported group types are:

    * ``stdlib`` - standard library imports including ``__future__``
    * ``sitepackages`` - imports coming from the ``site-packages`` directory
    * ``local`` - local imports which start with ``"."``.
      for example ``from .foo import bar``
    * ``packages`` - if this group is specified, additional key ``packages``
      is required within import group definition which should list
      all Python packages (root level) which should be included in that group::

          {
              "type": "packages",
              "packages": ["foo", "bar"]
          }

    * ``remaining`` - all remaining imports which did not satisfy requirements
      of all other groups will go to this group.

    Can only be specified in configuration file.

:``formatter``:
    Select how to format long multiline imports.
    Supported formatters:

    * ``grouped`` (default)::

          from package.subpackage.module.submodule import (
              CONSTANT,
              Klass,
              bar,
              foo,
              rainbows,
          )

    * ``inline-grouped``::

          from package.subpackage.module.submodule import (CONSTANT,
                                                           Klass,
                                                           bar,
                                                           foo,
                                                           rainbows)

    Can be specified in CLI with ``-f`` or ``--formatter`` parameter::

        ❯❯❯ importanize --formatter=grouped

:``length``:
    Line length after which the formatter will split imports.

    Can be specified in CLI with ``-l`` or ``--length`` parameter::

        ❯❯❯ importanize --length=120

:``exclude``:
    List of glob patterns of files which should be excluded from organizing::

        "exclude": [
            "path/to/file",
            "path/to/files/ignore_*.py"
        ]

    Can only be specified in configuration file.

:``after_imports_new_lines``:
    Number of lines to be included after imports.

    Can only be specified in configuration file.

:``add_imports``:
    List of imports to add to every file::

        "add_imports": [
            "from __future__ import absolute_import, print_function, unicode_literals"
        ]

    Can only be specified in configuration file.

To view all additional run-time options you can use ``--help`` parameter::

    ❯❯❯ importanize --help

Default Configuration
+++++++++++++++++++++

As mentioned previously default configuration attempts to mimic PEP8.
Specific configuration is::

    [importanize]
    groups=
        stdlib
        sitepackages
        remainder
        local

Configuration Styles
++++++++++++++++++++

Configuration file can either be ``json`` or ``ini`` file.
The following configurations are identical::

    {
        "formatter": "grouped",
        "groups": [
            {"type": "stdlib"},
            {"type": "sitepackages"},
            {"type": "remainder"},
            {"type": "packages",
             "packages": ["my_favorite_package"]},
            {"type": "local"}
        ]
    }

and::

    [importanize]
    formatter=grouped
    groups=
        stdlib
        sitepackages
        remainder
        mypackages
        local

    [importanize:mypackages]
    packages:
        my_favorite_package

CI Mode
-------

Sometimes it is useful to check if imports are already organized in a file::

    ❯❯❯ importanize --ci

In addition since some imports change order between Python 2/3 due to different
stdlibs, ``--py`` can be used to enable ``importanize`` only for specific
Python versions::

    ❯❯❯ importanize --ci --py=3

Pre-Commit
----------

Importanize integrates with pre-commit_. You can use the following config

::

    repos:
    - repo: https://github.com/miki725/importanize/
      rev: 'master'
      hooks:
      - id: importanize
        args: [--verbose]

Testing
-------

To run the tests you need to install testing requirements first::

    ❯❯❯ make install

Then to run tests, you can use ``nosetests`` or simply use Makefile command::

    ❯❯❯ nosetests -sv
    # or
    ❯❯❯ make test

.. _pre-commit: https://pre-commit.com/
