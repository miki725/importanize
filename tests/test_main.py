# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
import os
import unittest

import mock

from importanize.main import PEP8_CONFIG, run, run_importanize
from importanize.utils import read


TESTING_MODULE = 'importanize.main'


class TestMain(unittest.TestCase):
    @mock.patch(TESTING_MODULE + '.read')
    def test_run_importanize_skip(self, mock_read):
        conf = {
            'exclude': ['*foo.py'],
        }
        self.assertFalse(
            run_importanize('/path/to/importanize/file/foo.py', conf, None)
        )
        self.assertFalse(mock_read.called)

    @mock.patch(TESTING_MODULE + '.print', create=True)
    def test_run_importanize_print(self, mock_print):
        test_file = os.path.join(os.path.dirname(__file__),
                                 'test_data',
                                 'normal.txt')
        expected_file = os.path.join(os.path.dirname(__file__),
                                     'test_data',
                                     'normal_expected.txt')
        expected = read(expected_file).encode('utf-8')

        self.assertTrue(
            run_importanize(test_file,
                            PEP8_CONFIG,
                            mock.MagicMock(print=True))
        )
        mock_print.assert_called_once_with(expected)

    @mock.patch(TESTING_MODULE + '.open', create=True)
    def test_run_importanize_write(self, mock_open):
        test_file = os.path.join(os.path.dirname(__file__),
                                 'test_data',
                                 'normal.txt')
        expected_file = os.path.join(os.path.dirname(__file__),
                                     'test_data',
                                     'normal_expected.txt')
        expected = read(expected_file).encode('utf-8')

        self.assertTrue(
            run_importanize(test_file,
                            PEP8_CONFIG,
                            mock.MagicMock(print=False))
        )
        mock_open.assert_called_once_with(test_file, 'wb')
        mock_open.return_value \
            .__enter__.return_value \
            .write.assert_called_once_with(expected)

    @mock.patch(TESTING_MODULE + '.run_importanize')
    @mock.patch('os.path.isdir')
    def test_run_single_file(self, mock_isdir, mock_run_importanize):
        mock_isdir.return_value = False
        run(
            mock.sentinel.path,
            mock.sentinel.config,
            mock.sentinel.args,
        )
        mock_run_importanize.assert_called_once_with(
            mock.sentinel.path,
            mock.sentinel.config,
            mock.sentinel.args,
        )

    @mock.patch(TESTING_MODULE + '.parser')
    @mock.patch(TESTING_MODULE + '.run_importanize')
    @mock.patch('os.path.isdir')
    def test_run_single_file_exception(self,
                                       mock_isdir,
                                       mock_run_importanize,
                                       mock_parser):
        mock_isdir.return_value = False
        mock_run_importanize.side_effect = ValueError
        run(
            mock.sentinel.path,
            mock.sentinel.config,
            mock.sentinel.args,
        )
        mock_run_importanize.assert_called_once_with(
            mock.sentinel.path,
            mock.sentinel.config,
            mock.sentinel.args,
        )
        mock_parser.error.assert_called_once_with(mock.ANY)

    @mock.patch(TESTING_MODULE + '.print', mock.MagicMock(), create=True)
    @mock.patch(TESTING_MODULE + '.run_importanize')
    @mock.patch('os.walk')
    @mock.patch('os.path.isdir')
    def test_run_folder(self,
                        mock_isdir,
                        mock_walk,
                        mock_run_importanize):
        mock_isdir.return_value = True
        mock_walk.return_value = [
            (
                'root',
                ['dir1', 'dir2'],
                ['foo.py', 'bar.txt'],
            ),
        ]

        conf = mock.MagicMock(print=True)
        run(
            mock.sentinel.path,
            mock.sentinel.config,
            conf,
        )
        mock_run_importanize.assert_called_once_with(
            'root/foo.py',
            mock.sentinel.config,
            conf,
        )

    @mock.patch(TESTING_MODULE + '.print', mock.MagicMock(), create=True)
    @mock.patch(TESTING_MODULE + '.parser')
    @mock.patch(TESTING_MODULE + '.run_importanize')
    @mock.patch('os.walk')
    @mock.patch('os.path.isdir')
    def test_run_folder_exception(self,
                                  mock_isdir,
                                  mock_walk,
                                  mock_run_importanize,
                                  mock_parser):
        mock_run_importanize.side_effect = ValueError
        mock_isdir.return_value = True
        mock_walk.return_value = [
            (
                'root',
                ['dir1', 'dir2'],
                ['foo.py', 'bar.txt'],
            ),
        ]

        conf = mock.MagicMock(print=True)
        run(
            mock.sentinel.path,
            mock.sentinel.config,
            conf,
        )
        mock_run_importanize.assert_called_once_with(
            'root/foo.py',
            mock.sentinel.config,
            conf,
        )
        mock_parser.error.assert_called_once_with(mock.ANY)
