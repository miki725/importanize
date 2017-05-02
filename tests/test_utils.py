# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
import os
import sys
import unittest

import mock

from importanize.utils import (
    ignore_site_packages_paths,
    is_site_package,
    is_std_lib,
    list_strip,
    read,
)


class TestUtils(unittest.TestCase):
    def _test_ignore_site_packages_paths(self, raise_msg=None):
        sys.path.append(os.getcwd())
        paths = sys.path[:]

        try:
            with ignore_site_packages_paths():
                self.assertNotEqual(sys.path, paths)
                self.assertLess(len(sys.path), len(paths))
                if raise_msg:
                    raise ValueError(raise_msg)
        except ValueError as e:
            if raise_msg not in str(e):
                # -- This only happens if there's a bug in this test
                raise  # pragma: no cover

        self.assertIn(os.getcwd(), sys.path)
        self.assertListEqual(sys.path, paths)
        sys.path.remove(os.getcwd())

    def test_site_packages_paths(self):
        self._test_ignore_site_packages_paths(raise_msg=None)

    def test_site_packages_paths_exception(self):
        self._test_ignore_site_packages_paths(raise_msg="TEST EXCEPTION")

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
