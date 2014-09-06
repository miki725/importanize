# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function
import mock
import six
import unittest

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
            hash('a+b')
        )


class TestImportStatement(unittest.TestCase):
    def test_init(self):
        actual = ImportStatement(mock.sentinel.line_numbers,
                                 mock.sentinel.stem)
        self.assertEqual(actual.line_numbers, mock.sentinel.line_numbers)
        self.assertEqual(actual.stem, mock.sentinel.stem)
        self.assertEqual(actual.leafs, [])

        actual = ImportStatement(mock.sentinel.line_numbers,
                                 mock.sentinel.stem,
                                 mock.sentinel.leafs)
        self.assertEqual(actual.line_numbers, mock.sentinel.line_numbers)
        self.assertEqual(actual.stem, mock.sentinel.stem)
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

    def test_eq(self):
        self.assertTrue(
            ImportStatement([], 'a', [ImportLeaf('a')])
            == ImportStatement([], 'a', [ImportLeaf('a')])
        )
        self.assertTrue(
            ImportStatement([], 'a', [ImportLeaf('a')])
            == ImportStatement([], 'a', [ImportLeaf('a'),
                                         ImportLeaf('a')])
        )
        self.assertFalse(
            ImportStatement([], 'a', [ImportLeaf('a')])
            == ImportStatement([], 'a', [ImportLeaf('b')])
        )
