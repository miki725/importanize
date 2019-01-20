# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
import unittest

from pathlib2 import Path

from importanize.config import IMPORTANIZE_SETUP_CONFIG, Config


class TestConfig(unittest.TestCase):
    def test_find_config(self):
        config = Config.find(Path(__file__))

        expected_config = Path(__file__).parent.parent.joinpath(
            IMPORTANIZE_SETUP_CONFIG
        )
        self.assertEqual(config.path, expected_config)

    def test_find_config_current_dir(self):
        # Instead of the absolute path, assume, user is running importanize
        # from the current directory.

        expected_config = Path(__file__).parent.parent.joinpath(
            IMPORTANIZE_SETUP_CONFIG
        )
        # If path is a file, and we have a config for the project and no
        # subconfig, and we dont find the config for the file, return the
        # passed config.
        config = Config.find(Path("tests/test_main.py"))
        self.assertEqual(config.path, expected_config)

    def test_find_config_nonfound(self):
        config = Config.find(Path(Path(__file__).root))

        self.assertIsNone(config.path)
