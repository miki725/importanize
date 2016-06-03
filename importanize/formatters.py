# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
import itertools
import operator
from copy import deepcopy


def get_normalized(i):
    return map(operator.attrgetter('normalized'), i)


class Formatter(object):
    """
    Parent class for all formatters

    Parameters
    ----------
    statement : ImportStatement
        This is the data-structure which store information about
        the import statement that must be formatted
    """

    def __init__(self, statement):
        self.statement = statement


class GroupedFormatter(Formatter):
    """
    Default formatter used to organize long imports

    Imports are added one by line preceded by 4 spaces, here's a sample output:

    from other.package.subpackage.module.submodule import (
        CONSTANT,
        Klass,
        bar,
        foo,
        rainbows,
    )
    """
    name = 'grouped'

    def __init__(self, *args, **kwargs):
        super(GroupedFormatter, self).__init__(*args, **kwargs)

        self.leafs = self.statement.unique_leafs
        self.stem = self.statement.stem
        self.comments = self.statement.comments
        self.string = self.statement.as_string()
        self.sep = self.statement.file_artifacts.get('sep', '\n')

        self.all_comments = (
            self.comments + list(itertools.chain(
                *list(map(operator.attrgetter('comments'), self.leafs))
            ))
        )

    def do_grouped_formatting(self, one_liner):
        return any((len(one_liner) > 80 and len(self.leafs) > 1,
                    len(self.all_comments) > 1))

    def get_leaf_separator(self, stem=None):
        return '{}    '.format(self.sep)

    def format_as_one_liner(self):
        string = self.string

        if len(self.all_comments) == 1:
            string += '  # {}'.format(
                ' '.join(get_normalized(self.all_comments))
            )

        return string

    def format_stem(self):
        return 'from {} import ('.format(self.stem)

    def format_statement_comments(self, sep):
        if self.comments:
            return '  # {}'.format(' '.join(
                get_normalized(self.comments)
            ))
        return ''

    def format_leaf_start(self, leaf, sep):
        return sep

    def format_leaf_end(self, leaf, sep):
        return ''

    def format_leaf_first_comments(self, leaf, sep):
        string = ''

        first_comments = list(filter(
            lambda i: i.is_comment_first,
            leaf.comments
        ))
        if first_comments:
            string += sep.join(
                '# {}'.format(i)
                for i in get_normalized(first_comments)
            ) + sep

        return string

    def format_leaf(self, leaf, sep):
        return '{},'.format(leaf.as_string())

    def format_leaf_inline_comments(self, leaf, sep):
        string = ''

        inline_comments = list(filter(
            lambda i: not i.is_comment_first,
            leaf.comments
        ))
        if inline_comments:
            string += '  # {}'.format(
                ' '.join(get_normalized(inline_comments))
            )

        return string

    def format_wrap_up(self):
        return '{})'.format(self.sep)

    def format_as_grouped(self):
        string = self.format_stem()
        sep = self.get_leaf_separator(string)
        string += self.format_statement_comments(sep)

        for leaf in self.leafs:
            string += self.format_leaf_start(leaf, sep)
            string += self.format_leaf_first_comments(leaf, sep)
            string += self.format_leaf(leaf, sep)
            string += self.format_leaf_inline_comments(leaf, sep)
            string += self.format_leaf_end(leaf, sep)

        string += self.format_wrap_up()

        return string

    def format(self):
        one_liner = self.format_as_one_liner()

        if self.do_grouped_formatting(one_liner):
            return self.format_as_grouped()
        else:
            return one_liner


class GroupedInlineAlignedFormatter(GroupedFormatter):
    """
    Alternative formatter used to organize long imports

    Imports are added one by line and aligned with the opening parenthesis,
    here's a sample output:

    from package.subpackage.module.submodule import (CONSTANT,
                                                     Klass,
                                                     bar,
                                                     foo,
                                                     rainbows)
    """
    name = 'inline-grouped'

    def __new__(cls, statement):
        """
        Overwrite __new__ to return GroupedFormatter formatter instance
        when the statement to be formatted has both statement comment and
        leaf comment. This is a nicer fallback option vs doing super() magic
        in each subclassed function. If some criteria is met, simply use
        a different formatter class.
        """
        if all([statement.comments,
                statement.leafs and statement.leafs[0].comments]):
            return GroupedFormatter(statement)
        return super(GroupedInlineAlignedFormatter, cls).__new__(cls)

    def __init__(self, statement):
        (super(GroupedInlineAlignedFormatter, self)
         .__init__(self.normalize_statement(statement)))

    def normalize_statement(self, statement):
        if all([statement.comments,
                statement.leafs and not statement.leafs[0].comments]):
            statement = deepcopy(statement)
            statement.leafs[0].comments.extend(statement.comments)
            statement.comments = []
        return statement

    def format_leaf_start(self, leaf, sep):
        return ''

    def format_leaf_end(self, leaf, sep):
        if leaf != self.leafs[-1]:
            return sep
        return ''

    def get_leaf_separator(self, stem=None):
        return '{}{}'.format(self.sep, ' ' * len(stem))

    def format_leaf(self, leaf, sep):
        if leaf != self.leafs[-1]:
            f = '{},'
        else:
            f = '{})'
        return f.format(leaf.as_string())

    def format_wrap_up(self):
        return ''


DEFAULT_FORMATTER = GroupedFormatter
