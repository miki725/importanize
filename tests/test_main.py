# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
import json
import sys
import unittest
from copy import deepcopy
from pathlib import Path

import mock

from importanize import __version__
from importanize.__main__ import (
    CIFailure,
    Config,
    main,
    run,
    run_importanize_on_text,
)
from importanize.config import IMPORTANIZE_JSON_CONFIG, PEP8_CONFIG
from importanize.utils import force_text


TESTING_MODULE = "importanize.__main__"
CONFIG = PEP8_CONFIG.copy()
CONFIG["add_imports"] = [
    "from __future__ import absolute_import, print_function, unicode_literals"
]


def consume(i):
    for _ in i:
        pass


class TestMain(unittest.TestCase):
    maxDiff = None

    test_data = Path(__file__).parent / "test_data"

    input_text = (test_data / "input.py").read_text()
    output_grouped = (test_data / "output_grouped.py").read_text()
    output_grouped_single_line = (
        test_data / "output_grouped_single_line.py"
    ).read_text()
    output_inline_grouped = (test_data / "output_inline_grouped.py").read_text()
    output_lines = (test_data / "output_lines.py").read_text()

    input_no_imports = (test_data / "input_no_imports.py").read_text()
    output_no_imports = (test_data / "output_no_imports.py").read_text()

    def test_run_importanize_no_imports(self):
        actual = run_importanize_on_text(
            self.input_no_imports,
            CONFIG,
            mock.Mock(
                formatter="grouped",
                ci=False,
                subconfig=False,
                length=None,
                list=False,
            ),
        )

        self.assertEqual(actual, self.output_no_imports)

    def test_run_importanize_on_text_grouped(self):
        actual = run_importanize_on_text(
            self.input_text,
            CONFIG,
            mock.Mock(
                formatter="grouped",
                ci=False,
                subconfig=False,
                length=None,
                list=False,
            ),
        )

        self.assertEqual(actual, self.output_grouped)

    def test_run_importanize_on_text_inline_grouped(self):
        actual = run_importanize_on_text(
            self.input_text,
            CONFIG,
            mock.Mock(
                formatter="inline-grouped",
                ci=False,
                subconfig=False,
                length=None,
                list=False,
            ),
        )

        self.assertEqual(actual, self.output_inline_grouped)

    def test_run_importanize_on_text_lines(self):
        actual = run_importanize_on_text(
            self.input_text,
            CONFIG,
            mock.Mock(
                formatter="lines",
                ci=False,
                subconfig=False,
                length=None,
                list=False,
            ),
        )

        self.assertEqual(actual, self.output_lines)

    def test_run_importanize_on_text_ci_failed(self):
        with self.assertRaises(CIFailure):
            run_importanize_on_text(
                self.input_text,
                CONFIG,
                mock.Mock(
                    formatter="grouped",
                    ci=True,
                    subconfig=False,
                    length=None,
                    list=False,
                ),
            )

    def test_run_importanize_on_text_ci_passed(self):
        actual = run_importanize_on_text(
            self.output_grouped,
            CONFIG,
            mock.Mock(
                formatter="grouped",
                ci=True,
                subconfig=False,
                length=None,
                list=False,
            ),
        )

        self.assertEqual(actual, self.output_grouped)

    @mock.patch.object(Path, "write_text")
    def test_run_text_to_file_organized(self, mock_write_text):
        actual = next(
            run(
                self.input_text,
                CONFIG,
                mock.Mock(
                    formatter="grouped",
                    ci=False,
                    print=False,
                    subconfig=False,
                    length=None,
                    list=False,
                ),
                Path(__file__),
            )
        )

        self.assertEqual(self.output_grouped, actual)
        mock_write_text.assert_called_once_with(self.output_grouped)

    @mock.patch.object(Path, "write_text")
    def test_run_text_to_file_nothing_to_do(self, mock_write_text):
        actual = next(
            run(
                self.output_grouped,
                CONFIG,
                mock.Mock(
                    formatter="grouped",
                    ci=False,
                    print=False,
                    subconfig=False,
                    length=None,
                    list=False,
                ),
                Path(__file__),
            )
        )

        self.assertEqual(actual, self.output_grouped)
        mock_write_text.assert_not_called()

    @mock.patch(TESTING_MODULE + ".print", create=True)
    def test_run_text_print(self, mock_print):
        actual = next(
            run(
                self.input_text,
                CONFIG,
                mock.Mock(
                    formatter="grouped",
                    ci=False,
                    print=True,
                    header=True,
                    subconfig=False,
                    length=None,
                    list=False,
                ),
                Path("foo"),
            )
        )

        self.assertEqual(actual, self.output_grouped)
        mock_print.assert_has_calls(
            [
                mock.call("==="),
                mock.call("foo"),
                mock.call("---"),
                mock.call(self.output_grouped),
            ]
        )

    @mock.patch(TESTING_MODULE + ".print", create=True)
    def test_run_text_print_no_file(self, mock_print):
        actual = next(
            run(
                self.input_text,
                CONFIG,
                mock.Mock(
                    formatter="grouped",
                    ci=False,
                    print=True,
                    header=True,
                    subconfig=False,
                    length=None,
                    list=False,
                ),
            )
        )

        self.assertEqual(actual, self.output_grouped)
        mock_print.assert_has_calls([mock.call(self.output_grouped)])

    @mock.patch(TESTING_MODULE + ".print", create=True)
    def test_run_text_print_no_header(self, mock_print):
        actual = next(
            run(
                self.input_text,
                CONFIG,
                mock.Mock(
                    formatter="grouped",
                    ci=False,
                    print=True,
                    header=False,
                    subconfig=False,
                    length=None,
                    list=False,
                ),
                Path("foo"),
            )
        )

        self.assertEqual(actual, self.output_grouped)
        mock_print.assert_has_calls([mock.call(self.output_grouped)])

    @mock.patch(TESTING_MODULE + ".print", create=True)
    def test_run_file_skipped(self, mock_print):
        config = deepcopy(CONFIG)
        config["exclude"] = ["*/test_data/*.py"]

        consume(
            run(
                self.test_data / "input.py",
                Config(config),
                mock.Mock(
                    formatter="grouped",
                    ci=False,
                    print=True,
                    header=False,
                    subconfig=False,
                    length=None,
                    list=False,
                ),
            )
        )

        mock_print.assert_not_called()

    @mock.patch(TESTING_MODULE + ".print", create=True)
    def test_run_file(self, mock_print):
        actual = next(
            run(
                self.test_data / "input.py",
                Config(CONFIG),
                mock.Mock(
                    formatter="grouped",
                    ci=False,
                    print=True,
                    header=False,
                    subconfig=False,
                    length=None,
                    list=False,
                ),
            )
        )

        self.assertEqual(actual, self.output_grouped)
        mock_print.assert_called_once_with(self.output_grouped)

    @mock.patch(TESTING_MODULE + ".print", create=True)
    def test_run_dir(self, mock_print):
        consume(
            run(
                self.test_data,
                Config(CONFIG),
                mock.Mock(
                    formatter="grouped",
                    ci=False,
                    print=True,
                    header=False,
                    subconfig=False,
                    length=None,
                    list=False,
                ),
            )
        )

        mock_print.assert_has_calls([mock.call(self.output_grouped)])

    @mock.patch(TESTING_MODULE + ".print", create=True)
    def test_run_dir_subconfig_invalid(self, mock_print):
        config_file = self.test_data / IMPORTANIZE_JSON_CONFIG
        config_file.write_text("invalid json")

        try:
            consume(
                run(
                    self.test_data,
                    Config(CONFIG),
                    mock.Mock(
                        formatter="grouped",
                        ci=False,
                        print=True,
                        header=False,
                        subconfig=True,
                        length=None,
                        list=False,
                    ),
                )
            )

            mock_print.assert_has_calls([mock.call(self.output_grouped)])

        finally:
            config_file.unlink()

    @mock.patch(TESTING_MODULE + ".print", create=True)
    def test_run_dir_subconfig_valid(self, mock_print):
        config = deepcopy(CONFIG)
        config["after_imports_new_lines"] = 1

        config_file = self.test_data / IMPORTANIZE_JSON_CONFIG
        config_file.write_text(force_text(json.dumps(config)))

        try:
            consume(
                run(
                    self.test_data,
                    Config(CONFIG),
                    mock.Mock(
                        formatter="grouped",
                        ci=False,
                        print=True,
                        header=False,
                        subconfig=True,
                        length=None,
                        list=False,
                    ),
                )
            )

            mock_print.assert_has_calls(
                [mock.call(self.output_grouped_single_line)]
            )

        finally:
            config_file.unlink()

    @mock.patch(TESTING_MODULE + ".print", create=True)
    def test_run_dir_skipped(self, mock_print):
        config = deepcopy(CONFIG)
        config["exclude"] = ["*/test_data"]

        consume(
            run(
                self.test_data,
                Config(config),
                mock.Mock(
                    formatter="grouped",
                    ci=False,
                    print=True,
                    header=False,
                    subconfig=False,
                    length=None,
                    list=False,
                ),
            )
        )

        mock_print.assert_not_called()

    @mock.patch(TESTING_MODULE + ".print", create=True)
    def test_run_dir_ci(self, mock_print):
        with self.assertRaises(CIFailure):
            consume(
                run(
                    self.test_data,
                    Config(CONFIG),
                    mock.Mock(
                        formatter="grouped",
                        ci=True,
                        print=True,
                        header=False,
                        subconfig=False,
                        length=None,
                        list=False,
                    ),
                )
            )

    def test_main_python_version(self):
        self.assertEqual(
            main(["--py={}".format(3 - sys.version_info.major % 2)]), 0
        )

    @mock.patch(TESTING_MODULE + ".print", create=True)
    def test_main_version(self, mock_print):

        self.assertEqual(main(["--version"]), 0)

        self.assertEqual(mock_print.call_count, 1)
        version = mock_print.mock_calls[0][1][0]
        self.assertIn(f"version: {__version__}", version)

    @mock.patch(TESTING_MODULE + ".S_ISFIFO", mock.Mock(return_value=False))
    @mock.patch(TESTING_MODULE + ".print", create=True)
    def test_main_list(self, mock_print):
        actual = main(
            [
                str(self.test_data / "input_few_imports.py"),
                "--config",
                str(self.test_data / "config.json"),
                "--list",
            ]
        )

        self.assertEqual(actual, 0)
        mock_print.assert_has_calls(
            [
                mock.call("stdlib"),
                mock.call("------"),
                mock.call("from __future__ import unicode_literals"),
                mock.call("import datetime as mydatetime"),
                mock.call(),
                mock.call("sitepackages"),
                mock.call("------------"),
                mock.call("import flake8 as lint"),
                mock.call(),
                mock.call("remainder"),
                mock.call("---------"),
                mock.call("import z"),
                mock.call("from a import b"),
                mock.call("from a.b import d"),
                mock.call(),
                mock.call("local"),
                mock.call("-----"),
                mock.call("from .module import bar, foo"),
            ]
        )

    @mock.patch(TESTING_MODULE + ".S_ISFIFO", mock.Mock(return_value=True))
    @mock.patch(TESTING_MODULE + ".print", create=True)
    @mock.patch.object(sys, "stdin")
    def test_main_piped(self, mock_stdin, mock_print):
        mock_stdin.read.return_value = self.input_text
        actual = main(["--length", "80"])

        self.assertEqual(actual, 0)
        mock_print.assert_called_once_with(self.output_grouped)

    @mock.patch(TESTING_MODULE + ".S_ISFIFO", mock.Mock(return_value=False))
    @mock.patch(TESTING_MODULE + ".print", create=True)
    def test_main_not_piped(self, mock_print):
        actual = main(
            [
                str(self.test_data / "input.py"),
                "--config",
                str(self.test_data / "config.json"),
                "--print",
                "--no-header",
            ]
        )

        self.assertEqual(actual, 0)
        mock_print.assert_called_once_with(self.output_grouped)

    @mock.patch(TESTING_MODULE + ".S_ISFIFO", mock.Mock(return_value=False))
    @mock.patch(TESTING_MODULE + ".print", create=True)
    def test_main_not_piped_ci(self, mock_print):
        actual = main(
            [
                str(self.test_data / "input.py"),
                "--config",
                str(self.test_data / "config.json"),
                "--ci",
            ]
        )

        self.assertEqual(actual, 1)

    @mock.patch(TESTING_MODULE + ".S_ISFIFO", mock.Mock(return_value=False))
    @mock.patch(TESTING_MODULE + ".print", create=True)
    @mock.patch(TESTING_MODULE + ".run")
    def test_main_not_piped_exception(self, mock_run, mock_print):
        mock_run.side_effect = ValueError

        actual = main(
            [
                str(self.test_data / "input.py"),
                "--config",
                str(self.test_data / "config.json"),
                "--ci",
            ]
        )

        self.assertEqual(actual, 1)
