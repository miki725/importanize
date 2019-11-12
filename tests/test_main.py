# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
from pathlib import Path

from click.testing import CliRunner

from importanize.__main__ import click_cli as cli
from importanize.config import IMPORTANIZE_INI_CONFIG
from importanize.importanize import RuntimeConfig
from importanize.main import main


TEST_DATA = Path(__file__).parent / "test_data"


def test_version() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "https://github.com/miki725/importanize" in result.output


def test_ci() -> None:
    assert (
        main(
            RuntimeConfig(
                config_path=str(TEST_DATA / "subconfig" / IMPORTANIZE_INI_CONFIG),
                path_names=[str(TEST_DATA / "input.py")],
                is_ci_mode=True,
                is_subconfig_allowed=False,
            )
        )
        == 1
    )
