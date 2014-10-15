# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
import unittest

import mock
import six

from importanize.parser import (
    find_imports_from_lines,
    get_artifacts,
    parse_statements,
)


TESTING_MODULE = 'importanize.parser'


class TestParsing(unittest.TestCase):
    @mock.patch(TESTING_MODULE + '.read')
    def test_get_artifacts(self, mock_read):
        mock_read.return_value = 'Hello\nWorld\n'
        actual = get_artifacts(mock.sentinel.path)
        self.assertDictEqual(actual, {
            'sep': '\n',
        })
        mock_read.assert_called_once_with(mock.sentinel.path)

        mock_read.return_value = 'Hello\r\nWorld\n'
        actual = get_artifacts(mock.sentinel.path)
        self.assertDictEqual(actual, {
            'sep': '\r\n',
        })

        mock_read.return_value = 'Hello'
        actual = get_artifacts(mock.sentinel.path)
        self.assertDictEqual(actual, {
            'sep': '\n',
        })

    def _test_import_parsing(self, lines, expected):
        self.assertListEqual(
            list(find_imports_from_lines(enumerate(iter(lines)))),
            [expected] if expected else [],
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
            ('from a.b \\',
             '    import c'),
            ('from a.b import c', [0, 1]),
        )
        self._test_import_parsing(
            ('import a.b \\',
             '    as c'),
            ('import a.b as c', [0, 1]),
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
        self._test_import_parsing(
            ('"""',
             'from this shall not import',
             '"""',
             'from a.b import (',
             '    c,',
             '    d,',
             ')',
             'foo'),
            ('from a.b import c,d', [3, 4, 5, 6]),
        )
        self._test_import_parsing(
            ('""" from this shall not import """',
             'from a.b import (',
             '    c,',
             '    d,',
             ')',
             'foo'),
            ('from a.b import c,d', [1, 2, 3, 4]),
        )
        self._test_import_parsing(
            ('"""',
             'from this shall not import'),
            tuple(),
        )
        self._test_import_parsing(
            ('"""',
             'from this shall not import'
             '"""'),
            tuple(),
        )
        self._test_import_parsing(
            ('""" from this shall not import """'),
            tuple(),
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
