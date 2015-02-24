# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
import unittest
from importanize.formatters import (
    Formatter,
    IndentWithTabsFormatter,
    VerticalHangingFormatter,
)
from importanize.parser import Token
from importanize.statements import ImportLeaf, ImportStatement

import mock


def _test(self, stem, leafs, expected, sep='\n', comments=None, **kwargs):
    statement = ImportStatement(
        list(),
        stem,
        list(map((lambda i:
                  i if isinstance(i, ImportLeaf)
                  else ImportLeaf(i)),
                 leafs)),
        comments=comments,
        formatter=self.formatter,
        **kwargs
    )
    self.assertEqual(statement.formatted(),
                     sep.join(expected))


class TestFormatter(unittest.TestCase):
    def test_init(self):
        actual = Formatter(mock.sentinel.statement)
        self.assertEqual(actual.statement, mock.sentinel.statement)


class TestIndentWithTabsFormatter(unittest.TestCase):
    def setUp(self):
        self.formatter = IndentWithTabsFormatter

    def test_formatted(self):
        _test(self, 'a', [], ['import a'])
        _test(self, 'a', ['b'], ['from a import b'])
        _test(self, 'a' * 40, ['b' * 40],
              ['from {} import {}'.format('a' * 40, 'b' * 40)])
        _test(self, 'a' * 40, ['b' * 20, 'c' * 20],
              ['from {} import ('.format('a' * 40),
               '    {},'.format('b' * 20),
               '    {},'.format('c' * 20),
               ')'])
        _test(self, 'a' * 40, ['b' * 20, 'c' * 20],
              ['from {} import ('.format('a' * 40),
               '    {},'.format('b' * 20),
               '    {},'.format('c' * 20),
               ')'],
              sep='\r\n',
              file_artifacts={'sep': '\r\n'})
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
        self.formatter = VerticalHangingFormatter

    def test_formatted(self):
        _test(self, 'a', [], ['import a'])
        _test(self, 'a', ['b'], ['from a import b'])
        _test(self, 'a' * 40, ['b' * 40],
              ['from {} import {}'.format('a' * 40, 'b' * 40)])
        _test(self, 'a' * 40, ['b' * 20, 'c' * 20],
              ['from {} import ('.format('a' * 40),
               '    {},'.format('b' * 20),
               '    {},'.format('c' * 20),
               ')'])
        _test(self, 'a' * 40, ['b' * 20, 'c' * 20],
              ['from {} import ('.format('a' * 40),
               '    {},'.format('b' * 20),
               '    {},'.format('c' * 20),
               ')'],
              sep='\r\n',
              file_artifacts={'sep': '\r\n'})
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
