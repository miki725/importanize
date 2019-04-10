# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from importanize.formatters import (
    GroupedFormatter,
    GroupedInlineAlignedFormatter,
    LinesFormatter,
)
import typing
from importanize.statements import ImportLeaf, ImportStatement
from importanize.formatters import Formatter
from importanize.config import Config
from importanize.parser import Artifacts


# Define some names for tests purposes
module = "module"
obj1 = "object1"
obj2 = "object2"
long_module = module * 13
long_obj1 = obj1 * 13
long_obj2 = obj2 * 13


class BaseTestFormatter:
    formatter: typing.Type[Formatter]

    def _test(
        self,
        stem: str,
        leafs: typing.List[ImportLeaf],
        expected: typing.List[str],
        sep: str = "\n",
        inline_comments: typing.List[str] = None,
        standalone_comments: typing.List[str] = None,
    ) -> None:
        """Facilitate the output tests of formatters"""
        statement = ImportStatement(
            stem,
            leafs=leafs,
            inline_comments=inline_comments,
            standalone_comments=standalone_comments,
        )
        assert self.formatter(
            statement, config=Config.default(), artifacts=Artifacts(sep=sep)
        ).format() == sep.join(expected)


class TestGroupedFormatter(BaseTestFormatter):
    formatter = GroupedFormatter

    def test_formatted(self) -> None:
        # Test one-line imports
        self._test(module, [], [f"import {module}"])
        self._test(module, [ImportLeaf(obj1)], [f"from {module} import {obj1}"])
        self._test(
            module,
            [ImportLeaf(obj1), ImportLeaf(obj2)],
            [f"from {module} import {obj1}, {obj2}"],
        )
        self._test(
            long_module,
            [ImportLeaf(long_obj1)],
            [f"from {long_module} import {long_obj1}"],
        )

        # Test multi-lines imports
        self._test(
            long_module,
            [ImportLeaf(long_obj1), ImportLeaf(long_obj2)],
            [
                f"from {long_module} import (",
                f"    {long_obj1},",
                f"    {long_obj2},",
                f")",
            ],
        )

        # Test file_artifacts
        self._test(
            long_module,
            [ImportLeaf(long_obj1), ImportLeaf(long_obj2)],
            [
                f"from {long_module} import (",
                f"    {long_obj1},",
                f"    {long_obj2},",
                f")",
            ],
            sep="\r\n",
        )

        # Test imports with comments
        self._test("foo", [], ["import foo  # comment"], inline_comments=["comment"])
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
                ImportLeaf("zz", standalone_comments=["and lots of sleep"]),
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

    def test_formatted(self) -> None:
        # Test one-line imports
        self._test(module, [], [f"import {module}"])
        self._test(module, [ImportLeaf(obj1)], [f"from {module} import {obj1}"])
        self._test(
            module,
            [ImportLeaf(obj1), ImportLeaf(obj2)],
            [f"from {module} import {obj1}, {obj2}"],
        )
        self._test(
            long_module,
            [ImportLeaf(long_obj1)],
            [f"from {long_module} import {long_obj1}"],
        )

        # Test multi-lines imports
        self._test(
            long_module,
            [ImportLeaf(long_obj1), ImportLeaf(long_obj2)],
            [
                f"from {long_module} import ({long_obj1},",
                "{}{})".format(" " * 92, long_obj2),
            ],
        )

        # Test file_artifacts
        self._test(
            long_module,
            [ImportLeaf(long_obj1), ImportLeaf(long_obj2)],
            [
                f"from {long_module} import ({long_obj1},",
                "{}{})".format(" " * 92, long_obj2),
            ],
            sep="\r\n",
        )

        # Test imports with comments
        self._test("foo", [], ["import foo  # comment"], inline_comments=["comment"])
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
                ImportLeaf("zz", standalone_comments=["and lots of sleep"]),
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
                f"from foo import (bar,  # noqa",
                f"                 {long_obj1},",
                f"                 rainbows)",
            ],
            inline_comments=["noqa"],
        )


class TestLinesFormatter(BaseTestFormatter):
    formatter = LinesFormatter

    def test_formatted(self) -> None:
        # Test one-line imports
        self._test(module, [], [f"import {module}"])
        self._test(module, [ImportLeaf(obj1)], [f"from {module} import {obj1}"])
        self._test(
            module,
            [ImportLeaf(obj1), ImportLeaf(obj2)],
            [f"from {module} import {obj1}", f"from {module} import {obj2}"],
        )
        self._test(
            long_module,
            [ImportLeaf(long_obj1)],
            [f"from {long_module} import {long_obj1}"],
        )

        # Test multi-lines imports
        self._test(
            long_module,
            [ImportLeaf(long_obj1), ImportLeaf(long_obj2)],
            [
                f"from {long_module} import {long_obj1}",
                f"from {long_module} import {long_obj2}",
            ],
        )

        # Test file_artifacts
        self._test(
            long_module,
            [ImportLeaf(long_obj1), ImportLeaf(long_obj2)],
            [
                f"from {long_module} import {long_obj1}",
                f"from {long_module} import {long_obj2}",
            ],
            sep="\r\n",
        )

        # Test imports with comments
        self._test("foo", [], ["import foo  # comment"], inline_comments=["comment"])
        self._test(
            "foo",
            [ImportLeaf("bar", inline_comments=["comment"])],
            ["from foo import bar  # comment"],
        )
        self._test(
            "something",
            [ImportLeaf("foo"), ImportLeaf("bar")],
            ["from something import bar  # noqa", "from something import foo  # noqa"],
            inline_comments=["noqa"],
        )
        self._test(
            "foo",
            [
                ImportLeaf("bar", inline_comments=["hello"]),
                ImportLeaf("rainbows", inline_comments=["world"]),
                ImportLeaf("zz", standalone_comments=["and lots of sleep"]),
            ],
            [
                "# comment",
                "from foo import bar  # noqa hello",
                "from foo import rainbows  # noqa world",
                "from foo import zz  # noqa and lots of sleep",
            ],
            standalone_comments=["comment"],
            inline_comments=["noqa"],
        )
