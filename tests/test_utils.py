# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
import os
import sys
import unittest

import mock

from importanize.utils import (
    ignore_site_packages_paths,
    is_std_lib,
    list_strip,
    read,
)


class TestUtils(unittest.TestCase):
    def test_ignore_site_packages_paths(self):
        sys.path.append(os.getcwd())
        paths = sys.path[:]

        with ignore_site_packages_paths():
            self.assertNotEqual(sys.path, paths)
            self.assertLess(len(sys.path), len(paths))

        self.assertIn(os.getcwd(), sys.path)
        self.assertListEqual(sys.path, paths)
        sys.path.remove(os.getcwd())

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
            'pdb',
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
