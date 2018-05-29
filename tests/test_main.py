# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
import json
import sys
import unittest
from copy import deepcopy

import mock
import six
from pathlib2 import Path

from importanize import __version__
from importanize.__main__ import (
    IMPORTANIZE_CONFIG,
    PEP8_CONFIG,
    CIFailure,
    Config,
    main,
    run,
    run_importanize_on_text,
)
from importanize.utils import force_text


TESTING_MODULE = 'importanize.__main__'
CONFIG = PEP8_CONFIG.copy()
CONFIG['add_imports'] = [
    'from __future__ import absolute_import, print_function, unicode_literals',
]


class TestMain(unittest.TestCase):
    test_data = Path(__file__).parent / 'test_data'

    input_text = (test_data / 'input.py').read_text()
    output_grouped = (test_data / 'output_grouped.py').read_text()
    output_grouped_single_line = (
        test_data / 'output_grouped_single_line.py'
    ).read_text()
    output_inline_grouped = (
        test_data / 'output_inline_grouped.py'
    ).read_text()

    def test_run_importanize_on_text_grouped(self):
        actual = run_importanize_on_text(
            self.input_text,
            CONFIG,
            mock.Mock(formatter='grouped',
                      ci=False,
                      subconfig=False,
                      length=None),
        )

        self.assertEqual(actual, self.output_grouped)

    def test_run_importanize_on_text_inline_grouped(self):
        actual = run_importanize_on_text(
            self.input_text,
            CONFIG,
            mock.Mock(formatter='inline-grouped',
                      ci=False,
                      subconfig=False,
                      length=None),
        )

        self.assertEqual(actual, self.output_inline_grouped)

    def test_run_importanize_on_text_ci_failed(self):
        with self.assertRaises(CIFailure):
            run_importanize_on_text(
                self.input_text,
                CONFIG,
                mock.Mock(formatter='grouped',
                          ci=True,
                          subconfig=False,
                          length=None),
            )

    def test_run_importanize_on_text_ci_passed(self):
        actual = run_importanize_on_text(
            self.output_grouped,
            CONFIG,
            mock.Mock(formatter='grouped',
                      ci=True,
                      subconfig=False,
                      length=None),
        )

        self.assertEqual(actual, self.output_grouped)

    @mock.patch.object(Path, 'write_text')
    def test_run_text_to_file_organized(self, mock_write_text):
        actual = run(
            self.input_text,
            CONFIG,
            mock.Mock(formatter='grouped',
                      ci=False,
                      print=False,
                      subconfig=False,
                      length=None),
            Path(__file__),
        )

        self.assertEqual(actual, self.output_grouped)
        mock_write_text.assert_called_once_with(self.output_grouped)

    @mock.patch.object(Path, 'write_text')
    def test_run_text_to_file_nothing_to_do(self, mock_write_text):
        actual = run(
            self.output_grouped,
            CONFIG,
            mock.Mock(formatter='grouped',
                      ci=False,
                      print=False,
                      subconfig=False,
                      length=None),
            Path(__file__),
        )

        self.assertEqual(actual, self.output_grouped)
        mock_write_text.assert_not_called()

    @mock.patch(TESTING_MODULE + '.print', create=True)
    def test_run_text_print(self, mock_print):
        actual = run(
            self.input_text,
            CONFIG,
            mock.Mock(formatter='grouped',
                      ci=False,
                      print=True,
                      header=True,
                      subconfig=False,
                      length=None),
            Path('foo'),
        )

        self.assertEqual(actual, self.output_grouped)
        mock_print.assert_has_calls([
            mock.call('==='),
            mock.call('foo'),
            mock.call('---'),
            mock.call(self.output_grouped),
        ])

    @mock.patch(TESTING_MODULE + '.print', create=True)
    def test_run_text_print_no_file(self, mock_print):
        actual = run(
            self.input_text,
            CONFIG,
            mock.Mock(formatter='grouped',
                      ci=False,
                      print=True,
                      header=True,
                      subconfig=False,
                      length=None),
        )

        self.assertEqual(actual, self.output_grouped)
        mock_print.assert_has_calls([
            mock.call(self.output_grouped),
        ])

    @mock.patch(TESTING_MODULE + '.print', create=True)
    def test_run_text_print_no_header(self, mock_print):
        actual = run(
            self.input_text,
            CONFIG,
            mock.Mock(formatter='grouped',
                      ci=False,
                      print=True,
                      header=False,
                      subconfig=False,
                      length=None),
            Path('foo'),
        )

        self.assertEqual(actual, self.output_grouped)
        mock_print.assert_has_calls([
            mock.call(self.output_grouped),
        ])

    @mock.patch(TESTING_MODULE + '.print', create=True)
    def test_run_file_skipped(self, mock_print):
        config = deepcopy(CONFIG)
        config['exclude'] = ['*/test_data/*.py']

        actual = run(
            self.test_data / 'input.py',
            Config(config),
            mock.Mock(formatter='grouped',
                      ci=False,
                      print=True,
                      header=False,
                      subconfig=False,
                      length=None),
        )

        self.assertIsNone(actual)
        mock_print.assert_not_called()

    @mock.patch(TESTING_MODULE + '.print', create=True)
    def test_run_file(self, mock_print):
        actual = run(
            self.test_data / 'input.py',
            Config(CONFIG),
            mock.Mock(formatter='grouped',
                      ci=False,
                      print=True,
                      header=False,
                      subconfig=False,
                      length=None),
        )

        self.assertEqual(actual, self.output_grouped)
        mock_print.assert_called_once_with(self.output_grouped)

    @mock.patch(TESTING_MODULE + '.print', create=True)
    def test_run_dir(self, mock_print):
        actual = run(
            self.test_data,
            Config(CONFIG),
            mock.Mock(formatter='grouped',
                      ci=False,
                      print=True,
                      header=False,
                      subconfig=False,
                      length=None),
        )

        self.assertIsNone(actual)
        mock_print.assert_has_calls([
            mock.call(self.output_grouped),
        ])

    @mock.patch(TESTING_MODULE + '.print', create=True)
    def test_run_dir_subconfig_invalid(self, mock_print):
        config_file = self.test_data / IMPORTANIZE_CONFIG
        config_file.write_text('invalid json')

        try:
            actual = run(
                self.test_data,
                Config(CONFIG),
                mock.Mock(formatter='grouped',
                          ci=False,
                          print=True,
                          header=False,
                          subconfig=True,
                          length=None),
            )

            self.assertIsNone(actual)
            mock_print.assert_has_calls([
                mock.call(self.output_grouped),
            ])

        finally:
            config_file.unlink()

    @mock.patch(TESTING_MODULE + '.print', create=True)
    def test_run_dir_subconfig_valid(self, mock_print):
        config = deepcopy(CONFIG)
        config['after_imports_new_lines'] = 1

        config_file = self.test_data / IMPORTANIZE_CONFIG
        config_file.write_text(force_text(json.dumps(config)))

        try:
            actual = run(
                self.test_data,
                Config(CONFIG),
                mock.Mock(formatter='grouped',
                          ci=False,
                          print=True,
                          header=False,
                          subconfig=True,
                          length=None),
            )

            self.assertIsNone(actual)
            mock_print.assert_has_calls([
                mock.call(self.output_grouped_single_line),
            ])

        finally:
            config_file.unlink()

    @mock.patch(TESTING_MODULE + '.print', create=True)
    def test_run_dir_skipped(self, mock_print):
        config = deepcopy(CONFIG)
        config['exclude'] = ['*/test_data']

        actual = run(
            self.test_data,
            Config(config),
            mock.Mock(formatter='grouped',
                      ci=False,
                      print=True,
                      header=False,
                      subconfig=False,
                      length=None),
        )

        self.assertIsNone(actual)
        mock_print.assert_not_called()

    @mock.patch(TESTING_MODULE + '.print', create=True)
    def test_run_dir_ci(self, mock_print):
        with self.assertRaises(CIFailure):
            run(
                self.test_data,
                Config(CONFIG),
                mock.Mock(formatter='grouped',
                          ci=True,
                          print=True,
                          header=False,
                          subconfig=False,
                          length=None),
            )

    def test_find_config(self):
        config = Config.find(Path(__file__))

        expected_config = Path(__file__).parent.parent.joinpath(
            IMPORTANIZE_CONFIG
        )
        self.assertEqual(config.path, expected_config)

    def test_find_config_current_dir(self):
        # Instead of the absolute path, assume, user is running importanize
        # from the current directory.

        expected_config = Path(__file__).parent.parent.joinpath(
            IMPORTANIZE_CONFIG
        )
        # If path is a file, and we have a config for the project and no
        # subconfig, and we dont find the config for the file, return the
        # passed config.
        config = Config.find(Path('tests/test_main.py'))
        self.assertEqual(config.path, expected_config)

    def test_find_config_nonfound(self):
        config = Config.find(Path(Path(__file__).root))

        self.assertIsNone(config.path)

    @mock.patch(TESTING_MODULE + '.print', create=True)
    def test_main_version(self, mock_print):

        self.assertEqual(main(['--version']), 0)

        self.assertEqual(mock_print.call_count, 1)
        version = mock_print.mock_calls[0][1][0]
        self.assertIn('version: {}'.format(__version__), version)

    @mock.patch(TESTING_MODULE + '.S_ISFIFO', mock.Mock(return_value=True))
    @mock.patch(TESTING_MODULE + '.print', create=True)
    @mock.patch.object(sys, 'stdin')
    def test_main_piped(self, mock_stdin, mock_print):
        mock_stdin.read.return_value = self.input_text
        actual = main([])

        self.assertEqual(actual, 0)
        mock_print.assert_called_once_with(self.output_grouped)

    @mock.patch(TESTING_MODULE + '.S_ISFIFO', mock.Mock(return_value=False))
    @mock.patch(TESTING_MODULE + '.print', create=True)
    def test_main_not_piped(self, mock_print):
        actual = main([
            six.text_type(self.test_data / 'input.py'),
            '--config', six.text_type(self.test_data / 'config.json'),
            '--print',
            '--no-header',
        ])

        self.assertEqual(actual, 0)
        mock_print.assert_called_once_with(self.output_grouped)

    @mock.patch(TESTING_MODULE + '.S_ISFIFO', mock.Mock(return_value=False))
    @mock.patch(TESTING_MODULE + '.print', create=True)
    def test_main_not_piped_ci(self, mock_print):
        actual = main([
            six.text_type(self.test_data / 'input.py'),
            '--config', six.text_type(self.test_data / 'config.json'),
            '--ci',
        ])

        self.assertEqual(actual, 1)

    @mock.patch(TESTING_MODULE + '.S_ISFIFO', mock.Mock(return_value=False))
    @mock.patch(TESTING_MODULE + '.print', create=True)
    @mock.patch(TESTING_MODULE + '.run')
    def test_main_not_piped_exception(self, mock_run, mock_print):
        mock_run.side_effect = ValueError

        actual = main([
            six.text_type(self.test_data / 'input.py'),
            '--config', six.text_type(self.test_data / 'config.json'),
            '--ci',
        ])

        self.assertEqual(actual, 1)
