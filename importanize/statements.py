# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
import abc
import itertools
import re
import typing
from functools import reduce, total_ordering

from .utils import list_set


DOTS = re.compile(r"^(\.+)(.*)")


class BaseImport(metaclass=abc.ABCMeta):
    """
    Base class for import classes

    Adds common comment arguments and common representation
    """

    def __init__(
        self,
        standalone_comments: typing.List[str] = None,
        inline_comments: typing.List[str] = None,
        strict: bool = False,
    ):
        self.standalone_comments = standalone_comments or []
        self.inline_comments = inline_comments or []
        self.strict = strict

    def __repr__(self) -> str:
        return str(
            "<{} {}>"
            "".format(
                self.__class__.__name__,
                (
                    "\n    "
                    + ",\n    ".join(f"{k}={v!r}" for k, v in vars(self).items())
                    if self.strict
                    else repr(self.as_string())
                ),
            )
        )

    @abc.abstractmethod
    def as_string(self) -> str:
        """
        Subclasses must implement
        """


@total_ordering
class ImportLeaf(BaseImport):
    """
    Data-structure about each import statement leaf-module.

    For example, if import statement is
    ``from foo.bar import rainbows``, leaf-module is
    ``rainbows``.
    Also aliased modules are supported (e.g. using ``a as b``).
    """

    def __init__(
        self,
        name: str,
        as_name: str = None,
        standalone_comments: typing.List[str] = None,
        inline_comments: typing.List[str] = None,
        statement_comments: typing.List[str] = None,
        strict: bool = False,
    ):
        if name == as_name:
            as_name = None

        self.name = name
        self.as_name = as_name

        self.statement_comments = statement_comments or []

        super().__init__(
            standalone_comments=standalone_comments,
            inline_comments=inline_comments,
            strict=strict,
        )

    def as_string(self) -> str:
        string = self.name
        if self.as_name:
            string += f" as {self.as_name}"
        return string

    def __str__(self) -> str:
        return self.as_string()

    def __hash__(self) -> int:
        return hash(self.as_string())

    def __add__(self, other: "ImportLeaf") -> "ImportLeaf":
        return ImportLeaf(
            name=self.name,
            as_name=self.as_name,
            standalone_comments=list_set(
                self.standalone_comments + other.standalone_comments
            ),
            inline_comments=list_set(self.inline_comments + other.inline_comments),
            statement_comments=list_set(
                self.statement_comments + other.statement_comments
            ),
            strict=self.strict,
        )

    def __eq__(self, other: "ImportLeaf") -> bool:  # type: ignore
        params = [self.name == other.name, self.as_name == other.as_name]
        if self.strict:
            params += [
                self.standalone_comments == other.standalone_comments,
                self.inline_comments == other.inline_comments,
                self.statement_comments == other.statement_comments,
            ]
        return all(params)

    def __gt__(self, other: "ImportLeaf") -> bool:
        def _type(obj: "ImportLeaf") -> str:
            if obj.name.isupper():
                return "upper"
            elif obj.name.islower():
                return "lower"
            else:
                return "mixed"

        self_type = _type(self)
        other_type = _type(other)

        priority = ("upper", "mixed", "lower")

        if self_type is not other_type:
            return priority.index(self_type) > priority.index(other_type)

        return (self.name, self.as_name or "") > (other.name, other.as_name or "")


@total_ordering
class ImportStatement(BaseImport):
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

    def __init__(
        self,
        stem: str,
        as_name: str = None,
        leafs: typing.List[ImportLeaf] = None,
        line_numbers: typing.List[int] = None,
        standalone_comments: typing.List[str] = None,
        inline_comments: typing.List[str] = None,
        strict: bool = False,
    ):
        if leafs or stem == as_name:
            as_name = None

        self.line_numbers = line_numbers or []
        self.stem = stem
        self.as_name = as_name
        self.leafs: typing.List[ImportLeaf] = leafs or []

        super().__init__(
            standalone_comments=standalone_comments,
            inline_comments=inline_comments,
            strict=strict,
        )

    @property
    def full_stem(self) -> str:
        return f"{self.stem}" if not self.as_name else f"{self.stem} as {self.as_name}"

    @property
    def unique_leafs(self) -> typing.List[ImportLeaf]:
        return [
            reduce(lambda a, b: a + b, leafs)
            for _, leafs in itertools.groupby(
                sorted(self.leafs), key=lambda i: (i.name, i.as_name)
            )
        ]

    @property
    def all_inline_comments(self) -> typing.List[str]:
        return (
            list_set(itertools.chain(*[i.statement_comments for i in self.leafs]))
            + self.inline_comments
        )

    @property
    def root_module(self) -> str:
        """
        Root module being imported.
        This is used to sort imports as well as to
        determine to which import group this import
        belongs to.
        """
        return self.stem.split(".", 1)[0]

    def with_line_numbers(self, line_numbers: typing.List[int]) -> "ImportStatement":
        self.line_numbers = line_numbers
        return self

    def as_string(self) -> str:
        if not self.leafs:
            return f"import {self.full_stem}"
        else:
            return "from {} import {}".format(
                self.stem, ", ".join(i.as_string() for i in self.unique_leafs)
            )

    def __hash__(self) -> int:
        return hash(self.as_string())

    def __str__(self) -> str:
        return self.as_string()

    def __add__(self, other: "ImportStatement") -> "ImportStatement":
        """
        Combined two import statements into a single statement.
        This requires both import statements to have the same stem.
        """
        assert self.stem == other.stem
        assert self.as_name == other.as_name

        return ImportStatement(
            line_numbers=self.line_numbers + other.line_numbers,
            stem=self.stem,
            leafs=self.leafs + other.leafs,
            standalone_comments=self.standalone_comments + other.standalone_comments,
            inline_comments=self.inline_comments + other.inline_comments,
        )

    def __eq__(self, other: "ImportStatement") -> bool:  # type: ignore
        params = [
            self.stem == other.stem,
            self.as_name == other.as_name,
            self.unique_leafs == other.unique_leafs,
        ]
        if self.strict:
            params += [
                self.standalone_comments == other.standalone_comments,
                self.inline_comments == other.inline_comments,
            ]
        return all(params)

    def __gt__(self, other: "ImportStatement") -> bool:
        """
        Follows the following rules:

        * ``__future__`` is always first
        * ``import ..`` is ahead of ``from .. import ..`` imports
        * ``import ..a`` is ahead of ``import .a``
        * local imports are below regular imports
        * otherwise root_module is alphabetically compared
        """
        # same stem so compare sorted first leafs, if there
        if self.stem == other.stem and self.leafs and other.leafs:
            return sorted(self.leafs)[0] > sorted(other.leafs)[0]

        # check for __future__
        if self.root_module == "__future__":
            return False
        elif other.root_module == "__future__":
            return True

        # local imports
        if all([self.stem.startswith("."), other.stem.startswith(".")]):
            # double dot import should be ahead of single dot
            # so only make comparison when different number of dots
            self_local = DOTS.findall(self.stem)[0][0]
            other_local = DOTS.findall(other.stem)[0][0]
            if len(self_local) != len(other_local):
                return len(self_local) < len(other_local)

        # only one is local import
        if any(
            [
                not self.stem.startswith(".") and other.stem.startswith("."),
                self.stem.startswith(".") and not other.stem.startswith("."),
            ]
        ):
            return self.stem.startswith(".")

        # check for ``import ..`` vs ``from .. import ..``
        self_len = len(self.leafs)
        other_len = len(other.leafs)
        if any([not self_len and other_len, self_len and not other_len]):
            return self_len > other_len

        # alphabetical sort
        return self.full_stem > other.full_stem
