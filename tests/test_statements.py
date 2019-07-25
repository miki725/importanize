# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from importanize.statements import ImportLeaf, ImportStatement
import typing

import pytest  # type: ignore


class TestImportLeaf:
    def test_as_string(self) -> None:
        assert ImportLeaf("a").as_string() == "a"
        assert str(ImportLeaf("a")) == "a"
        assert ImportLeaf("a", "b").as_string() == "a as b"
        assert ImportLeaf("a", "a").as_string() == "a"
        assert str(ImportLeaf("a", "b")) == "a as b"

    def test_eq(self) -> None:
        assert ImportLeaf("a") == ImportLeaf("a")
        assert ImportLeaf("a") != ImportLeaf("b")
        assert ImportLeaf("a", "b") == ImportLeaf("a", "b")
        assert ImportLeaf("a", "b") != ImportLeaf("a", "c")
        assert ImportLeaf("a", "b", standalone_comments=["comment"]) == ImportLeaf(
            "a", "b"
        )
        assert ImportLeaf(
            "a", "b", standalone_comments=["comment"], strict=True
        ) != ImportLeaf("a", "b")

    def test_gt(self) -> None:
        assert ImportLeaf("b") > ImportLeaf("a")
        assert ImportLeaf("a_variable") > ImportLeaf("CONSTANT")
        assert ImportLeaf("a_variable") > ImportLeaf("aKlassName")
        assert ImportLeaf("KlassName") > ImportLeaf("CONSTANT")
        assert ImportLeaf("aKlassName") > ImportLeaf("CONSTANT")

    def test_repr(self) -> None:
        assert repr(ImportLeaf("a")) == "<ImportLeaf 'a'>"

    def test_hash(self) -> None:
        assert hash(ImportLeaf("a")) == hash("a")
        assert hash(ImportLeaf("a", "b")) == hash("a as b")


class TestImportStatement:
    def test_with_line_numbers(self) -> None:
        assert ImportStatement("a", line_numbers=[1, 2]).with_line_numbers(
            [3, 4]
        ).line_numbers == [3, 4]

    def test_root_module(self) -> None:
        assert ImportStatement("a").root_module == "a"
        assert ImportStatement("a.b.c").root_module == "a"
        assert ImportStatement(".a").root_module == ""

    def test_as_string(self) -> None:
        def _test(
            stem: str,
            leafs: typing.List[typing.Union[typing.Tuple[str], typing.Tuple[str, str]]],
            expected: str,
        ) -> None:
            statement = ImportStatement(stem, leafs=[ImportLeaf(*i) for i in leafs])
            assert statement.as_string() == expected
            assert str(statement) == expected

        _test("a", [], "import a")
        _test("a as b", [], "import a as b")
        _test("a.b.c", [], "import a.b.c")
        _test("a.b", [("c",)], "from a.b import c")
        _test("a.b", [("c",), ("d",)], "from a.b import c, d")
        _test("a.b", [("c", "d"), ("e",)], "from a.b import c as d, e")
        _test("a.b", [("e",), ("c", "d"), ("e",)], "from a.b import c as d, e")

    def test_repr(self) -> None:
        assert repr(ImportStatement("a")) == "<ImportStatement 'import a'>"

    def test_add(self) -> None:
        with pytest.raises(AssertionError):
            ImportStatement("a") + ImportStatement("b")

        actual = ImportStatement(
            "a", leafs=[ImportLeaf("b")], line_numbers=[1, 2]
        ) + ImportStatement("a", leafs=[ImportLeaf("c")], line_numbers=[3, 4])

        assert actual == ImportStatement(
            "a", leafs=[ImportLeaf("b"), ImportLeaf("c")], line_numbers=[1, 2, 3, 4]
        )
        assert actual.line_numbers == [1, 2, 3, 4]

    def test_eq(self) -> None:
        assert ImportStatement("a", leafs=[ImportLeaf("a")]) == ImportStatement(
            "a", leafs=[ImportLeaf("a")]
        )
        assert ImportStatement("a", leafs=[ImportLeaf("a")]) == ImportStatement(
            "a", leafs=[ImportLeaf("a"), ImportLeaf("a")]
        )
        assert ImportStatement("a", leafs=[ImportLeaf("a")]) != ImportStatement(
            "a", leafs=[ImportLeaf("b")]
        )
        assert ImportStatement(
            "a", leafs=[ImportLeaf("a")], standalone_comments=["comment"]
        ) == ImportStatement("a", leafs=[ImportLeaf("a"), ImportLeaf("a")])
        assert ImportStatement(
            "a", leafs=[ImportLeaf("a")], standalone_comments=["comment"], strict=True
        ) != ImportStatement("a", leafs=[ImportLeaf("a"), ImportLeaf("a")])

    def test_gt(self) -> None:
        def _test(
            stem: str,
            leafs: typing.List[str],
            stem2: str,
            leafs2: typing.List[str],
            greater: bool = True,
        ) -> None:
            statement = ImportStatement(stem, leafs=list(map(ImportLeaf, leafs)))
            statement2 = ImportStatement(stem2, leafs=list(map(ImportLeaf, leafs2)))
            assert (statement2 > statement) == greater

        # from __future import unicode_literals
        # import a
        _test("__future__", ["unicode_literals"], "a", [])
        _test("a", [""], "__future__", ["unicode_literals"], False)
        _test("a", [], "a", ["b"])  # import a  # from a import b
        _test("a", ["b"], "a.b", ["c"])  # from a import b  # from a.b import c
        _test("a", [], ".a", [])  # import a  # import .a
        _test("a", ["b"], ".a", ["b"])  # from aa import b  # from .a import b
        _test("..a", [], ".a", [])  # import ..a  # import .a
        _test("..a", ["b"], "..a.b", ["c"])  # from ..a import b  # from ..a.b import c
        _test(".a", ["b"], ".a.b", ["c"])  # from .a import b  # from .a.b import b
        _test("a.b", ["c"], "a.b", ["d"])  # from a.b import c  # from a.b import d

    def test_hash(self) -> None:
        assert hash(ImportStatement("a")) == hash("import a")
        assert hash(ImportStatement("a", leafs=[ImportLeaf("b")])) == hash(
            "from a import b"
        )
