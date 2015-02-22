# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
import unittest
from importanize.formatters import (
    Formatter,
)
from importanize.parser import Token
from importanize.statements import ImportLeaf, ImportStatement

import mock

# Define some names for tests purposes
m = 'module'
o1 = 'Object1'
o2 = 'Object2'
lm = m * 13
lo1 = o1 * 13
lo2 = m * 13


def _test(self, stem, leafs, expected, sep='\n', comments=None, **kwargs):
    """Facilitate the output tests of fromatters"""
    statement = ImportStatement(
        list(),
        stem,
        list(map((lambda i:
                  i if isinstance(i, ImportLeaf)
                  else ImportLeaf(i)),
                 leafs)),
        comments=comments,
        **kwargs
    )
    self.assertEqual(statement.formatted(formatter=self.formatter),
                     sep.join(expected))


class TestFormatter(unittest.TestCase):
    def test_init(self):
        actual = Formatter(mock.sentinel.statement)
        self.assertEqual(actual.statement, mock.sentinel.statement)


class TestIndentWithTabsFormatter(unittest.TestCase):
    def setUp(self):
        self.formatter = 'IndentWithTabsFormatter'

    def test_formatted(self):
        # Test one-line imports
        _test(self, m, [],
              ['import {}'.format(m)])
        _test(self, m, [o1],
              ['from {} import {}'.format(m, o1)])
        _test(self, m, [o1, o2],
              ['from {} import {}, {}'.format(m, o1, o2)])
        _test(self, lm, [lo1],
              ['from {} import {}'.format(lm, lo1)])

        # Test multi-lines imports
        _test(self, lm, [lo1, lo2],
              ['from {} import ('.format(lm),
               '    {},'.format(lo1),
               '    {},'.format(lo2),
               ')'])

        # Test file_artifacts
        _test(self, lm, [lo1, lo2],
              ['from {} import ('.format(lm),
               '    {},'.format(lo1),
               '    {},'.format(lo2),
               ')'],
              sep='\r\n',
              file_artifacts={'sep': '\r\n'})

        # Test imports with comments
        _test(self, 'foo', [],
              ['import foo  # comment'],
              comments=[Token('# comment')])
        _test(self, 'foo', [ImportLeaf('bar', comments=[Token('#comment')])],
              ['from foo import bar  # comment'])
        _test(self, 'something', [ImportLeaf('foo'),
                                  ImportLeaf('bar')],
              ['from something import bar, foo  # noqa'],
              comments=[Token('# noqa')])
        _test(self, 'foo',
              [ImportLeaf('bar', comments=[Token('#hello')]),
               ImportLeaf('rainbows', comments=[Token('#world')]),
               ImportLeaf('zzz', comments=[Token('#and lots of sleep',
                                                 is_comment_first=True)])],
              ['from foo import (  # noqa',
               '    bar,  # hello',
               '    rainbows,  # world',
               '    # and lots of sleep',
               '    zzz,',
               ')'],
              comments=[Token('#noqa')])


class TestVerticalHangingFormatter(unittest.TestCase):
    def setUp(self):
        self.formatter = 'VerticalHangingFormatter'

    def test_formatted(self):
        # Test one-line imports
        _test(self, m, [],
              ['import {}'.format(m)])
        _test(self, m, [o1],
              ['from {} import {}'.format(m, o1)])
        _test(self, m, [o1, o2],
              ['from {} import {}, {}'.format(m, o1, o2)])
        _test(self, lm, [lo1],
              ['from {} import {}'.format(lm, lo1)])

        # Test multi-lines imports
        _test(self, lm, [lo1, lo2],
              ['from {} import ({},'.format(lm, lo1),
               '{}{})'.format(' ' * 92, lo2)])

        # Test file_artifacts
        _test(self, lm, [lo1, lo2],
              ['from {} import ({},'.format(lm, lo1),
               '{}{})'.format(' ' * 92, lo2)],
              sep='\r\n',
              file_artifacts={'sep': '\r\n'})

        # Test imports with comments
        _test(self, 'foo', [],
              ['import foo  # comment'],
              comments=[Token('# comment')])
        _test(self, 'foo', [ImportLeaf('bar', comments=[Token('#comment')])],
              ['from foo import bar  # comment'])
        _test(self, 'something', [ImportLeaf('foo'),
                                  ImportLeaf('bar')],
              ['from something import bar, foo  # noqa'],
              comments=[Token('# noqa')])
        _test(self, 'foo',
              [ImportLeaf('bar', comments=[Token('#hello')]),
               ImportLeaf('rainbows', comments=[Token('#world')]),
               ImportLeaf('zzz', comments=[Token('#and lots of sleep',
                                                 is_comment_first=True)])],
              ['from foo import (  # noqa',
               '                 bar,  # hello',
               '                 rainbows,  # world',
               '                 # and lots of sleep',
               '                 zzz)'],
              comments=[Token('#noqa')])
        _test(self, 'foo',
              [ImportLeaf('bar', comments=[Token('#hello')]),
               ImportLeaf('rainbows', comments=[Token('#world')]),
               ImportLeaf('zzz', comments=[Token('#and lots of sleep')])],
              ['from foo import (  # noqa',
               '                 bar,  # hello',
               '                 rainbows,  # world',
               '                 zzz)  # and lots of sleep'],
              comments=[Token('#noqa')])
