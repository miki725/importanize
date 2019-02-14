# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
import unittest

import mock
import six

from importanize.statements import ImportLeaf, ImportStatement


class TestImportLeaf(unittest.TestCase):
    def test_as_string(self):
        leaf = ImportLeaf("")

        leaf.name, leaf.as_name = "a", None
        self.assertEqual(leaf.as_string(), "a")

        leaf.name, leaf.as_name = "a", "b"
        self.assertEqual(leaf.as_string(), "a as b")

    def test_str(self):
        leaf = ImportLeaf("a")
        self.assertEqual(six.text_type(leaf), leaf.as_string())

        leaf = ImportLeaf("a as b")
        self.assertEqual(six.text_type(leaf), leaf.as_string())

        leaf = ImportLeaf("a as a")
        self.assertEqual(six.text_type(leaf), leaf.as_string())

    @mock.patch.object(ImportLeaf, "as_string")
    def test_str_mock(self, mock_as_string):
        self.assertEqual(
            getattr(ImportLeaf("a"), "__{}__".format(six.text_type.__name__))(),
            mock_as_string.return_value,
        )

    def test_eq(self):
        self.assertTrue(ImportLeaf("a") == ImportLeaf("a"))
        self.assertFalse(ImportLeaf("a") == ImportLeaf("b"))

    def test_gt(self):
        self.assertGreater(ImportLeaf("b"), ImportLeaf("a"))

        self.assertGreater(ImportLeaf("a_variable"), ImportLeaf("CONSTANT"))

        self.assertGreater(ImportLeaf("AKlassName"), ImportLeaf("CONSTANT"))

        self.assertGreater(ImportLeaf("aKlassName"), ImportLeaf("CONSTANT"))
        self.assertGreater(ImportLeaf("a_variable"), ImportLeaf("aKlassName"))

    def test_repr(self):
        self.assertEqual(repr(ImportLeaf("a")), "<ImportLeaf 'a'>")

    def test_hash(self):
        self.assertEqual(hash(ImportLeaf("a")), hash("a"))
        self.assertEqual(hash(ImportLeaf("a as b")), hash("a as b"))

    @mock.patch.object(ImportLeaf, "as_string")
    def test_hash_mock(self, mock_as_string):
        hash(ImportLeaf("a"))
        mock_as_string.assert_called_once_with()


class TestImportStatement(unittest.TestCase):
    def test_root_module(self):
        self.assertEqual(ImportStatement("a").root_module, "a")
        self.assertEqual(ImportStatement("a.b.c").root_module, "a")
        self.assertEqual(ImportStatement(".a").root_module, "")

    def test_as_string(self):
        def _test(stem, leafs, expected):
            statement = ImportStatement(
                stem, leafs=list(map(ImportLeaf, leafs))
            )
            self.assertEqual(statement.as_string(), expected)

        _test("a", [], "import a")
        _test("a as b", [], "import a as b")
        _test("a.b.c", [], "import a.b.c")
        _test("a.b", ["c"], "from a.b import c")
        _test("a.b", ["c", "d"], "from a.b import c, d")
        _test("a.b", ["c as d", "e"], "from a.b import c as d, e")
        _test("a.b", ["e", "c as d", "e"], "from a.b import c as d, e")

    def test_str(self):
        statement = ImportStatement("a")
        self.assertEqual(statement.as_string(), six.text_type(statement))

    @mock.patch.object(ImportStatement, "as_string")
    def test_str_mock(self, mock_as_string):
        self.assertEqual(
            getattr(
                ImportStatement("a"), "__{}__".format(six.text_type.__name__)
            )(),
            mock_as_string.return_value,
        )

    def test_repr(self):
        self.assertEqual(
            repr(ImportStatement("a")), "<ImportStatement 'import a'>"
        )

    def test_add(self):
        with self.assertRaises(AssertionError):
            ImportStatement("a") + ImportStatement("b")

        actual = ImportStatement(
            "a", leafs=[ImportLeaf("b")], line_numbers=[1, 2]
        ) + ImportStatement("a", leafs=[ImportLeaf("c")], line_numbers=[3, 4])

        self.assertEqual(
            actual,
            ImportStatement(
                "a",
                leafs=[ImportLeaf("b"), ImportLeaf("c")],
                line_numbers=[1, 2, 3, 4],
            ),
        )
        self.assertListEqual(actual.line_numbers, [1, 2, 3, 4])

    def test_eq(self):
        self.assertTrue(
            ImportStatement("a", leafs=[ImportLeaf("a")])
            == ImportStatement("a", leafs=[ImportLeaf("a")])
        )
        self.assertTrue(
            ImportStatement("a", leafs=[ImportLeaf("a")])
            == ImportStatement("a", leafs=[ImportLeaf("a"), ImportLeaf("a")])
        )
        self.assertFalse(
            ImportStatement("a", leafs=[ImportLeaf("a")])
            == ImportStatement("a", leafs=[ImportLeaf("b")])
        )

    def test_gt(self):
        def _test(stem, leafs, stem2, leafs2, greater=True):
            statement = ImportStatement(
                stem, leafs=list(map(ImportLeaf, leafs))
            )
            statement2 = ImportStatement(
                stem2, leafs=list(map(ImportLeaf, leafs2))
            )
            if greater:
                self.assertGreater(statement2, statement)
            else:
                self.assertLess(statement2, statement)

        # from __future import unicode_literals
        # import a
        _test("__future__", ["unicode_literals"], "a", [])
        _test("a", [""], "__future__", ["unicode_literals"], False)
        _test("a", [], "a", ["b"])  # import a  # from a import b
        _test("a", ["b"], "a.b", ["c"])  # from a import b  # from a.b import c
        _test("a", [], ".a", [])  # import a  # import .a
        _test("a", ["b"], ".a", ["b"])  # from aa import b  # from .a import b
        _test("..a", [], ".a", [])  # import ..a  # import .a
        _test(
            "..a", ["b"], "..a.b", ["c"]
        )  # from ..a import b  # from ..a.b import c
        _test(
            ".a", ["b"], ".a.b", ["c"]
        )  # from .a import b  # from .a.b import b
        _test(
            "a.b", ["c"], "a.b", ["d"]
        )  # from a.b import c  # from a.b import d

    def test_hash(self):
        self.assertEqual(hash(ImportStatement("a")), hash("import a"))
        self.assertEqual(
            hash(ImportStatement("a", leafs=[ImportLeaf("b")])),
            hash("from a import b"),
        )

    @mock.patch.object(ImportStatement, "as_string")
    def test_hash_mock(self, mock_as_string):
        hash(ImportStatement("a"))
        mock_as_string.assert_called_once_with()
