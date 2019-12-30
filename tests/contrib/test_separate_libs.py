# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
from pathlib import Path

from importanize.config import Config
from importanize.importanize import RuntimeConfig, run_importanize_on_text
from importanize.plugins import activate_plugin, deactivate_all_plugins
from importanize.statements import ImportLeaf, ImportStatement


class TestSeparateLibsPlugin:
    TEST_DATA = Path(__file__).parent.parent / "test_data"
    subconfig_test_data = TEST_DATA / "subconfig"

    input_text = TEST_DATA / "input.py"
    output_grouped_separate_libs = TEST_DATA / "output_grouped_separate_libs.py"

    def test_plugin(self) -> None:
        activate_plugin("separate_libs")
        try:
            config = Config.default()
            config.add_imports = [
                ImportStatement(
                    "__future__",
                    leafs=[
                        ImportLeaf("absolute_import"),
                        ImportLeaf("print_function"),
                        ImportLeaf("unicode_literals"),
                    ],
                )
            ]

            result = next(
                run_importanize_on_text(
                    self.input_text.read_text(),
                    self.input_text,
                    config,
                    RuntimeConfig(_config=config),
                )
            )
            assert result.organized == self.output_grouped_separate_libs.read_text()
        finally:
            deactivate_all_plugins()
