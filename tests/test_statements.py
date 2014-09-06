# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function
import six
import unittest

from importanize.statements import ImportLeaf


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
