# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
import re

from .exceptions import MultipleImportsError
from .statements import DOTS, ImportLeaf, ImportStatement
from .utils import list_strip


CHARS = re.compile(r'[\\()]')


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

        if import_line.startswith('import '):
            stem = import_line.replace('import ', '').strip()
            leafs = []

            if ',' in stem:
                msg = ('There are multiple imports in a single line "{}" '
                       'which violates PEP8 (http://bitly.com/pep8)')
                raise MultipleImportsError(msg.format(import_line))

            if stem.startswith('.'):
                stem, leafs_string = DOTS.findall(stem)[0]

                # handle ``import .foo.bar``
                leafs_split = leafs_string.rsplit('.', 1)
                if len(leafs_split) == 2:
                    stem += leafs_split[0]
                    leafs_string = leafs_split[1]

                leafs.append(ImportLeaf(leafs_string))

            else:
                # handle ``import a.b as c``
                stem_split = stem.rsplit('.', 1)
                if len(stem_split) == 2 and ' as ' in stem:
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
                import_line.replace('from ', '').split(' import ')
            )
            leafs = filter(None, list_strip(leafs_string.split(',')))
            leafs = list(map(ImportLeaf, leafs))

            statement = ImportStatement(line_numbers, stem, leafs)

        yield statement
