import six
import unittest

from importanize.importanize import parse_statements


class TestParsing(unittest.TestCase):
    def _test_import_string_matches(self, string, expected):
        self.assertEqual(
            six.text_type(
                list(parse_statements([(string, [1])]))[0]
            ),
            expected
        )

    def test_import_statements(self):
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
            'from a.b import c'
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
