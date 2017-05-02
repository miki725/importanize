# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
import re

import six

from .statements import DOTS, ImportLeaf, ImportStatement
from .utils import list_split


STATEMENT_COMMENTS = ('noqa',)
TOKEN_REGEX = re.compile(r' +|[\(\)]|([,\\])|(#.*)')
SPECIAL_TOKENS = (',', 'import', 'from', 'as')


class Token(six.text_type):
    def __new__(cls, value, **kwargs):
        obj = six.text_type.__new__(cls, value)
        obj.is_comment_first = False
        for k, v in kwargs.items():
            setattr(obj, k, v)
        return obj

    @property
    def is_comment(self):
        return self.startswith('#')

    @property
    def normalized(self):
        if not self.is_comment:
            return self
        else:
            if self.startswith('# '):
                return self[2:]
            else:
                return self[1:]


def get_text_artifacts(text):
    """
    Get artifacts for the given file.

    Parameters
    ----------
    path : str
        File content to analyze

    Returns
    -------
    artifacts : dict
        Dictionary of file artifacts which should be
        considered while processing imports.
    """
    artifacts = {
        'sep': '\n',
    }

    lines = text.splitlines(True)
    if len(lines) > 1 and lines[0][-2:] == '\r\n':
        artifacts['sep'] = '\r\n'

    return artifacts


def find_imports_from_lines(iterator):
    """
    Find only import statements from enumerated iterator of file files.

    Parameters
    ----------
    iterator : generator
        Enumerated iterator which yield items
        ``(line_number, line_string)``

    Returns
    -------
    imports : generator
        Iterator which yields tuple of lines strings composing
        a single import statement as well as teh line numbers
        on which the import statement was found.
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

        paren_count = line.count('(') - line.count(')')

        def read_line(paren_count):
            line_number, line = next(iterator)
            line_numbers.append(line_number)
            line_imports.append(line)

            paren_count += line.count('(')
            paren_count -= line.count(')')

            return line, paren_count

        while paren_count > 0 or line.endswith('\\'):
            line, paren_count = read_line(paren_count)

        yield line_imports, line_numbers


def tokenize_import_lines(import_lines):
    tokens = []

    for n, line in enumerate(import_lines):
        _tokens = []
        words = filter(None, TOKEN_REGEX.split(line))

        for i, word in enumerate(words):
            token = Token(word)
            # tokenize same-line comments before "," to allow to associate
            # a comment with specific import since pure Python
            # syntax does not do that because # has to be after ","
            # hence when tokenizing, comment will be associated
            # with next import which is not desired
            if token.is_comment and _tokens and _tokens[max(i - 1, 0)] == ',':
                _tokens.insert(i - 1, token)
            else:
                _tokens.append(token)

        tokens.extend(_tokens)

    # combine tokens between \\ newline escape
    segments = list_split(tokens, '\\')
    tokens = [Token('')]
    for i, segment in enumerate(segments):
        # don't add to previous token if it is a ","
        if all((tokens[-1] not in SPECIAL_TOKENS,
                not i or segment[0] not in SPECIAL_TOKENS)):
            tokens[-1] += segment[0]
        else:
            tokens.append(segment[0])
        tokens += segment[1:]

    return [Token(i) for i in tokens]


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
    def get_comments(j):
        return filter(lambda i: i.is_comment, j)

    def get_not_comments(j):
        return filter(lambda i: not i.is_comment, j)

    def get_first_not_comment(j):
        return next(
            iter(filter(lambda i: not i.is_comment, j))
        )

    for import_lines, line_numbers in iterable:
        tokens = tokenize_import_lines(import_lines)

        if tokens[0] == 'import':
            for _tokens in list_split(tokens[1:], ','):
                stem = ' '.join(get_not_comments(_tokens))
                comments = get_comments(_tokens)
                yield parse_import_statement(
                    stem=stem,
                    line_numbers=line_numbers,
                    comments=list(comments),
                    **kwargs
                )

        else:
            stem_tokens, leafs_tokens = list_split(tokens[1:], 'import')
            stem = ' '.join(get_not_comments(stem_tokens))
            list_of_leafs = list(list_split(leafs_tokens, ','))
            statement_comments = set()
            leafs = []

            for leaf_list in list_of_leafs:
                first_non_leaf_index = leaf_list.index(
                    get_first_not_comment(leaf_list)
                )
                leaf_stem = ' '.join(get_not_comments(leaf_list))
                comments = []
                all_leaf_comments = filter(lambda i: i.is_comment, leaf_list)

                for comment in all_leaf_comments:
                    if comment.normalized in STATEMENT_COMMENTS:
                        statement_comments.add(comment)
                    else:
                        comment.is_comment_first = (
                            leaf_list.index(comment) < first_non_leaf_index
                        )
                        comments.append(comment)

                leafs.append(ImportLeaf(leaf_stem, comments=comments))

            yield ImportStatement(
                line_numbers=line_numbers,
                stem=stem,
                leafs=leafs,
                comments=list(statement_comments),
                **kwargs
            )
