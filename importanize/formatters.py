# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

import operator
import itertools


class Formatter(object):
    def __init__(self, statement):
        self.statement = statement


class IndentWithTabsFormatter(Formatter):
    def format(self):
        leafs = self.statement.unique_leafs
        string = self.statement.as_string()
        get_normalized = lambda i: map(
            operator.attrgetter('normalized'), i
        )

        all_comments = (
            self.statement.comments + list(itertools.chain(
                *list(map(operator.attrgetter('comments'), leafs))
            ))
        )

        if len(all_comments) == 1:
            string += '  # {}'.format(' '.join(get_normalized(all_comments)))

        if any((len(string) > 80 and len(leafs) > 1,
                len(all_comments) > 1)):
            sep = '{}    '.format(self.statement.file_artifacts.get('sep', '\n'))

            string = 'from {} import ('.format(self.statement.stem)

            if self.statement.comments:
                string += '  # {}'.format(' '.join(
                    get_normalized(self.statement.comments)
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

            string += '{})'.format(self.statement.file_artifacts.get('sep', '\n'))

        return string


class VerticalHangingFormatter(Formatter):
    def formatted(self):
        leafs = self.unique_leafs
        string = self.as_string()
        get_normalized = lambda i: map(
            operator.attrgetter('normalized'), i
        )

        all_comments = (
            self.comments + list(itertools.chain(
                *list(map(operator.attrgetter('comments'), leafs))
            ))
        )

        if len(all_comments) == 1:
            string += '  # {}'.format(' '.join(get_normalized(all_comments)))

        if any((len(string) > 80 and len(leafs) > 1,
                len(all_comments) > 1)):

            string = 'from {} import ('.format(self.stem)

            sep = '{0}{1}'.format(self.file_artifacts.get('sep', '\n'),
                                  ' '*len(string))

            if self.comments:
                string += '  # {}'.format(' '.join(
                    get_normalized(self.comments)
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

            string += '{})'.format(sep)

            # Check if lines doesn't exceed 80 characters
            needs_reformat = False
            for line in string.split(self.file_artifacts.get('sep', '\n')):
                if len(line) > 80:
                    needs_reformat = True

            if needs_reformat:
                tab_sep = '{}    '.format(self.file_artifacts.get('sep', '\n'))
                string = re.sub(sep, tab_sep, string)

        return string
