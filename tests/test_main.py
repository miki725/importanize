# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
import logging
import os
import unittest

import mock
import six

from importanize.main import (
    PEP8_CONFIG,
    find_config,
    main,
    parser,
    run,
    run_importanize,
)
from importanize.utils import read


TESTING_MODULE = 'importanize.main'


class TestMain(unittest.TestCase):
    @mock.patch(TESTING_MODULE + '.read')
    def test_run_importanize_skip(self, mock_read):
        conf = {'exclude': ['*input.txt'], }
        test_file = os.path.join(os.path.dirname(__file__),
                                 'test_data',
                                 'input.txt')
        self.assertFalse(run_importanize(test_file, conf, None))

        self.assertFalse(mock_read.called)

    @mock.patch(TESTING_MODULE + '.print', create=True)
    def test_run_importanize_print(self, mock_print):
        test_file = os.path.join(os.path.dirname(__file__),
                                 'test_data',
                                 'input.txt')
        expected_file = os.path.join(os.path.dirname(__file__),
                                     'test_data',
                                     'output_IndentWithTabsFormatter.txt')
        expected = (
            read(expected_file)
            if six.PY3
            else read(expected_file).encode('utf-8')
        )

        self.assertTrue(
            run_importanize(test_file,
                            PEP8_CONFIG,
                            mock.MagicMock(print=True,
                                           formatter='IndentWithTabsFormatter')
                            )
        )
        mock_print.assert_called_once_with(expected)

    @mock.patch(TESTING_MODULE + '.print', create=True)
    def test_run_importanize_print_verticalhangingformatter(self, mock_print):
        test_file = os.path.join(os.path.dirname(__file__),
                                 'test_data',
                                 'input.txt')
        expected_file = os.path.join(os.path.dirname(__file__),
                                     'test_data',
                                     'output_VerticalHangingFormatter.txt')
        expected = (
            read(expected_file)
            if six.PY3
            else read(expected_file).encode('utf-8')
        )

        self.assertTrue(
            run_importanize(test_file,
                            PEP8_CONFIG,
                            mock.MagicMock(print=True,
                                           formatter='VerticalHangingFormatter'
                                           )
                            )
        )
        mock_print.assert_called_once_with(expected)

    @mock.patch(TESTING_MODULE + '.print', create=True)
    def test_run_importanize_with_unavailable_formatter(self, mock_print):
        test_file = os.path.join(os.path.dirname(__file__),
                                 'test_data',
                                 'input.txt')
        with self.assertRaises(SystemExit) as cm:
            run_importanize(test_file,
                            PEP8_CONFIG,
                            mock.MagicMock(print=True,
                                           formatter='UnavailableFormatter'
                                           )
                            )
        self.assertEqual(cm.exception.code, 1)

    @mock.patch(TESTING_MODULE + '.open', create=True)
    def test_run_importanize_write(self, mock_open):
        test_file = os.path.join(os.path.dirname(__file__),
                                 'test_data',
                                 'input.txt')
        expected_file = os.path.join(os.path.dirname(__file__),
                                     'test_data',
                                     'output_IndentWithTabsFormatter.txt')
        expected = read(expected_file).encode('utf-8')

        self.assertTrue(
            run_importanize(test_file,
                            PEP8_CONFIG,
                            mock.MagicMock(print=False,
                                           formatter='IndentWithTabsFormatter')
                            )
        )
        mock_open.assert_called_once_with(test_file, 'wb')
        mock_open.return_value \
            .__enter__.return_value \
            .write.assert_called_once_with(expected)

    @mock.patch(TESTING_MODULE + '.open', create=True)
    def test_run_importanize_write_verticalhangingformatter(self, mock_open):
        test_file = os.path.join(os.path.dirname(__file__),
                                 'test_data',
                                 'input.txt')
        expected_file = os.path.join(os.path.dirname(__file__),
                                     'test_data',
                                     'output_VerticalHangingFormatter.txt')
        expected = read(expected_file).encode('utf-8')

        self.assertTrue(
            run_importanize(test_file,
                            PEP8_CONFIG,
                            mock.MagicMock(print=False,
                                           formatter='VerticalHangingFormatter'
                                           )
                            )
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

    @mock.patch('os.path.exists')
    @mock.patch('os.getcwd')
    def test_find_config(self, mock_getcwd, mock_exists):
        mock_getcwd.return_value = '/path/to/importanize'
        mock_exists.side_effect = False, True

        config, found = find_config()

        self.assertEqual(config, '/path/to/.importanizerc')
        self.assertTrue(bool(found))

    @mock.patch(TESTING_MODULE + '.run')
    @mock.patch('logging.getLogger')
    @mock.patch.object(parser, 'parse_args')
    def test_main_without_config(self,
                                 mock_parse_args,
                                 mock_get_logger,
                                 mock_run):
        args = mock.MagicMock(
            verbose=1,
            version=False,
            path=['/path/../'],
            config=None,
        )
        mock_parse_args.return_value = args

        main()

        mock_parse_args.assert_called_once_with()
        mock_get_logger.assert_called_once_with('')
        mock_get_logger().setLevel.assert_called_once_with(logging.INFO)
        mock_run.assert_called_once_with('/', PEP8_CONFIG, args)

    @mock.patch(TESTING_MODULE + '.read')
    @mock.patch(TESTING_MODULE + '.run')
    @mock.patch('json.loads')
    @mock.patch('logging.getLogger')
    @mock.patch.object(parser, 'parse_args')
    def test_main_with_config(self,
                              mock_parse_args,
                              mock_get_logger,
                              mock_loads,
                              mock_run,
                              mock_read):
        args = mock.MagicMock(
            verbose=1,
            version=False,
            path=['/path/../'],
            config=mock.sentinel.config,
        )
        mock_parse_args.return_value = args

        main()

        mock_parse_args.assert_called_once_with()
        mock_get_logger.assert_called_once_with('')
        mock_get_logger().setLevel.assert_called_once_with(logging.INFO)
        mock_read.assert_called_once_with(mock.sentinel.config)
        mock_loads.assert_called_once_with(mock_read.return_value)
        mock_run.assert_called_once_with('/', mock_loads.return_value, args)

    @mock.patch(TESTING_MODULE + '.print', create=True)
    @mock.patch('sys.exit')
    @mock.patch.object(parser, 'parse_args')
    def test_main_version(self, mock_parse_args, mock_exit, mock_print):
        mock_exit.side_effect = SystemExit
        mock_parse_args.return_value = mock.MagicMock(
            verbose=1,
            version=True,
        )

        with self.assertRaises(SystemExit):
            main()

        mock_parse_args.assert_called_once_with()
        mock_exit.assert_called_once_with(0)
        mock_print.assert_called_once_with(mock.ANY)
