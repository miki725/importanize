# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function
import operator
import re
from future.utils import python_2_unicode_compatible

from utils import list_strip


CHARS = re.compile(r'[\\()]')
DOTS = re.compile(r'^(\.+)(.*)')


class ComparatorMixin(object):
    def __ne__(self, other):
        return not (self == other)

    def __lt__(self, other):
        return (not self == other) and not (self > other)

    def __ge__(self, other):
        return (self == other) and (self > other)

    def __le__(self, other):
        return not (self > other)


@python_2_unicode_compatible
class ImportLeaf(ComparatorMixin):
    """
    Data-structure about each import statement leaf-module.

    For example, if import statement is
    ``from foo.bar import rainbows``, leaf-module is
    ``rainbows``.
    Also aliased modules are supported (e.g. using ``as``).
    """

    def __init__(self, name):
        as_name = None

        if ' as ' in name:
            name, as_name = list_strip(name.split(' as '))

        if name == as_name:
            as_name = None

        self.name = name
        self.as_name = as_name

    def as_string(self):
        string = self.name
        if self.as_name:
            string += ' as {}'.format(self.as_name)
        return string

    def __str__(self):
        return self.as_string()

    def __eq__(self, other):
        return self.name == other.name

    def __gt__(self, other):
        return self.name > other.name


class ImportStatement(ComparatorMixin):
    """
    Data-structure to store information about
    each import statement.

    Parameters
    ----------
    line_numbers : list
        List of line numbers from which
        this import was parsed.
        Useful when writing imports back into file.
    stem : str
        Import step string.
        For ``from foo.bar import rainbows``
        step is ``foo.bar``.
    leafs : list
        List of ``ImportLeaf`` instances
    """

    def __init__(self, line_numbers, stem, leafs=None):
        self.line_numbers = line_numbers
        self.stem = stem
        self.leafs = leafs or []

    @property
    def root_module(self):
        """
        Root module being imported.
        This is used to sort imports as well as to
        determine to which import group this import
        belongs to.
        """
        return self.stem.split('.', 1)[0]

    def as_string(self):
        if not self.leafs:
            return 'import {}'.format(self.stem)
        else:
            return (
                'from {} import {}'
                ''.format(self.stem,
                          ', '.join(map(operator.methodcaller('as_string'),
                                        sorted(self.leafs))))
            )

    def __str__(self):
        return self.as_string()

    def __eq__(self, other):
        return all((self.stem == other.stem,
                    sorted(self.leafs) == sorted(other.leafs)))

    def __gt__(self, other):
        """
        Follows the following rules:

        * ``__future__`` is always first
        * ``import ..`` is ahead of ``from .. import ..``
        * otherwise root_module is alphabetically compared
        """
        # same stem so compare sorted first leafs, if there
        if self.stem == other.stem and self.leafs and other.leafs:
            return sorted(self.leafs)[0] > sorted(other.leafs)[0]

        # check for __future__
        if self.root_module == '__future__':
            return False
        elif other.root_module == '__future__':
            return True

        # local imports
        if all([self.stem.startswith('.'),
                other.stem.startswith('.')]):
            # double dot import should be ahead of single dot
            # so only make comparison when different number of dots
            self_local = DOTS.findall(self.stem)[0][0]
            other_local = DOTS.findall(other.stem)[0][0]
            if len(self_local) != len(other_local):
                return len(self_local) < len(other_local)

        # check for ``import ..`` vs ``from .. import ..``
        self_len = len(self.leafs)
        other_len = len(other.leafs)
        if any([not self_len and other_len,
                self_len and not other_len]):
            return self_len > other_len

        # alphabetical sort
        return self.stem > other.stem


def find_imports_from_lines(iterator):
    """
    Find import statements as strings from
    enumerated iterator of lines.

    Usually the iterator will of file lines.

    Parameters
    ----------
    iterator : generator
        Enumerated iterator which yield items
        ``(line_number, line_string)``

    Returns
    -------
    imports : generator
        Iterator which yields normalized import
        strings with line numbers from which the
        import statement has been parsed from.

    Example
    -------

    ::

        >>> parsed = list(find_imports_from_lines(iter([
        ...     (1, 'from __future__ import unicode_literals'),
        ...     (2, 'import os.path'),
        ...     (3, 'from datetime import ('),
        ...     (4, '   date,'),
        ...     (5, '   datetime,'),
        ...     (6, ')'),
        ... ])))
        >>> assert parsed == [
        ...     ('from __future__ import unicode_literals', [1]),
        ...     ('import os.path', [2]),
        ...     ('from datetime import date,datetime', [3, 4, 5, 6])
        ... ]
    """
    while True:

        try:
            line_number, line = next(iterator)
        except StopIteration:
            break

        # if no imports found on line, ignore
        if not any([line.startswith('from '),
                    line.startswith('import ')]):
            continue

        line_numbers = [line_number]
        line_imports = [line]

        # if parenthesis found, consider new lines
        # until matching closing parenthesis is found
        if '(' in line and ')' not in line:
            while ')' not in line:
                line_number, line = next(iterator)
                line_numbers.append(line_number)
                line_imports.append(line)

        # if new line escape is found, consider new lines
        # until no escape character is found
        if line.endswith('\\'):
            while line.endswith('\\'):
                line_number, line = next(iterator)
                line_numbers.append(line_number)
                line_imports.append(line)

        # remove unneeded characters
        line_imports = map(lambda i: CHARS.sub('', i), line_imports)

        # now that extra characters are removed
        # strip each line
        line_imports = list_strip(line_imports)

        # if line ended with "import\"
        # that will result in incorrect join
        # so explicitly add space after "import"
        # note this has to be after stripping each line
        line_imports = map(lambda i: (i if not i.endswith(' import')
                                      else i + ' '),
                           line_imports)

        import_line = ''.join(line_imports)

        # strip ending comma if there
        if import_line.endswith(','):
            import_line = import_line[:-1]

        yield import_line, line_numbers


def parse_statements(iterable):
    """
    Parse iterable into ``ImportStatement`` instances.

    Parameters
    ----------
    iterable : generator
        Generator as returned by ``find_imports_from_lines``

    Returns
    -------
    statements : generator
        Generator which yields ``ImportStatement`` instances.
    """
    for import_line, line_numbers in iterable:

        if import_line.startswith('import'):
            stem = import_line.replace('import', '').strip()
            leafs = []

            if stem.startswith('.'):
                stem, leafs_string = DOTS.findall(stem)[0]

                # handle ``import .foo.bar``
                leafs_split = leafs_string.rsplit('.', 1)
                if len(leafs_split) == 2:
                    stem += leafs_split[0]
                    leafs_string = leafs_split[1]

                leafs.append(ImportLeaf(leafs_string))

            else:
                # handle ``import a.b.c.d``
                stem_split = stem.rsplit('.', 1)
                if len(stem_split) == 2:
                    stem = stem_split[0]
                    leafs_string = stem_split[1]
                    leafs.append(ImportLeaf(leafs_string))

            # handle when ``as`` is present and is unnecessary
            # in import without leafs
            # e.g. ``import foo as foo``
            # if leaf is present, leaf will take care of normalization
            if ' as ' in stem and not leafs:
                name, as_name = stem.split(' as ')
                if name == as_name:
                    stem = name

            statement = ImportStatement(line_numbers, stem, leafs)

        else:
            stem, leafs_string = list_strip(
                import_line.replace('from', '').split('import')
            )
            leafs = filter(None, list_strip(leafs_string.split(',')))
            leafs = list(map(ImportLeaf, leafs))

            statement = ImportStatement(line_numbers, stem, leafs)

        yield statement
