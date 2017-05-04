# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
import unittest

import mock
import six

from importanize.statements import ImportLeaf, ImportStatement


class TestImportLeaf(unittest.TestCase):
    def test_init(self):
        actual = ImportLeaf('a')
        self.assertEqual(actual.name, 'a')
        self.assertIsNone(actual.as_name)

        actual = ImportLeaf('a as b')
        self.assertEqual(actual.name, 'a')
        self.assertEqual(actual.as_name, 'b')

        actual = ImportLeaf('a as a')
        self.assertEqual(actual.name, 'a')
        self.assertIsNone(actual.as_name)

    def test_as_string(self):
        leaf = ImportLeaf('')

        leaf.name, leaf.as_name = 'a', None
        self.assertEqual(leaf.as_string(), 'a')

        leaf.name, leaf.as_name = 'a', 'b'
        self.assertEqual(leaf.as_string(), 'a as b')

    def test_str(self):
        leaf = ImportLeaf('a')
        self.assertEqual(six.text_type(leaf), leaf.as_string())

        leaf = ImportLeaf('a as b')
        self.assertEqual(six.text_type(leaf), leaf.as_string())

        leaf = ImportLeaf('a as a')
        self.assertEqual(six.text_type(leaf), leaf.as_string())

    @mock.patch.object(ImportLeaf, 'as_string')
    def test_str_mock(self, mock_as_string):
        self.assertEqual(
            getattr(ImportLeaf('a'),
                    '__{}__'.format(six.text_type.__name__))(),
            mock_as_string.return_value
        )

    def test_eq(self):
        self.assertTrue(ImportLeaf('a') == ImportLeaf('a'))
        self.assertFalse(ImportLeaf('a') == ImportLeaf('b'))

    def test_gt(self):
        self.assertGreater(
            ImportLeaf('b'),
            ImportLeaf('a')
        )

        self.assertGreater(
            ImportLeaf('a_variable'),
            ImportLeaf('CONSTANT')
        )

        self.assertGreater(
            ImportLeaf('AKlassName'),
            ImportLeaf('CONSTANT')
        )

        self.assertGreater(
            ImportLeaf('aKlassName'),
            ImportLeaf('CONSTANT')
        )
        self.assertGreater(
            ImportLeaf('a_variable'),
            ImportLeaf('aKlassName')
        )

    def test_repr(self):
        self.assertEqual(
            repr(ImportLeaf('a')),
            '<{}.{} object - "a">'.format(ImportLeaf.__module__,
                                          ImportLeaf.__name__)
        )

    def test_hash(self):
        self.assertEqual(
            hash(ImportLeaf('a')),
            hash('a')
        )
        self.assertEqual(
            hash(ImportLeaf('a as b')),
            hash('a as b')
        )

    @mock.patch.object(ImportLeaf, 'as_string')
    def test_hash_mock(self, mock_as_string):
        hash(ImportLeaf('a'))
        mock_as_string.assert_called_once_with()


class TestImportStatement(unittest.TestCase):
    def test_init(self):
        actual = ImportStatement(mock.sentinel.line_numbers,
                                 'foo')
        self.assertEqual(actual.line_numbers, mock.sentinel.line_numbers)
        self.assertEqual(actual.stem, 'foo')
        self.assertIsNone(actual.as_name)
        self.assertEqual(actual.leafs, [])

        actual = ImportStatement(mock.sentinel.line_numbers,
                                 'foo as bar')
        self.assertEqual(actual.line_numbers, mock.sentinel.line_numbers)
        self.assertEqual(actual.stem, 'foo')
        self.assertEqual(actual.as_name, 'bar')
        self.assertEqual(actual.leafs, [])

        actual = ImportStatement(mock.sentinel.line_numbers,
                                 'foo as foo')
        self.assertEqual(actual.line_numbers, mock.sentinel.line_numbers)
        self.assertEqual(actual.stem, 'foo')
        self.assertIsNone(actual.as_name)
        self.assertEqual(actual.leafs, [])

        actual = ImportStatement(mock.sentinel.line_numbers,
                                 'foo',
                                 mock.sentinel.leafs)
        self.assertEqual(actual.line_numbers, mock.sentinel.line_numbers)
        self.assertEqual(actual.stem, 'foo')
        self.assertEqual(actual.leafs, mock.sentinel.leafs)

        actual = ImportStatement(mock.sentinel.line_numbers,
                                 'foo as bar',
                                 mock.sentinel.leafs)
        self.assertEqual(actual.line_numbers, mock.sentinel.line_numbers)
        self.assertEqual(actual.stem, 'foo')
        self.assertIsNone(actual.as_name)
        self.assertEqual(actual.leafs, mock.sentinel.leafs)

    def test_root_module(self):
        self.assertEqual(
            ImportStatement([], 'a').root_module,
            'a'
        )
        self.assertEqual(
            ImportStatement([], 'a.b.c').root_module,
            'a'
        )
        self.assertEqual(
            ImportStatement([], '.a').root_module,
            ''
        )

    def test_as_string(self):
        def _test(stem, leafs, expected):
            statement = ImportStatement(
                list(),
                stem,
                list(map(ImportLeaf, leafs))
            )
            self.assertEqual(statement.as_string(), expected)

        _test('a', [], 'import a')
        _test('a as b', [], 'import a as b')
        _test('a.b.c', [], 'import a.b.c')
        _test('a.b', ['c'], 'from a.b import c')
        _test('a.b', ['c', 'd'], 'from a.b import c, d')
        _test('a.b', ['c as d', 'e'], 'from a.b import c as d, e')
        _test('a.b', ['e', 'c as d', 'e'], 'from a.b import c as d, e')

    def test_str(self):
        statement = ImportStatement([], 'a')
        self.assertEqual(
            statement.as_string(),
            six.text_type(statement),
        )

    @mock.patch.object(ImportStatement, 'as_string')
    def test_str_mock(self, mock_as_string):
        self.assertEqual(
            getattr(ImportStatement([], 'a'),
                    '__{}__'.format(six.text_type.__name__))(),
            mock_as_string.return_value
        )

    def test_repr(self):
        self.assertEqual(
            repr(ImportStatement([], 'a')),
            '<{}.{} object - "import a">'.format(ImportStatement.__module__,
                                                 ImportStatement.__name__)
        )

    def test_add(self):
        with self.assertRaises(AssertionError):
            ImportStatement([], 'a') + ImportStatement([], 'b')

        actual = (ImportStatement([1, 2], 'a', [ImportLeaf('b')]) +
                  ImportStatement([3, 4], 'a', [ImportLeaf('c')]))

        self.assertEqual(
            actual,
            ImportStatement([1, 2, 3, 4], 'a', [ImportLeaf('b'),
                                                ImportLeaf('c')])
        )
        self.assertListEqual(actual.line_numbers, [1, 2, 3, 4])

    def test_eq(self):
        self.assertTrue(
            ImportStatement([], 'a', [ImportLeaf('a')]) ==
            ImportStatement([], 'a', [ImportLeaf('a')])
        )
        self.assertTrue(
            ImportStatement([], 'a', [ImportLeaf('a')]) ==
            ImportStatement([], 'a', [ImportLeaf('a'), ImportLeaf('a')])
        )
        self.assertFalse(
            ImportStatement([], 'a', [ImportLeaf('a')]) ==
            ImportStatement([], 'a', [ImportLeaf('b')])
        )

    def test_gt(self):
        def _test(stem, leafs, stem2, leafs2, greater=True):
            statement = ImportStatement(
                list(),
                stem,
                list(map(ImportLeaf, leafs))
            )
            statement2 = ImportStatement(
                list(),
                stem2,
                list(map(ImportLeaf, leafs2))
            )
            if greater:
                self.assertGreater(statement2, statement)
            else:
                self.assertLess(statement2, statement)

        # from __future import unicode_literals
        # import a
        _test('__future__', ['unicode_literals'],
              'a', [])
        _test('a', [''],
              '__future__', ['unicode_literals'],
              False)
        _test('a', [],  # import a
              'a', ['b'])  # from a import b
        _test('a', ['b'],  # from a import b
              'a.b', ['c'])  # from a.b import c
        _test('a', [],  # import a
              '.a', [])  # import .a
        _test('a', ['b'],  # from aa import b
              '.a', ['b'])  # from .a import b
        _test('..a', [],  # import ..a
              '.a', [])  # import .a
        _test('..a', ['b'],  # from ..a import b
              '..a.b', ['c'])  # from ..a.b import c
        _test('.a', ['b'],  # from .a import b
              '.a.b', ['c'])  # from .a.b import b
        _test('a.b', ['c'],  # from a.b import c
              'a.b', ['d'])  # from a.b import d

    def test_hash(self):
        self.assertEqual(
            hash(ImportStatement([], 'a')),
            hash('import a')
        )
        self.assertEqual(
            hash(ImportStatement([], 'a', [ImportLeaf('b')])),
            hash('from a import b')
        )

    @mock.patch.object(ImportStatement, 'as_string')
    def test_hash_mock(self, mock_as_string):
        hash(ImportStatement([], 'a'))
        mock_as_string.assert_called_once_with()
