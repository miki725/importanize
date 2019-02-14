# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
import operator
import re
from functools import total_ordering

import six

from .formatters import DEFAULT_FORMATTER, DEFAULT_LENGTH


DOTS = re.compile(r"^(\.+)(.*)")


class BaseImport(object):
    def __init__(self, pre_comments=None, inline_comments=None):
        self.pre_comments = pre_comments or []
        self.inline_comments = inline_comments or []

    @property
    def comments(self):
        return self.pre_comments + self.inline_comments

    def __repr__(self):
        return str(
            "<{} {}>"
            "".format(
                self.__class__.__name__,
                (
                    "\n    "
                    + ",\n    ".join(
                        "{}={!r}".format(k, v) for k, v in vars(self).items()
                    )
                    if self.strict
                    else repr(self.as_string())
                ),
            )
        )


@total_ordering
@six.python_2_unicode_compatible
class ImportLeaf(BaseImport):
    """
    Data-structure about each import statement leaf-module.

    For example, if import statement is
    ``from foo.bar import rainbows``, leaf-module is
    ``rainbows``.
    Also aliased modules are supported (e.g. using ``as``).
    """

    def __init__(self, name, as_name=None, **kwargs):
        if name == as_name:
            as_name = None

        self.name = name
        self.as_name = as_name
        self.strict = kwargs.pop("strict", False)

        super(ImportLeaf, self).__init__(**kwargs)

    def as_string(self):
        string = self.name
        if self.as_name:
            string += " as {}".format(self.as_name)
        return string

    def __str__(self):
        return self.as_string()

    def __hash__(self):
        return hash(self.as_string())

    def __eq__(self, other):
        params = [self.name == other.name, self.as_name == other.as_name]
        if self.strict:
            params += [
                self.pre_comments == other.pre_comments,
                self.inline_comments == other.inline_comments,
            ]
        return all(params)

    def __gt__(self, other):
        def _type(obj):
            if obj.name.isupper():
                return "upper"
            elif obj.name.islower():
                return "lower"
            else:
                return "mixed"

        self_type = _type(self)
        other_type = _type(other)

        priority = ("upper", "mixed", "lower")

        if self_type != other_type:
            return priority.index(self_type) > priority.index(other_type)

        return self.name > other.name


@total_ordering
@six.python_2_unicode_compatible
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
        self, stem, as_name=None, leafs=None, line_numbers=None, **kwargs
    ):
        if leafs or stem == as_name:
            as_name = None

        self.line_numbers = line_numbers or []
        self.stem = stem
        self.as_name = as_name
        self.leafs = leafs or []
        self.file_artifacts = kwargs.pop("file_artifacts", {})
        self.strict = kwargs.pop("strict", False)

        super(ImportStatement, self).__init__(**kwargs)

    @property
    def full_stem(self):
        stem = self.stem
        if self.as_name:
            stem += " as {}".format(self.as_name)
        return stem

    @property
    def unique_leafs(self):
        return sorted(list(set(self.leafs)))

    @property
    def root_module(self):
        """
        Root module being imported.
        This is used to sort imports as well as to
        determine to which import group this import
        belongs to.
        """
        return self.stem.split(".", 1)[0]

    def as_string(self):
        if not self.leafs:
            return "import {}".format(self.full_stem)
        else:
            return "from {} import {}" "".format(
                self.stem,
                ", ".join(
                    map(operator.methodcaller("as_string"), self.unique_leafs)
                ),
            )

    def formatted(self, formatter=DEFAULT_FORMATTER, length=DEFAULT_LENGTH):
        return formatter(self, length=length).format()

    def __hash__(self):
        return hash(self.as_string())

    def __str__(self):
        return self.as_string()

    def __add__(self, other):
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
            pre_comments=self.pre_comments + other.pre_comments,
            inline_comments=self.inline_comments + other.inline_comments,
        )

    def __eq__(self, other):
        params = [
            self.stem == other.stem,
            self.as_name == other.as_name,
            self.unique_leafs == other.unique_leafs,
        ]
        if self.strict:
            params += [
                self.pre_comments == other.pre_comments,
                self.inline_comments == other.inline_comments,
            ]
        return all(params)

    def __gt__(self, other):
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
