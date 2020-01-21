=============================
Importanize (import organize)
=============================

.. image:: https://badge.fury.io/py/importanize.svg
    :target: http://badge.fury.io/py/importanize

.. image:: https://drone.miki725.com/api/badges/miki725/importanize/status.svg
    :target: https://drone.miki725.com/miki725/importanize

.. image:: https://codecov.io/gh/miki725/importanize/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/miki725/importanize

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/psf/black

Utility for organizing Python imports using PEP8 or custom rules

* Free software: MIT license
* GitHub: https://github.com/miki725/importanize

Installing
----------

You can install ``importanize`` using pip:

.. code-block:: bash

    pip install importanize

Why?
----

I think imports are important in Python. There are some tools to reformat code
(`black <https://black.readthedocs.io/en/stable/>`_ is amazing). However they
usually dont organize imports very well following PEP8 or custom rules. Top
import organizers are `isort <http://isort.readthedocs.org/en/latest/>`_ and
`zimports <https://github.com/sqlalchemyorg/zimports>`_. ``importanize`` is
similar to them in a sense that it too organizes imports using either PEP8
or custom rules except it also preserves any comments surrounding imports.
In addition it supports some nifty features like full pipe support (yes you
can run ``:'<,'>!importanize`` - your welcome my fellow ``vim`` users :D) or
it can natively output a diff between original and organized file(s).

Example
-------

Before
++++++

.. code-block:: python

    $ cat tests/test_data/input_readme.py
    from __future__ import unicode_literals, print_function
    import os.path as ospath  # ospath is great
    from package.subpackage.module.submodule import CONSTANT, Klass, foo, bar, rainbows
    # UTC all the things
    import datetime # pytz
    from .module import foo, bar  # baz
    from ..othermodule import rainbows

After
+++++

.. code-block:: python

    $ cat tests/test_data/input_readme.py | importanize
    from __future__ import print_function, unicode_literals
    # UTC all the things
    import datetime  # pytz
    from os import path as ospath  # ospath is great

    from package.subpackage.module.submodule import (
        CONSTANT,
        Klass,
        bar,
        foo,
        rainbows,
    )

    from ..othermodule import rainbows
    from .module import bar, foo  # baz⏎

``importanize`` did:

* alphabetical sort, even inside import line (look at ``__future__``)
* normalized ``import .. as ..`` into ``from .. import .. as ..``
* broke long import (>80 chars) which has more than one import
  into multiple lines
* reordered some imports (e.g. local imports ``..`` should be before ``.``)

Using
-----

Using ``importanize`` is super easy. Just run:

.. code-block:: bash

    importanize file_to_organize.py

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
cases it would be recommended to use custom config file:

.. code-block:: bash

    importanize file_to_organize.py --config=config.json

Alternatively ``importanize`` attempts to find configuration in a couple of
default files:

* ``.importanizerc``
* ``importanize.ini``
* ``importanize.json``
* ``setup.cfg``
* ``tox.ini``

As a matter of fact you can see the config file for the importanize
repository itself at
`setup.cfg <https://github.com/miki725/importanize/blob/master/setup.cfg>`_.

Additionally multiple configurations are supported within a single repository
via sub-configurations.
Simply place any of supported config files (see above) within a sub-folder and
all imports will be reconfigured under that folder with the subconfiguration.

Configuration Options
+++++++++++++++++++++

:``groups``:
    List of import groups.
    ``importanize`` will use these group definitions
    to organize imports and will output import groups in the same order
    as defined. Supported group types are:

    * ``stdlib`` - standard library imports including ``__future__``
    * ``sitepackages`` - imports coming from the ``site-packages`` directory
    * ``local`` - local imports which start with ``"."``.
      for example ``from .foo import bar``
    * ``packages`` - if this group is specified, additional key ``packages``
      is required within import group definition which should list
      all Python packages (root level) which should be included in that group:

      .. code-block:: ini

          [importanize]
          groups=
            packages:foo,bar

      or:

      .. code-block:: json

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

    * ``grouped`` (default):

      .. code-block:: python

          from package.subpackage.module.submodule import (
              CONSTANT,
              Klass,
              bar,
              foo,
              rainbows,
          )

    * ``inline-grouped``:

      .. code-block:: python

          from package.subpackage.module.submodule import (CONSTANT,
                                                           Klass,
                                                           bar,
                                                           foo,
                                                           rainbows)

    * ``lines``:

      .. code-block:: python

          from package.subpackage.module.submodule import CONSTANT
          from package.subpackage.module.submodule import Klass
          from package.subpackage.module.submodule import bar
          from package.subpackage.module.submodule import foo
          from package.subpackage.module.submodule import rainbows

    Can be specified in CLI with ``-f`` or ``--formatter`` parameter:

    .. code-block:: bash

        importanize --formatter=grouped

:``length``:
    Line length after which the formatter will split imports.

    Can be specified in CLI with ``-l`` or ``--length`` parameter:

    .. code-block:: bash

        importanize --length=120

:``exclude``:
    List of glob patterns of files which should be excluded from organizing:

    .. code-block:: ini

        [importanize]
        exclude=
          path/to/file
          path/to/files/ignore_*.py

    or:

    .. code-block:: json

        {
          "exclude": [
            "path/to/file",
            "path/to/files/ignore_*.py"
          ]
        }

    Can only be specified in configuration file.

:``after_imports_normalize_new_lines``:
    Boolean whether to adjust number of new lines after imports. By
    default this option is enabled. Enabling this option will disable
    ``after_imports_new_lines``.

    Can only be specified in configuration file.

:``after_imports_new_lines``:
    Number of lines to be included after imports.

    Can only be specified in configuration file.

:``add_imports``:
    List of imports to add to every file:

    .. code-block:: ini

        [importanize]
        add_imports=
          from __future__ import absolute_import, print_function, unicode_literals

    or:

    .. code-block:: json

        {
          "add_imports": [
            "from __future__ import absolute_import, print_function, unicode_literals"
          ]
        }

    Can only be specified in configuration file.

    Note that this option is ignored when input is provided via ``stdin`` pipe.
    This is on purpose to allow to importanize selected text in editors such as
    ``vim``.

    .. code-block:: bash

        cat test.py | importanize

:``allow_plugins``:
    Whether to allow plugins:

    .. code-block:: ini

        [importanize]
        allow_plugins=True

    or:

    .. code-block:: json

        {
            "allow_plugins": true
        }

    Can also be specified with ``--plugins/--no-plugins`` parameter.

    .. code-block:: bash

        importanize --no-plugins

    Note that this configuration is only global and is not honored in
    subconfigurations.

:``plugins``:
    If plugins are allowed, which plugins to use. If not specified
    all by default enabled plugins will be used.

    .. code-block:: ini

        [importanize]
        plugins=
            unused_imports

    or:

    .. code-block:: json

        {
            "plugins": ["unused_imports"]
        }

    Note that this configuration is only global and is not honored in
    subconfigurations.

To view all additional run-time options you can use ``--help`` parameter:

.. code-block:: bash

    importanize --help

Default Configuration
+++++++++++++++++++++

As mentioned previously default configuration attempts to mimic PEP8.
Specific configuration is:

.. code-block:: ini

    [importanize]
    groups=
      stdlib
      sitepackages
      remainder
      local

Configuration Styles
++++++++++++++++++++

Configuration file can either be ``ini`` or ``json`` file. Previously ``json``
was the only supported style however since ``ini`` is easier to read and can
be combined with other configurations like ``flake8`` in ``setup.cfg``, going
forward it is the preferred configuration format.
The following configurations are identical:

.. code-block:: ini

    [importanize]
    formatter=grouped
    groups=
      stdlib
      sitepackages
      remainder
      packages:my_favorite_package,least_favorite_package
      local

and:

.. code-block:: json

    {
      "formatter": "grouped",
      "groups": [
        {"type": "stdlib"},
        {"type": "sitepackages"},
        {"type": "remainder"},
        {"type": "packages",
         "packages": ["my_favorite_package", "least_favorite_package"]},
        {"type": "local"}
      ]
    }

CI Mode
-------

Sometimes it is useful to check if imports are already organized in a file:

.. code-block:: bash

    importanize --ci

Diff
----

It is possible to directly see the diff between original and organized file

.. code-block:: diff

    $ importanize --print --diff --no-subconfig --no-plugins tests/test_data/input_readme_diff.py
    --- original/tests/test_data/input_readme_diff.py
    +++ importanized/tests/test_data/input_readme_diff.py
    @@ -1 +1,9 @@
    -from package.subpackage.module.submodule import CONSTANT, Klass, foo, bar, rainbows
    +from __future__ import absolute_import, print_function, unicode_literals
    +
    +from package.subpackage.module.submodule import (
    +    CONSTANT,
    +    Klass,
    +    bar,
    +    foo,
    +    rainbows,
    +)

List All Imports
----------------

All found imports can be aggregated with ``--list`` parameter:

.. code-block:: bash

    $ importanize --list .
    stdlib
    ------
    from __future__ import absolute_import, print_function, unicode_literals
    import abc
    ...

    sitepackages
    ------------
    import click
    ...

    remainder
    ---------

    packages
    --------
    import importanize
    ...

    local
    -----
    ...

Pipe Support
------------

Pipes for both ``stdin`` and ``stdout`` are supported and are auto-detected:

.. code-block:: python

    $ cat tests/test_data/input_readme_diff.py | importanize
    from package.subpackage.module.submodule import (
        CONSTANT,
        Klass,
        bar,
        foo,
        rainbows,
    )

.. code-block:: python

    $ importanize --no-header --no-subconfig --no-plugins tests/test_data/input_readme_diff.py | cat
    from __future__ import absolute_import, print_function, unicode_literals

    from package.subpackage.module.submodule import (
        CONSTANT,
        Klass,
        bar,
        foo,
        rainbows,
    )

As mentioned above note that ``stdin`` did not honor ``add_imports`` which
allows to use importanize on selected lines in editors such as ``vim``.
To facilitate that feature even further, if selected lines are not module
level (e.g. inside function), any whitespace prefix will be honored:

.. code-block:: python

    $ python -c "print('    import sys\n    import os')" | importanize
        import os
        import sys

Just in case pipes are incorrectly detected auto-detection can be disabled
with ``--no-auto-pipe`` which will require to explicitly use ``--print``,
``--no-header`` and/or ``-`` file path:

.. code-block:: python

    $ cat tests/test_data/input_readme_diff.py | importanize --no-auto-pipe --print -
    from package.subpackage.module.submodule import (
        CONSTANT,
        Klass,
        bar,
        foo,
        rainbows,
    )

Pre-Commit
----------

Importanize integrates with pre-commit_. You can use the following config

.. code-block:: yaml

    repos:
    - repo: https://github.com/miki725/importanize/
      rev: 'master'
      hooks:
      - id: importanize
        args: [--verbose]

Testing
-------

To run the tests you need to install testing requirements first:

.. code-block:: bash

    make install

Then to run tests, you can use ``nosetests`` or simply use Makefile command:

.. code-block:: bash

    nosetests -sv
    # or
    make test

.. _pre-commit: https://pre-commit.com/

Plugins
-------

There is rudimentarry support for plugins. Currently plugin interface is
limited but allows for some useful operations. Plugins can be dynamically
registered via `pluggy <https://pluggy.readthedocs.io/en/latest/>`_ however
``importanize`` ships with some bundled-in plugins at ``importanize/contrib``.

To create a plugin simply implement ``ImportanizePlugin`` class.
Note that example below does not implement all supported methods.

.. code-block:: python

    from importanize.plugins import ImportanizePlugin, hookimpl

    class MyPlugin(ImportanizePlugin):
        version = '0.1'
        @hookimpl
        def should_include_statement(self, group, statement):
            return True

    plugin = MyPlugin()

Then register the plugin in ``setup.py``:

.. code-block:: python

    setup(
        ...
        entry_points={
            "importanize": ["my_plugin = my_plugin:plugin"],
        },
    )

All installed plugins are listed as part of ``importanize --version`` command.

Bundled Plugins
+++++++++++++++

Unused Imports
~~~~~~~~~~~~~~

Uses ``pyflakes`` to remove unused imports:

.. code-block:: bash

    $ importanize tests/test_data/input_unused_imports.py --print --diff --no-subconfig
    --- original/tests/test_data/input_unused_imports.py
    +++ importanized/tests/test_data/input_unused_imports.py
    @@ -1,5 +1,5 @@
    +from __future__ import absolute_import, print_function, unicode_literals
     import os
    -import sys


     os.path.exists('.')

This plugin is enabled by default. To disable removing unused imports you can
either:

* disable all plugins via ``allow_plugins``:

  .. code-block:: ini

      allow_plugins=false

* disable ``unused_imports`` specific plugin by omitting it from ``plugins``
  configuration:

  .. code-block:: ini

      plugins=
        # other plugins except unused_imports

* add ``# noqa`` comment to unused imports to not remove them

Separate Libraries
~~~~~~~~~~~~~~~~~~

Splits all libraries into independant blocks within import groups:

.. code-block:: bash

    $ importanize tests/test_data/input_separate_libs.py --print --diff --no-subconfig -c tests/test_data/subconfig/separate_libs.ini
    --- original/tests/test_data/input_separate_libs.py
    +++ importanized/tests/test_data/input_separate_libs.py
    @@ -2,6 +2,7 @@
     import sys

     import click
    +
     import pluggy

     from . import foo

This plugin is not enabled by default. To enable add ``separate_libs`` to
``plugins`` configuration:

.. code-block:: ini

    plugins=
      separate_libs
