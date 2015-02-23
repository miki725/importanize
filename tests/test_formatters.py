# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
import unittest

import mock

from importanize.formatters import Formatter, VerticalHangingFormatter
from importanize.parser import Token
from importanize.statements import ImportLeaf, ImportStatement


#class TestFormatter(unittest.TestCase):
    #def test_init(self):
        #actual = Formatter(mock.sentinel.statement)
        #self.assertEqual(actual.statement, mock.sentinel.statement)


class TestIndentWithTabsFormatter(unittest.TestCase):
    def test_formatted(self):
        def _test(stem, leafs, expected, sep='\n', comments=None, **kwargs):
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
            self.assertEqual(statement.formatted(),
                             sep.join(expected))

        _test('a', [], ['import a'])
        _test('a', ['b'], ['from a import b'])
        _test('a' * 40, ['b' * 40],
              ['from {} import {}'.format('a' * 40, 'b' * 40)])
        _test('a' * 40, ['b' * 20, 'c' * 20],
              ['from {} import ('.format('a' * 40),
               '    {},'.format('b' * 20),
               '    {},'.format('c' * 20),
               ')'])
        _test('a' * 40, ['b' * 20, 'c' * 20],
              ['from {} import ('.format('a' * 40),
               '    {},'.format('b' * 20),
               '    {},'.format('c' * 20),
               ')'],
              sep='\r\n',
              file_artifacts={'sep': '\r\n'})
        _test('foo', [],
              ['import foo  # comment'],
              comments=[Token('# comment')])
        _test('foo', [ImportLeaf('bar', comments=[Token('#comment')])],
              ['from foo import bar  # comment'])
        _test('something', [ImportLeaf('foo'),
                            ImportLeaf('bar')],
              ['from something import bar, foo  # noqa'],
              comments=[Token('# noqa')])
        _test('foo',
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


#class TestVerticalHangingFormatter(unittest.TestCase):
    #def test_formatted(self):
        #def _test(stem, leafs, expected, sep='\n', comments=None, **kwargs):
            #statement = ImportStatement(
                #list(),
                #stem,
                #list(map((lambda i:
                          #i if isinstance(i, ImportLeaf)
                          #else ImportLeaf(i)),
                         #leafs)),
                #comments=comments,
                #formatter=VerticalHangingFormatter,
                #**kwargs
            #)
            #self.assertEqual(statement.formatted(),
                             #sep.join(expected))

        #_test('a', [], ['import a'])
        #_test('a', ['b'], ['from a import b'])
        #_test('a' * 40, ['b' * 40],
              #['from {} import {}'.format('a' * 40, 'b' * 40)])
        #_test('a' * 40, ['b' * 20, 'c' * 20],
              #['from {} import ({}'.format('a' * 40, 'b' * 20),
               #'    {},'.format('c' * 20),
               #')'])
        #_test('a' * 40, ['b' * 20, 'c' * 20],
              #['from {} import ('.format('a' * 40),
               #'    {},'.format('b' * 20),
               #'    {},'.format('c' * 20),
               #')'],
              #sep='\r\n',
              #file_artifacts={'sep': '\r\n'})
        #_test('foo', [],
              #['import foo  # comment'],
              #comments=[Token('# comment')])
        #_test('foo', [ImportLeaf('bar', comments=[Token('#comment')])],
              #['from foo import bar  # comment'])
        #_test('something', [ImportLeaf('foo'),
                            #ImportLeaf('bar')],
              #['from something import bar, foo  # noqa'],
              #comments=[Token('# noqa')])
        #_test('foo',
              #[ImportLeaf('bar', comments=[Token('#hello')]),
               #ImportLeaf('rainbows', comments=[Token('#world')]),
               #ImportLeaf('zzz', comments=[Token('#and lots of sleep',
                                                 #is_comment_first=True)])],
              #['from foo import (  # noqa',
               #'    bar,  # hello',
               #'    rainbows,  # world',
               #'    # and lots of sleep',
               #'    zzz,',
               #')'],
              #comments=[Token('#noqa')])
