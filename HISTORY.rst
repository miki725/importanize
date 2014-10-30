.. :changelog:

History
-------

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
