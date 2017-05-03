# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
import unittest

import mock

from importanize.utils import (
    force_bytes,
    force_text,
    is_site_package,
    is_std_lib,
    list_split,
    list_strip,
    read,
)


class TestUtils(unittest.TestCase):
    def test_is_std_lib(self):
        self.assertFalse(is_std_lib(''))

        stdlib_modules = (
            'argparse',
            'codecs',
            'collections',
            'copy',
            'csv',
            'datetime',
            'decimal',
            'fileinput',
            'fnmatch',
            'functools',
            'glob',
            'gzip',
            'hashlib',
            'hmac',
            'importlib',
            'io',
            'itertools',
            'json',
            'logging',
            'math',
            'numbers',
            'operator',
            'optparse',
            'os',
            'pickle',
            'pprint',
            'random',
            're',
            'shelve',
            'shutil',
            'socket',
            'sqlite3',
            'ssl',
            'stat',
            'string',
            'struct',
            'subprocess',
            'sys',
            'sysconfig',
            'tempfile',
            'time',
            'timeit',
            'trace',
            'traceback',
            'unittest',
            'uuid',
            'xml',
            'zlib',
        )
        for module in stdlib_modules:
            msg = '{} should be stdlib'
            self.assertTrue(is_std_lib(module),
                            msg.format(module))

        self.assertFalse(is_std_lib('foo'))

    def test_is_site_package(self):
        self.assertFalse(is_site_package(''))

        # -- Be sure that stdlib modules are not site-packages
        stdlib_modules = (
            'argparse',
            'codecs',
        )
        for module in stdlib_modules:
            msg = '{} should not be sitepackages'
            self.assertFalse(is_site_package(module),
                             msg.format(module))

        # -- Be sure that fake modules are not site-packages
        self.assertFalse(is_site_package('foo'))

        # -- These packages come from requirements-dev.txt
        site_packages_modules = (
            "coverage",
            "mock",
            "rednose",
            "tox",
        )
        for module in site_packages_modules:
            msg = '{} should  be sitepackages'
            self.assertTrue(is_site_package(module),
                            msg.format(module))

    def test_list_strip(self):
        self.assertListEqual(
            list_strip(['  hello ', 'world']),
            ['hello', 'world']
        )

    @mock.patch('importanize.utils.open', create=True)
    def test_read(self, mock_open):
        actual = read(mock.sentinel.path)

        mock_open.assert_called_once_with(
            mock.sentinel.path,
            'rb'
        )
        mock_open.return_value \
            .__enter__.return_value \
            .read.assert_called_once_with()
        mock_open.return_value \
            .__enter__.return_value \
            .read.return_value \
            .decode.assert_called_once_with('utf-8')

        self.assertEqual(
            actual,
            (mock_open.return_value
             .__enter__.return_value
             .read.return_value
             .decode.return_value)
        )

    def test_list_split(self):
        self.assertEqual(
            list(list_split(['foo', '/', 'bar'], '/')),
            [['foo'], ['bar']]
        )

    def test_force_text(self):
        self.assertEqual(force_text(b'foo'), u'foo')
        self.assertEqual(force_text(u'foo'), u'foo')

    def test_force_bytes(self):
        self.assertEqual(force_bytes('foo'), b'foo')
        self.assertEqual(force_bytes(b'foo'), b'foo')
