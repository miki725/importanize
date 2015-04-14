# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
import unittest

import mock

from importanize.formatters import (
    Formatter,
    GroupedFormatter,
    GroupedInlineAlignedFormatter,
)
from importanize.parser import Token
from importanize.statements import ImportLeaf, ImportStatement


# Define some names for tests purposes
module = 'module'
obj1 = 'object1'
obj2 = 'object2'
long_module = module * 13
long_obj1 = obj1 * 13
long_obj2 = obj2 * 13


class BaseTestFormatter(unittest.TestCase):
    formatter = None

    def _test(self, stem, leafs, expected, sep='\n', comments=None, **kwargs):
        """Facilitate the output tests of formatters"""
        statement = ImportStatement(
            [],
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


class TestFormatter(BaseTestFormatter):
    def test_init(self):
        actual = Formatter(mock.sentinel.statement)
        self.assertEqual(actual.statement, mock.sentinel.statement)


class TestIndentWithTabsFormatter(BaseTestFormatter):
    formatter = GroupedFormatter

    def test_formatted(self):
        # Test one-line imports
        self._test(module, [],
                   ['import {}'.format(module)])
        self._test(module, [obj1],
                   ['from {} import {}'.format(module, obj1)])
        self._test(module, [obj1, obj2],
                   ['from {} import {}, {}'.format(module, obj1, obj2)])
        self._test(long_module, [long_obj1],
                   ['from {} import {}'.format(long_module, long_obj1)])

        # Test multi-lines imports
        self._test(long_module, [long_obj1, long_obj2],
                   ['from {} import ('.format(long_module),
                    '    {},'.format(long_obj1),
                    '    {},'.format(long_obj2),
                    ')'])

        # Test file_artifacts
        self._test(long_module, [long_obj1, long_obj2],
                   ['from {} import ('.format(long_module),
                    '    {},'.format(long_obj1),
                    '    {},'.format(long_obj2),
                    ')'],
                   sep='\r\n',
                   file_artifacts={'sep': '\r\n'})

        # Test imports with comments
        self._test('foo', [],
                   ['import foo  # comment'],
                   comments=[Token('# comment')])
        self._test('foo', [ImportLeaf('bar', comments=[Token('#comment')])],
                   ['from foo import bar  # comment'])
        self._test('something', [ImportLeaf('foo'),
                                 ImportLeaf('bar')],
                   ['from something import bar, foo  # noqa'],
                   comments=[Token('# noqa')])
        self._test('foo',
                   [ImportLeaf('bar', comments=[Token('#hello')]),
                    ImportLeaf('rainbows', comments=[Token('#world')]),
                    ImportLeaf('zz', comments=[Token('#and lots of sleep',
                                                     is_comment_first=True)])],
                   ['from foo import (  # noqa',
                    '    bar,  # hello',
                    '    rainbows,  # world',
                    '    # and lots of sleep',
                    '    zz,',
                    ')'],
                   comments=[Token('#noqa')])


class TestGroupedInlineAlignedFormatter(BaseTestFormatter):
    formatter = GroupedInlineAlignedFormatter

    def test_formatted(self):
        # Test one-line imports
        self._test(module, [],
                   ['import {}'.format(module)])
        self._test(module, [obj1],
                   ['from {} import {}'.format(module, obj1)])
        self._test(module, [obj1, obj2],
                   ['from {} import {}, {}'.format(module, obj1, obj2)])
        self._test(long_module, [long_obj1],
                   ['from {} import {}'.format(long_module, long_obj1)])

        # Test multi-lines imports
        self._test(long_module, [long_obj1, long_obj2],
                   ['from {} import ({},'.format(long_module, long_obj1),
                    '{}{})'.format(' ' * 92, long_obj2)])

        # Test file_artifacts
        self._test(long_module, [long_obj1, long_obj2],
                   ['from {} import ({},'.format(long_module, long_obj1),
                    '{}{})'.format(' ' * 92, long_obj2)],
                   sep='\r\n',
                   file_artifacts={'sep': '\r\n'})

        # Test imports with comments
        self._test('foo', [],
                   ['import foo  # comment'],
                   comments=[Token('# comment')])
        self._test('foo', [ImportLeaf('bar', comments=[Token('#comment')])],
                   ['from foo import bar  # comment'])
        self._test('something', [ImportLeaf('foo'),
                                 ImportLeaf('bar')],
                   ['from something import bar, foo  # noqa'],
                   comments=[Token('# noqa')])
        self._test('foo',
                   [ImportLeaf('bar', comments=[Token('#hello')]),
                    ImportLeaf('rainbows', comments=[Token('#world')]),
                    ImportLeaf('zz', comments=[Token('#and lots of sleep',
                                                     is_comment_first=True)])],
                   ['from foo import (  # noqa',
                    '    bar,  # hello',
                    '    rainbows,  # world',
                    '    # and lots of sleep',
                    '    zz,',
                    ')'],
                   comments=[Token('#noqa')])
        self._test('foo',
                   [ImportLeaf('bar', comments=[Token('#hello')]),
                    ImportLeaf('rainbows', comments=[Token('#world')]),
                    ImportLeaf('zzz', comments=[Token('#and lots of sleep')])],
                   ['from foo import (  # noqa',
                    '    bar,  # hello',
                    '    rainbows,  # world',
                    '    zzz,  # and lots of sleep',
                    ')'],
                   comments=[Token('#noqa')])
        self._test('foo',
                   [ImportLeaf('bar'),
                    ImportLeaf('rainbows'),
                    ImportLeaf(long_obj1)],
                   ['from foo import (bar,  # noqa',
                    '                 {},'.format(long_obj1),
                    '                 rainbows)'],
                   comments=[Token('#noqa')])
