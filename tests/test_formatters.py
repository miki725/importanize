# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
import unittest

import mock

from importanize.formatters import (
    Formatter,
    GroupedFormatter,
    GroupedInlineAlignedFormatter,
    LinesFormatter,
)
from importanize.statements import ImportLeaf, ImportStatement


# Define some names for tests purposes
module = "module"
obj1 = "object1"
obj2 = "object2"
long_module = module * 13
long_obj1 = obj1 * 13
long_obj2 = obj2 * 13


class BaseTestFormatter(unittest.TestCase):
    formatter = None

    def _test(
        self,
        stem,
        leafs,
        expected,
        sep="\n",
        inline_comments=None,
        pre_comments=None,
        **kwargs
    ):
        """Facilitate the output tests of formatters"""
        statement = ImportStatement(
            stem,
            leafs=list(
                map(
                    (
                        lambda i: (
                            i if isinstance(i, ImportLeaf) else ImportLeaf(i)
                        )
                    ),
                    leafs,
                )
            ),
            inline_comments=inline_comments,
            pre_comments=pre_comments,
            **kwargs
        )
        self.assertEqual(
            statement.formatted(formatter=self.formatter), sep.join(expected)
        )


class TestFormatter(BaseTestFormatter):
    def test_init(self):
        actual = Formatter(mock.sentinel.statement)
        self.assertEqual(actual.statement, mock.sentinel.statement)


class TestGroupedFormatter(BaseTestFormatter):
    formatter = GroupedFormatter

    def test_formatted(self):
        # Test one-line imports
        self._test(module, [], ["import {}".format(module)])
        self._test(module, [obj1], ["from {} import {}".format(module, obj1)])
        self._test(
            module,
            [obj1, obj2],
            ["from {} import {}, {}".format(module, obj1, obj2)],
        )
        self._test(
            long_module,
            [long_obj1],
            ["from {} import {}".format(long_module, long_obj1)],
        )

        # Test multi-lines imports
        self._test(
            long_module,
            [long_obj1, long_obj2],
            [
                "from {} import (".format(long_module),
                "    {},".format(long_obj1),
                "    {},".format(long_obj2),
                ")",
            ],
        )

        # Test file_artifacts
        self._test(
            long_module,
            [long_obj1, long_obj2],
            [
                "from {} import (".format(long_module),
                "    {},".format(long_obj1),
                "    {},".format(long_obj2),
                ")",
            ],
            sep="\r\n",
            file_artifacts={"sep": "\r\n"},
        )

        # Test imports with comments
        self._test(
            "foo", [], ["import foo  # comment"], inline_comments=["comment"]
        )
        self._test(
            "foo",
            [ImportLeaf("bar", inline_comments=["comment"])],
            ["from foo import bar  # comment"],
        )
        self._test(
            "something",
            [ImportLeaf("foo"), ImportLeaf("bar")],
            ["from something import bar, foo  # noqa"],
            inline_comments=["noqa"],
        )
        self._test(
            "foo",
            [
                ImportLeaf("bar", inline_comments=["hello"]),
                ImportLeaf("rainbows", inline_comments=["world"]),
                ImportLeaf("zz", pre_comments=["and lots of sleep"]),
            ],
            [
                "from foo import (  # noqa",
                "    bar,  # hello",
                "    rainbows,  # world",
                "    # and lots of sleep",
                "    zz,",
                ")",
            ],
            inline_comments=["noqa"],
        )


class TestGroupedInlineAlignedFormatter(BaseTestFormatter):
    formatter = GroupedInlineAlignedFormatter

    def test_formatted(self):
        # Test one-line imports
        self._test(module, [], ["import {}".format(module)])
        self._test(module, [obj1], ["from {} import {}".format(module, obj1)])
        self._test(
            module,
            [obj1, obj2],
            ["from {} import {}, {}".format(module, obj1, obj2)],
        )
        self._test(
            long_module,
            [long_obj1],
            ["from {} import {}".format(long_module, long_obj1)],
        )

        # Test multi-lines imports
        self._test(
            long_module,
            [long_obj1, long_obj2],
            [
                "from {} import ({},".format(long_module, long_obj1),
                "{}{})".format(" " * 92, long_obj2),
            ],
        )

        # Test file_artifacts
        self._test(
            long_module,
            [long_obj1, long_obj2],
            [
                "from {} import ({},".format(long_module, long_obj1),
                "{}{})".format(" " * 92, long_obj2),
            ],
            sep="\r\n",
            file_artifacts={"sep": "\r\n"},
        )

        # Test imports with comments
        self._test(
            "foo", [], ["import foo  # comment"], inline_comments=["comment"]
        )
        self._test(
            "foo",
            [ImportLeaf("bar", inline_comments=["comment"])],
            ["from foo import bar  # comment"],
        )
        self._test(
            "something",
            [ImportLeaf("foo"), ImportLeaf("bar")],
            ["from something import bar, foo  # noqa"],
            inline_comments=["noqa"],
        )
        self._test(
            "foo",
            [
                ImportLeaf("bar", inline_comments=["hello"]),
                ImportLeaf("rainbows", inline_comments=["world"]),
                ImportLeaf("zz", pre_comments=["and lots of sleep"]),
            ],
            [
                "from foo import (  # noqa",
                "    bar,  # hello",
                "    rainbows,  # world",
                "    # and lots of sleep",
                "    zz,",
                ")",
            ],
            inline_comments=["noqa"],
        )
        self._test(
            "foo",
            [
                ImportLeaf("bar", inline_comments=["hello"]),
                ImportLeaf("rainbows", inline_comments=["world"]),
                ImportLeaf("zzz", inline_comments=["and lots of sleep"]),
            ],
            [
                "from foo import (  # noqa",
                "    bar,  # hello",
                "    rainbows,  # world",
                "    zzz,  # and lots of sleep",
                ")",
            ],
            inline_comments=["noqa"],
        )
        self._test(
            "foo",
            [ImportLeaf("bar"), ImportLeaf("rainbows"), ImportLeaf(long_obj1)],
            [
                "from foo import (bar,  # noqa",
                "                 {},".format(long_obj1),
                "                 rainbows)",
            ],
            inline_comments=["noqa"],
        )


class TestLinesFormatter(BaseTestFormatter):
    formatter = LinesFormatter

    def test_formatted(self):
        # Test one-line imports
        self._test(module, [], ["import {}".format(module)])
        self._test(module, [obj1], ["from {} import {}".format(module, obj1)])
        self._test(
            module,
            [obj1, obj2],
            [
                "from {} import {}".format(module, obj1),
                "from {} import {}".format(module, obj2),
            ],
        )
        self._test(
            long_module,
            [long_obj1],
            ["from {} import {}".format(long_module, long_obj1)],
        )

        # Test multi-lines imports
        self._test(
            long_module,
            [long_obj1, long_obj2],
            [
                "from {} import {}".format(long_module, long_obj1),
                "from {} import {}".format(long_module, long_obj2),
            ],
        )

        # Test file_artifacts
        self._test(
            long_module,
            [long_obj1, long_obj2],
            [
                "from {} import {}".format(long_module, long_obj1),
                "from {} import {}".format(long_module, long_obj2),
            ],
            sep="\r\n",
            file_artifacts={"sep": "\r\n"},
        )

        # Test imports with comments
        self._test(
            "foo", [], ["import foo  # comment"], inline_comments=["comment"]
        )
        self._test(
            "foo",
            [ImportLeaf("bar", inline_comments=["comment"])],
            ["from foo import bar  # comment"],
        )
        self._test(
            "something",
            [ImportLeaf("foo"), ImportLeaf("bar")],
            [
                "from something import bar  # noqa",
                "from something import foo  # noqa",
            ],
            inline_comments=["noqa"],
        )
        self._test(
            "foo",
            [
                ImportLeaf("bar", inline_comments=["hello"]),
                ImportLeaf("rainbows", inline_comments=["world"]),
                ImportLeaf("zz", pre_comments=["and lots of sleep"]),
            ],
            [
                "from foo import bar  # noqa hello",
                "from foo import rainbows  # noqa world",
                "from foo import zz  # noqa and lots of sleep",
            ],
            inline_comments=["noqa"],
        )
