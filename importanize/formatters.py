# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
import abc
import itertools
import typing
from copy import deepcopy

from .parser import Artifacts
from .statements import ImportLeaf, ImportStatement


if typing.TYPE_CHECKING:
    from .config import Config


class Formatter(metaclass=abc.ABCMeta):
    """
    Parent class for all formatters
    """

    name: str

    def __init__(
        self, statement: "ImportStatement", config: "Config", artifacts: "Artifacts"
    ):
        self.statement = self.normalize_statement(statement)
        self.config = config
        self.artifacts = artifacts

    def normalize_statement(self, statement: "ImportStatement") -> "ImportStatement":
        return statement

    @abc.abstractmethod
    def format(self) -> str:
        """
        Subclasses must implement
        """


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

    def __init__(
        self, statement: ImportStatement, config: "Config", artifacts: "Artifacts"
    ):
        super().__init__(statement=statement, config=config, artifacts=artifacts)

        self.leafs: typing.List[ImportLeaf] = self.statement.unique_leafs
        self.stem: str = self.statement.stem
        self.standalone_comments: typing.List[str] = self.statement.standalone_comments
        self.all_inline_comments: typing.List[str] = self.statement.all_inline_comments
        self.string: str = self.statement.as_string()

        self.all_comments: typing.List[str] = self.all_inline_comments + list(
            itertools.chain(
                *[i.standalone_comments + i.inline_comments for i in self.leafs]
            )
        )

    def do_grouped_formatting(self, one_liner: str) -> bool:
        return any(
            (
                len(one_liner) > self.config.length and len(self.leafs) > 1,
                len(self.all_comments) > 1,
            )
        )

    def get_leaf_separator(self, stem: str) -> str:
        return f"{self.artifacts.sep}    "

    def format_as_one_liner(self) -> str:
        string = self.format_statement_standalone_comments() + self.string

        if self.all_comments:
            string += "  # {}".format(" ".join(self.all_comments)).rstrip()

        return string

    def format_stem(self) -> str:
        return f"from {self.stem} import ("

    def format_statement_standalone_comments(self) -> str:
        if self.standalone_comments:
            return (
                self.artifacts.sep.join(
                    f"# {i}".rstrip() for i in self.standalone_comments
                )
                + self.artifacts.sep
            )
        return ""

    def format_statement_inline_comments(self, sep: str) -> str:
        if self.all_inline_comments:
            return "  # {}".format(" ".join(self.all_inline_comments)).rstrip()
        return ""

    def format_leaf_start(self, leaf: "ImportLeaf", sep: str) -> str:
        return sep

    def format_leaf_end(self, leaf: "ImportLeaf", sep: str) -> str:
        return ""

    def format_leaf_standalone_comments(self, leaf: "ImportLeaf", sep: str) -> str:
        string = ""

        if leaf.standalone_comments:
            string += (
                sep.join(f"# {i}".rstrip() for i in leaf.standalone_comments) + sep
            )

        return string

    def format_leaf(self, leaf: "ImportLeaf", sep: str) -> str:
        return "{},".format(leaf.as_string())

    def format_leaf_inline_comments(self, leaf: "ImportLeaf", sep: str) -> str:
        string = ""

        if leaf.inline_comments:
            string += "  # {}".format(" ".join(leaf.inline_comments)).rstrip()

        return string

    def format_wrap_up(self) -> str:
        return f"{self.artifacts.sep})"

    def format_as_grouped(self) -> str:
        string = self.format_statement_standalone_comments()
        string += self.format_stem()
        sep = self.get_leaf_separator(string.splitlines()[-1])
        string += self.format_statement_inline_comments(sep)

        for leaf in self.leafs:
            string += self.format_leaf_start(leaf, sep)
            string += self.format_leaf_standalone_comments(leaf, sep)
            string += self.format_leaf(leaf, sep)
            string += self.format_leaf_inline_comments(leaf, sep)
            string += self.format_leaf_end(leaf, sep)

        string += self.format_wrap_up()

        return string

    def format(self) -> str:
        one_liner = self.format_as_one_liner()

        if self.do_grouped_formatting(one_liner.splitlines()[-1]):
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

    def __new__(  # type: ignore
        cls, statement: "ImportStatement", **kwargs: typing.Any
    ) -> Formatter:
        """
        Overwrite __new__ to return GroupedFormatter formatter instance
        when the statement to be formatted has both statement inline comment and
        leaf comment. It is necessary since otherwise when parsing import back
        it will be impossible to separate both comments.
        This is a nicer fallback option vs doing super() magic
        in each subclassed function. If some criteria is met, simply use
        a different formatter class.

        For example::

            from other.package.subpackage.module.submodule import (  # noqa
                CONSTANT,  # inline
            )
        """
        if all(
            [
                statement.all_inline_comments,
                (
                    statement.leafs
                    and (
                        statement.leafs[0].standalone_comments
                        or statement.leafs[0].inline_comments
                    )
                ),
            ]
        ):
            return GroupedFormatter(statement, **kwargs)
        return typing.cast(GroupedInlineAlignedFormatter, super().__new__(cls))

    def normalize_statement(self, statement: "ImportStatement") -> "ImportStatement":
        if all(
            [
                statement.all_inline_comments,
                (
                    statement.leafs
                    and not statement.leafs[0].standalone_comments
                    and not statement.leafs[0].inline_comments
                ),
            ]
        ):
            statement = deepcopy(statement)
            statement.leafs[0].inline_comments.extend(statement.all_inline_comments)
            statement.inline_comments = []
            for i in statement.leafs:
                i.statement_comments = []
        return statement

    def format_leaf_start(self, leaf: "ImportLeaf", sep: str) -> str:
        return ""

    def format_leaf_end(self, leaf: "ImportLeaf", sep: str) -> str:
        if leaf != self.leafs[-1]:
            return sep
        return ""

    def get_leaf_separator(self, stem: str) -> str:
        return "{}{}".format(self.artifacts.sep, " " * len(stem))

    def format_leaf(self, leaf: "ImportLeaf", sep: str) -> str:
        if leaf != self.leafs[-1]:
            f = "{},"
        else:
            f = "{})"
        return f.format(leaf.as_string())

    def format_wrap_up(self) -> str:
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

    def __init__(
        self, statement: "ImportStatement", config: "Config", artifacts: "Artifacts"
    ):
        super().__init__(statement=statement, config=config, artifacts=artifacts)

        self.statements = self.split_to_statements(self.statement)

    def split_to_statements(
        self, statement: "ImportStatement"
    ) -> typing.List["ImportStatement"]:
        statements = []

        for i, leaf in enumerate(statement.unique_leafs):
            s = deepcopy(statement)
            s.leafs = [leaf]
            if i:
                s.standalone_comments = []
            statements.append(s)

        return statements or [statement]

    def format(self) -> str:
        return self.artifacts.sep.join(
            [
                GroupedFormatter(
                    statement=statement, config=self.config, artifacts=self.artifacts
                ).format_as_one_liner()
                for statement in self.statements
            ]
        )


FORMATTERS: typing.Dict[str, typing.Type[Formatter]] = {
    formatter.name: formatter
    for formatter in globals().values()
    if (
        isinstance(formatter, type)
        and formatter is not Formatter
        and issubclass(formatter, Formatter)
    )
}
