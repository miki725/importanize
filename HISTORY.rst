.. :changelog:

History
-------

0.5.3 (2017-06-06)
~~~~~~~~~~~~~~~~~~

* Added support to customize number of new lines added after imports
  via ``after_imports_new_lines`` configuration.
  Useful when using auto formatters such as ``yapf``.

0.5.2 (2017-05-18)
~~~~~~~~~~~~~~~~~~

* Skipping directories which makes skipping subfolders much faster
* Fixed bug which incorrectly skipped files

0.5.1 (2017-05-09)
~~~~~~~~~~~~~~~~~~

* Fixed bug which incorrectly removed duplicate leafless imports which had different ``as`` names

0.5.0 (2017-05-03)
~~~~~~~~~~~~~~~~~~

* Added ``--ci`` flag to validate import organization in files
* Added ``sitepackages`` import group. Thanks `Pamela <https://github.com/PamelaM>`_.
  See ``README`` for more info
* Added pipe handling (e.g. ``cat foo.py | importanize``)
* Fixed bug which incorrectly sorted imports with aliases (e.g. ``import foo as bar``)
* Files are not overridden when imports are already organized.
  Useful in precommit hooks which detect changed files.
* Released as Python `wheel <http://pythonwheels.com/>`_

0.4.1 (2015-07-28)
~~~~~~~~~~~~~~~~~~

* Fixed a bug where ``importanize`` did not correctly detect stdlibs on Windows
  (see `#29 <https://github.com/miki725/importanize/issues/29/>`_)
* Removed ``future`` dependency since ``six>=1.9`` includes all the used features
* Fixed tests to be executable on Windows

0.4 (2015-04-13)
~~~~~~~~~~~~~~~~

* Added multiple formatter options. Can be used using ``--formatter``
  flag or can be set in the configuration file.
* Fixes a bug in parsing imports when encountering both ``\`` and ``()``
  (see `#26 <https://github.com/miki725/importanize/issues/26>`_ for example)
* Fixes a bug where wildcard leaf imports were combined with other others
  (see `#25 <https://github.com/miki725/importanize/issues/25/>`_ for example)

0.3 (2015-01-18)
~~~~~~~~~~~~~~~~

* Using tokens to parse Python files. As a result this allows to
  fix how comments are handled
  (see `#21 <https://github.com/miki725/importanize/issues/21>`_ for example)

0.2 (2014-10-30)
~~~~~~~~~~~~~~~~

* New "exclude" config which allows to skip files
* Presetving origin file new line characters
* Traversing parent paths to find importanize config file

0.1.4 (2014-10-12)
~~~~~~~~~~~~~~~~~~

* Multiple imports (e.g. ``import a, b``) are normalized
  instead of exiting
* Multiple imports with the same stem are combined into
  single import statement
  (see `#17 <https://github.com/miki725/importanize/issues/17>`_ for example)

0.1.3 (2014-09-15)
~~~~~~~~~~~~~~~~~~

* Fixed where single line triple-quote docstrings would cause
  none of the imports to be recognized

0.1.2 (2014-09-15)
~~~~~~~~~~~~~~~~~~

* Fixed where import leafs were not properly sorted for
  mixed case (aka CamelCase)

0.1.1 (2014-09-07)
~~~~~~~~~~~~~~~~~~

* Ignoring comment blocks when parsing for imports
* Fixed bug when imports start on a first line,
  extra lines were being added to the file.

0.1.0 (2014-09-07)
~~~~~~~~~~~~~~~~~~

* First release on PyPI.
