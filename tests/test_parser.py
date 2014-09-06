# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
import unittest

import six

from importanize.exceptions import MultipleImportsError
from importanize.parser import find_imports_from_lines, parse_statements


class TestParsing(unittest.TestCase):
    def _test_import_parsing(self, lines, expected):
        self.assertEqual(
            list(find_imports_from_lines(enumerate(iter(lines))))[0],
            expected,
        )

    def test_parsing(self):
        self._test_import_parsing(
            ('import a',),
            ('import a', [0]),
        )
        self._test_import_parsing(
            ('import a, b',),
            ('import a, b', [0]),
        )
        self._test_import_parsing(
            ('import a, b as c',),
            ('import a, b as c', [0]),
        )
        self._test_import_parsing(
            ('from a import b',),
            ('from a import b', [0]),
        )
        self._test_import_parsing(
            ('from a.b import c',),
            ('from a.b import c', [0]),
        )
        self._test_import_parsing(
            ('from a.b import c,\\',
             '    d'),
            ('from a.b import c,d', [0, 1]),
        )
        self._test_import_parsing(
            ('from a.b import c, \\',
             '    d'),
            ('from a.b import c,d', [0, 1]),
        )
        self._test_import_parsing(
            ('from a.b import \\',
             '    c,\\',
             '    d,'),
            ('from a.b import c,d', [0, 1, 2]),
        )
        self._test_import_parsing(
            ('from a.b import (c,',
             '    d)'),
            ('from a.b import c,d', [0, 1]),
        )
        self._test_import_parsing(
            ('from a.b import (c, ',
             '    d',
             ')'),
            ('from a.b import c,d', [0, 1, 2]),
        )
        self._test_import_parsing(
            ('from a.b import (',
             '    c,',
             '    d,',
             ')',
             'foo'),
            ('from a.b import c,d', [0, 1, 2, 3]),
        )

    def _test_import_string_matches(self, string, expected):
        self.assertEqual(
            six.text_type(
                list(parse_statements([(string, [1])]))[0]
            ),
            expected
        )

    def test_import_statements(self):
        """
        Test that ``import ..`` statements are correctly parsed
        and that string output of ImportStatement matches
        expected string.

        This test is not strictly a unittest.
        """
        self._test_import_string_matches(
            'import a',
            'import a'
        )
        self._test_import_string_matches(
            'import a as a',
            'import a'
        )
        self._test_import_string_matches(
            'import a as b',
            'import a as b'
        )
        self._test_import_string_matches(
            'import a.b as b',
            'from a import b'
        )
        self._test_import_string_matches(
            'import a.b as c',
            'from a import b as c'
        )
        self._test_import_string_matches(
            'import a.b.c',
            'import a.b.c',
        )
        self._test_import_string_matches(
            'import .a',
            'from . import a'
        )
        self._test_import_string_matches(
            'import .a.b',
            'from .a import b'
        )
        self._test_import_string_matches(
            'import ..a',
            'from .. import a'
        )
        self._test_import_string_matches(
            'import ..a.b',
            'from ..a import b'
        )

        with self.assertRaises(MultipleImportsError):
            list(parse_statements([('import a, b', [1])]))

    def test_from_statements(self):
        """
        Test that ``from .. import ..`` statements are correctly parsed
        and that string output of ImportStatement matches
        expected string.

        This test is not strictly a unittest.
        """
        self._test_import_string_matches(
            'from a import b',
            'from a import b',
        )
        self._test_import_string_matches(
            'from a.b import c',
            'from a.b import c',
        )
        self._test_import_string_matches(
            'from a.b import c as d',
            'from a.b import c as d',
        )
        self._test_import_string_matches(
            'from a import b,d, c',
            'from a import b, c, d',
        )
        self._test_import_string_matches(
            'from a import b,d as e, c',
            'from a import b, c, d as e',
        )
        self._test_import_string_matches(
            'from a import b as e,d as g, c as f',
            'from a import b as e, c as f, d as g',
        )
        self._test_import_string_matches(
            'from a import b as e,d as g, c as c',
            'from a import b as e, c, d as g',
        )
