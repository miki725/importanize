# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
import itertools
import operator


def get_normalized(i):
    return map(operator.attrgetter('normalized'), i)


class Formatter(object):
    """Parent class for all formatters

    Parameters
    ----------
    statement : ImportStatement
        This is the data-structure which store information about
        the import statement that must be formatted
    """

    def __init__(self, statement):
        self.statement = statement


class GroupedFormatter(Formatter):
    """Default formatter used to organize long imports

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

    def format(self):
        leafs = self.statement.unique_leafs
        stem = self.statement.stem
        comments = self.statement.comments
        string = self.statement.as_string()
        file_artifacts = self.statement.file_artifacts.get('sep', '\n')

        all_comments = (
            comments + list(itertools.chain(
                *list(map(operator.attrgetter('comments'), leafs))
            ))
        )

        if len(all_comments) == 1:
            string += '  # {}'.format(' '.join(get_normalized(all_comments)))

        if any((len(string) > 80 and len(leafs) > 1,
                len(all_comments) > 1)):
            sep = '{}    '.format(file_artifacts)

            string = 'from {} import ('.format(stem)

            if comments:
                string += '  # {}'.format(' '.join(
                    get_normalized(comments)
                ))

            for leaf in leafs:
                string += sep

                first_comments = list(filter(
                    lambda i: i.is_comment_first,
                    leaf.comments
                ))
                if first_comments:
                    string += sep.join(
                        '# {}'.format(i)
                        for i in get_normalized(first_comments)
                    ) + sep

                string += '{},'.format(leaf.as_string())

                inline_comments = list(filter(
                    lambda i: not i.is_comment_first,
                    leaf.comments
                ))
                if inline_comments:
                    string += '  # {}'.format(
                        ' '.join(get_normalized(inline_comments))
                    )

            string += '{})'.format(file_artifacts)

        return string


class GroupedInlineAlignedFormatter(Formatter):
    """Alternative formatter used to organize long imports

    Imports are added one by line and aligned with the opening parenthesis,
    here's a sample output:

    from package.subpackage.module.submodule import (CONSTANT,
                                                     Klass,
                                                     bar,
                                                     foo,
                                                     rainbows)
    """
    name = 'inline-group'

    def format(self):
        leafs = self.statement.unique_leafs
        stem = self.statement.stem
        comments = self.statement.comments
        string = self.statement.as_string()
        file_artifacts = self.statement.file_artifacts.get('sep', '\n')

        all_comments = (
            comments + list(itertools.chain(
                *list(map(operator.attrgetter('comments'), leafs))
            ))
        )

        if len(all_comments) == 1:
            string += '  # {}' \
                .format(' '.join(get_normalized(all_comments)))

        if any((len(string) > 80 and len(leafs) > 1,
                len(all_comments) > 1)):

            string = 'from {} import ('.format(stem)

            sep = '{0}{1}'.format(file_artifacts, ' ' * len(string))

            if comments:
                string += '  # {}'.format(' '.join(
                    get_normalized(comments)
                )) + sep
            for leaf in leafs:
                first_comments = list(filter(
                    lambda i: i.is_comment_first,
                    leaf.comments
                ))
                if first_comments:
                    string += sep.join(
                        '# {}'.format(i)
                        for i in get_normalized(first_comments)
                    ) + sep

                if leaf < leafs[-1]:
                    string += '{},'.format(leaf.as_string())
                else:
                    string += '{})'.format(leaf.as_string())

                inline_comments = list(filter(
                    lambda i: not i.is_comment_first,
                    leaf.comments
                ))
                if inline_comments:
                    string += '  # {}'.format(
                        ' '.join(get_normalized(inline_comments))
                    )

                if leaf < leafs[-1]:
                    string += sep

        return string


DEFAULT_FORMATTER = GroupedFormatter
