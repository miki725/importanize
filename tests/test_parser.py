# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
import unittest

import six

from importanize.parser import (
    Token,
    find_imports_from_lines,
    get_text_artifacts,
    parse_statements,
    tokenize_import_lines,
)


TESTING_MODULE = 'importanize.parser'


class TestToken(unittest.TestCase):
    def test_is_comment(self):
        self.assertTrue(Token('# noqa').is_comment)
        self.assertFalse(Token('foo').is_comment)

    def test_normalized(self):
        self.assertEqual(Token('foo').normalized, 'foo')
        self.assertEqual(Token('#noqa').normalized, 'noqa')
        self.assertEqual(Token('# noqa').normalized, 'noqa')
        self.assertEqual(Token('#  noqa').normalized, ' noqa')


class TestParsing(unittest.TestCase):
    def test_get_text_artifacts(self):
        actual = get_text_artifacts('Hello\nWorld\n')
        self.assertDictEqual(actual, {
            'sep': '\n',
        })

        actual = get_text_artifacts('Hello\r\nWorld\n')
        self.assertDictEqual(actual, {
            'sep': '\r\n',
        })

        actual = get_text_artifacts('Hello')
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
            (['import a'], [0]),
        )
        self._test_import_parsing(
            ('import a, b',),
            (['import a, b'], [0]),
        )
        self._test_import_parsing(
            ('import a, b as c',),
            (['import a, b as c'], [0]),
        )
        self._test_import_parsing(
            ('from a import b',),
            (['from a import b'], [0]),
        )
        self._test_import_parsing(
            ('from a.b import c',),
            (['from a.b import c'], [0]),
        )
        self._test_import_parsing(
            ('from a.b import c,\\',
             '    d'),
            (['from a.b import c,\\',
              '    d'], [0, 1]),
        )
        self._test_import_parsing(
            ('from a.b import c, \\',
             '    d'),
            (['from a.b import c, \\',
              '    d'], [0, 1]),
        )
        self._test_import_parsing(
            ('from a.b \\',
             '    import c'),
            (['from a.b \\',
              '    import c'], [0, 1]),
        )
        self._test_import_parsing(
            ('import a.b \\',
             '    as c'),
            (['import a.b \\',
              '    as c'], [0, 1]),
        )
        self._test_import_parsing(
            ('from a.b import \\',
             '    c,\\',
             '    d,'),
            (['from a.b import \\',
              '    c,\\',
              '    d,'], [0, 1, 2]),
        )
        self._test_import_parsing(
            ('from a.b import (c,',
             '    d)'),
            (['from a.b import (c,',
              '    d)'], [0, 1]),
        )
        self._test_import_parsing(
            ('from a.b import (c, ',
             '    d',
             ')'),
            (['from a.b import (c, ',
              '    d',
              ')'], [0, 1, 2]),
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
            (['from a.b import (',
              '    c,',
              '    d,',
              ')'], [3, 4, 5, 6]),
        )
        self._test_import_parsing(
            ('""" from this shall not import """',
             'from a.b import (',
             '    c,',
             '    d,',
             ')',
             'foo'),
            (['from a.b import (',
              '    c,',
              '    d,',
              ')'], [1, 2, 3, 4]),
        )
        self._test_import_parsing(
            ('foo',
             'from a.b import \\',
             '    (c, d,',
             '     e, f,',
             '     g, h)',
             'bar'),
            (['from a.b import \\',
              '    (c, d,',
              '     e, f,',
              '     g, h)', ], [1, 2, 3, 4]),
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

    def test_tokenize_import_lines(self):
        data = (
            (
                ['import a.\\',
                 '    b'],
                ['import',
                 'a.b']
            ),
            (
                ['from __future__ import unicode_literals,\\',
                 '    print_function'],
                ['from',
                 '__future__',
                 'import',
                 'unicode_literals',
                 ',',
                 'print_function']
            ),
            (
                ['from a import b,  # noqa',
                 '    c'],
                ['from',
                 'a',
                 'import',
                 'b',
                 '# noqa',
                 ',',
                 'c']
            ),
            (
                ['import a,\\',
                 '    b'],
                ['import',
                 'a',
                 ',',
                 'b']
            ),
            (
                ['from a import\\',
                 '    b'],
                ['from',
                 'a',
                 'import',
                 'b']
            ),
            (
                ['from a\\',
                 '    import b'],
                ['from',
                 'a',
                 'import',
                 'b']
            ),
            (
                ['import a\\',
                 '    as b'],
                ['import',
                 'a',
                 'as',
                 'b']
            ),
            (
                ['from something import foo, bar  # noqa'],
                ['from',
                 'something',
                 'import',
                 'foo',
                 ',',
                 'bar',
                 '# noqa']
            ),
        )
        for _data, expected in data:
            self.assertListEqual(
                tokenize_import_lines(iter(_data)),
                expected
            )

    def _test_import_string_matches(self, string, expected):
        data = string if isinstance(string, (list, tuple)) else [string]
        self.assertEqual(
            six.text_type(
                next(parse_statements([(data, [1])]))
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
            'import a.b',
            'import a.b'
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
            'import a.b.c as d',
            'from a.b import c as d'
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
        self._test_import_string_matches(
            ['from a import (',
             '    b as e,  # foo',
             '    d as g  # noqa',
             ')'],
            'from a import b as e, d as g',
        )
