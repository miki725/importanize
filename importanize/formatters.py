# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

import itertools
import operator
import re


class Formatter(object):
    """Parent class for all formatters

    Parameters
    ----------
    statement : ImportStatement instance

    """
    def __init__(self, statement):
        self.statement = statement

    def init(self):
        """Rename some statement attributes to simplify code."""
        self.leafs = self.statement.unique_leafs
        self.stem = self.statement.stem
        self.comments = self.statement.comments
        self.string = self.statement.as_string()
        self.file_artifacts = self.statement.file_artifacts.get('sep', '\n')

    def get_normalized(self, i):
        return map(operator.attrgetter('normalized'), i)




class IndentWithTabsFormatter(Formatter):
    """Default formatter used to organize long imports

    Imports are added one by line preceded by 4 spaces, here's a sample output:

    from other.package.subpackage.module.submodule import (  # noqa
        CONSTANT,
        Klass,
        bar,
        foo,
        rainbows,
    )
    """

    def format(self):
        self.init()

        all_comments = (
            self.comments + list(itertools.chain(
                *list(map(operator.attrgetter('comments'), self.leafs))
            ))
        )

        if len(all_comments) == 1:
            self.string += '  # {}'\
                .format(' '.join(self.get_normalized(all_comments)))

        if any((len(self.string) > 80 and len(self.leafs) > 1,
                len(all_comments) > 1)):
            sep = '{}    '.format(self.file_artifacts)

            self.string = 'from {} import ('.format(self.stem)

            if self.comments:
                self.string += '  # {}'.format(' '.join(
                    self.get_normalized(self.comments)
                ))

            for leaf in self.leafs:
                self.string += sep

                first_comments = list(filter(
                    lambda i: i.is_comment_first,
                    leaf.comments
                ))
                if first_comments:
                    self.string += sep.join(
                        '# {}'.format(i)
                        for i in self.get_normalized(first_comments)
                    ) + sep

                self.string += '{},'.format(leaf.as_string())

                inline_comments = list(filter(
                    lambda i: not i.is_comment_first,
                    leaf.comments
                ))
                if inline_comments:
                    self.string += '  # {}'.format(
                        ' '.join(self.get_normalized(inline_comments))
                    )

            self.string += '{})'.format(self.file_artifacts)

        return self.string


class VerticalHangingFormatter(Formatter):
    pass
    #def format(self):
        #string = self.statement.as_string()
        #self.get_normalized = lambda i: map(
            #operator.attrgetter('normalized'), i
        #)

        #all_comments = (
            #self.comments + list(itertools.chain(
                #*list(map(operator.attrgetter('comments'), self.leafs))
            #))
        #)

        #if len(all_comments) == 1:
            #self.string += '  # {}'.format(' '.join(self.get_normalized(all_comments)))

        #if any((len(self.string) > 80 and len(self.leafs) > 1,
                #len(all_comments) > 1)):

            #self.string = 'from {} import ('.format(self.stem)

            #sep = '{0}{1}'.format(self.file_artifacts, #' ' * len(self.string))

            #if self.comments:
                #self.string += '  # {}'.format(' '.join(
                    #self.get_normalized(self.comments)
                #))

            #for leaf in self.leafs:
                #self.string += sep

                #first_comments = list(filter(
                    #lambda i: i.is_comment_first,
                    #leaf.comments
                #))
                #if first_comments:
                    #self.string += sep.join(
                        #'# {}'.format(i)
                        #for i in self.get_normalized(first_comments)
                    #) + sep

                #self.string += '{},'.format(leaf.as_string())

                #inline_comments = list(filter(
                    #lambda i: not i.is_comment_first,
                    #leaf.comments
                #))
                #if inline_comments:
                    #self.string += '  # {}'.format(
                        #' '.join(self.get_normalized(inline_comments))
                    #)

            #self.string += '{})'.format(sep)

            ## Check if lines doesn't exceed 80 characters
            #needs_reformat = False
            #for line in self.string.split(self.file_artifacts):
                #if len(line) > 80:
                    #needs_reformat = True

            #if needs_reformat:
                #tab_sep = '{}    '.format(self.file_artifacts)
                #self.string = re.sub(sep, tab_sep, self.string)

        #return self.string
