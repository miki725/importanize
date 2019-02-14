# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
import itertools
import operator
from copy import deepcopy


DEFAULT_LENGTH = 80


class Formatter(object):
    """
    Parent class for all formatters

    Parameters
    ----------
    statement : ImportStatement
        This is the data-structure which store information about
        the import statement that must be formatted
    """

    def __init__(self, statement, length=DEFAULT_LENGTH):
        self.statement = statement
        self.length = length


class GroupedFormatter(Formatter):
    """
    Default formatter used to organize long imports

    Imports are added one by line preceded by 4 spaces, here's a sample output::

        from other.package.subpackage.module.submodule import (
            CONSTANT,
            Klass,
            bar,
            foo,
            rainbows,
        )
    """

    name = "grouped"

    def __init__(self, *args, **kwargs):
        super(GroupedFormatter, self).__init__(*args, **kwargs)

        self.leafs = self.statement.unique_leafs
        self.stem = self.statement.stem
        self.pre_comments = self.statement.pre_comments
        self.inline_comments = self.statement.inline_comments
        self.string = self.statement.as_string()
        self.sep = self.statement.file_artifacts.get("sep", "\n")

        self.all_comments = self.inline_comments + list(
            itertools.chain(
                *list(map(operator.attrgetter("comments"), self.leafs))
            )
        )

    def do_grouped_formatting(self, one_liner):
        return any(
            (
                len(one_liner) > self.length and len(self.leafs) > 1,
                len(self.all_comments) > 1,
            )
        )

    def get_leaf_separator(self, stem=None):
        return "{}    ".format(self.sep)

    def format_as_one_liner(self):
        string = self.format_statement_pre_comments() + self.string

        if self.all_comments:
            string += "  # {}".format(" ".join(self.all_comments))

        return string

    def format_stem(self):
        return "from {} import (".format(self.stem)

    def format_statement_pre_comments(self):
        if self.pre_comments:
            return (
                self.sep.join("# {}".format(i) for i in self.pre_comments)
                + self.sep
            )
        return ""

    def format_statement_inline_comments(self, sep):
        if self.inline_comments:
            return "  # {}".format(" ".join(self.inline_comments))
        return ""

    def format_leaf_start(self, leaf, sep):
        return sep

    def format_leaf_end(self, leaf, sep):
        return ""

    def format_leaf_pre_comments(self, leaf, sep):
        string = ""

        if leaf.pre_comments:
            string += (
                sep.join("# {}".format(i) for i in leaf.pre_comments) + sep
            )

        return string

    def format_leaf(self, leaf, sep):
        return "{},".format(leaf.as_string())

    def format_leaf_inline_comments(self, leaf, sep):
        string = ""

        if leaf.inline_comments:
            string += "  # {}".format(" ".join(leaf.inline_comments))

        return string

    def format_wrap_up(self):
        return "{})".format(self.sep)

    def format_as_grouped(self):
        string = self.format_statement_pre_comments()
        string += self.format_stem()
        sep = self.get_leaf_separator(string)
        string += self.format_statement_inline_comments(sep)

        for leaf in self.leafs:
            string += self.format_leaf_start(leaf, sep)
            string += self.format_leaf_pre_comments(leaf, sep)
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
    here's a sample output::

        from package.subpackage.module.submodule import (CONSTANT,
                                                         Klass,
                                                         bar,
                                                         foo,
                                                         rainbows)
    """

    name = "inline-grouped"

    def __new__(cls, statement, **kwargs):
        """
        Overwrite __new__ to return GroupedFormatter formatter instance
        when the statement to be formatted has both statement comment and
        leaf comment. This is a nicer fallback option vs doing super() magic
        in each subclassed function. If some criteria is met, simply use
        a different formatter class.
        """
        if all(
            [
                statement.comments,
                statement.leafs and statement.leafs[0].comments,
            ]
        ):
            return GroupedFormatter(statement, **kwargs)
        return super(GroupedInlineAlignedFormatter, cls).__new__(cls)

    def __init__(self, statement, **kwargs):
        (
            super(GroupedInlineAlignedFormatter, self).__init__(
                self.normalize_statement(statement), **kwargs
            )
        )

    def normalize_statement(self, statement):
        if all(
            [
                statement.comments,
                statement.leafs and not statement.leafs[0].comments,
            ]
        ):
            statement = deepcopy(statement)
            statement.leafs[0].pre_comments.extend(statement.pre_comments)
            statement.leafs[0].inline_comments.extend(statement.inline_comments)
            statement.pre_comments = []
            statement.inline_comments = []
        return statement

    def format_leaf_start(self, leaf, sep):
        return ""

    def format_leaf_end(self, leaf, sep):
        if leaf != self.leafs[-1]:
            return sep
        return ""

    def get_leaf_separator(self, stem=None):
        return "{}{}".format(self.sep, " " * len(stem))

    def format_leaf(self, leaf, sep):
        if leaf != self.leafs[-1]:
            f = "{},"
        else:
            f = "{})"
        return f.format(leaf.as_string())

    def format_wrap_up(self):
        return ""


class LinesFormatter(Formatter):
    """
    Formatter which outputs each import on an individual line

    Sample output::

        from package.subpackage.module.submodule import CONSTANT
        from package.subpackage.module.submodule import Klass
        from package.subpackage.module.submodule import bar
        from package.subpackage.module.submodule import foo
        from package.subpackage.module.submodule import rainbows
    """

    name = "lines"

    def __init__(self, statement, **kwargs):
        self.kwargs = kwargs

        super(LinesFormatter, self).__init__(statement, **kwargs)

        self.sep = self.statement.file_artifacts.get("sep", "\n")
        self.statements = self.split_to_statements(self.statement)

    def split_to_statements(self, statement):
        statements = []

        for leaf in statement.unique_leafs:
            s = deepcopy(statement)
            s.leafs = [leaf]
            statements.append(s)

        return statements or [statement]

    def format(self):
        return self.sep.join(
            [
                GroupedFormatter(statement, **self.kwargs).format_as_one_liner()
                for statement in self.statements
            ]
        )


DEFAULT_FORMATTER = GroupedFormatter
