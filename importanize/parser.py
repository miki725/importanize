# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
import re

from .statements import DOTS, ImportLeaf, ImportStatement
from .utils import list_strip, read


CHARS = re.compile(r'[\\()]')


def get_artifacts(path):
    """
    Get artifacts for the given file.

    Parameters
    ----------
    path : str
        Path to a file

    Returns
    -------
    artifacts : dict
        Dictionary of file artifacts which should be
        considered while processing imports.
    """
    artifacts = {
        'sep': '\n',
    }

    lines = read(path).splitlines(True)
    if len(lines) > 1 and lines[0][-2:] == '\r\n':
        artifacts['sep'] = '\r\n'

    return artifacts


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
            return

        # ignore comment blocks
        triple_quote = line.find('"""')
        if triple_quote >= 0 and line.find('"""', triple_quote + 3) < 0:
            inside_comment = True
            while inside_comment:
                try:
                    line_number, line = next(iterator)
                except StopIteration:
                    return
                inside_comment = not line.endswith('"""')
            # get the next line since previous is an end of a comment
            try:
                line_number, line = next(iterator)
            except StopIteration:
                return

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

        # handle line breaks which can cause
        # incorrect syntax when recombined
        # mostly these are cases when line break
        # happens around either "import" or "as"
        # e.g. from long.import.here \n import foo
        # e.g. import package \n as foo
        for word in ('import', 'as'):
            kwargs = {
                'startswith': {
                    'word': word,
                    'pre': '',
                    'post': ' ',
                },
                'endswith': {
                    'word': word,
                    'pre': ' ',
                    'post': '',
                }
            }
            for f, k in kwargs.items():
                line_imports = list(map(
                    lambda i: (i if not getattr(i, f)('{pre}{word}{post}'
                                                      ''.format(**k))
                               else '{post}{i}{pre}'.format(i=i, **k)),
                    line_imports
                ))

        import_line = ''.join(line_imports).strip()

        # strip ending comma if there
        if import_line.endswith(','):
            import_line = import_line[:-1]

        yield import_line, line_numbers


def parse_import_statement(stem, line_numbers, **kwargs):
    """
    Parse single import statement into ``ImportStatement`` instances.

    Parameters
    ----------
    stem : str
        Import line stem which excludes ``"import"``.
        For example for ``import a`` import, simply ``a``
        should be passed.
    line_numbers : list
        List of line numbers which normalized to import stem.

    Returns
    -------
    statement : ImportStatement
        ``ImportStatement`` instances.
    """
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

    return ImportStatement(line_numbers,
                           stem,
                           leafs,
                           **kwargs)


def parse_statements(iterable, **kwargs):
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
            stems = import_line.replace('import ', '').strip().split(',')

            for stem in stems:
                yield parse_import_statement(stem.strip(),
                                             line_numbers,
                                             **kwargs)

        else:
            stem, leafs_string = list_strip(
                import_line.replace('from ', '').split(' import ')
            )
            leafs = filter(None, list_strip(leafs_string.split(',')))
            leafs = list(map(ImportLeaf, leafs))

            yield ImportStatement(line_numbers,
                                  stem,
                                  leafs,
                                  **kwargs)
