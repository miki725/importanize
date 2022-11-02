# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
import copy
import io
from pathlib import Path

from cached_property import cached_property  # type: ignore

from importanize.config import IMPORTANIZE_SETUP_CONFIG, Config, GroupConfig
from importanize.formatters import GroupedFormatter, LinesFormatter
from importanize.importanize import (
    Aggregator,
    CIAggregator,
    ListAggregator,
    PrintAggregator,
    Result,
    RuntimeConfig,
    run_importanize_on_source,
    run_importanize_on_text,
)
from importanize.statements import ImportLeaf, ImportStatement
from importanize.utils import OpenBytesIO, OpenStringIO, StdPath


TEST_DATA = StdPath(__file__).parent / "test_data"
CONFIG = Config(
    # need path so that subconfigs are not found within test_data subfolder
    path=TEST_DATA / "config",
    add_imports=[
        ImportStatement(
            "__future__",
            leafs=[
                ImportLeaf("absolute_import"),
                ImportLeaf("print_function"),
                ImportLeaf("unicode_literals"),
            ],
        )
    ],
    are_plugins_allowed=False,
    plugins=[],
)


class TestRuntimeConfig:
    config_path = str(
        (Path(__file__).parent.parent / IMPORTANIZE_SETUP_CONFIG).resolve()
    )

    def test_paths(self) -> None:
        assert RuntimeConfig(path_names=["foo"]).paths == [Path("foo")]

    def test_config(self) -> None:
        assert isinstance(RuntimeConfig(config_path=self.config_path).config, Config)

    def test_formatter(self) -> None:
        assert (
            RuntimeConfig(_config=Config(formatter=GroupedFormatter)).formatter
            is GroupedFormatter
        )
        assert (
            RuntimeConfig(
                formatter_name="lines", _config=Config(formatter=GroupedFormatter)
            ).formatter
            is LinesFormatter
        )

    def test_add_imports(self) -> None:
        assert RuntimeConfig(
            _config=Config(add_imports=[ImportStatement("foo")])
        ).add_imports
        assert not RuntimeConfig(
            path_names=["-"], _config=Config(add_imports=[ImportStatement("foo")])
        ).add_imports

    def test_merged_config(self) -> None:
        r = RuntimeConfig(
            path_names=["-"],
            formatter_name="lines",
            length=100,
            _config=Config(add_imports=[ImportStatement("foo")]),
        )

        assert r.merged_config.length == 100
        assert r.merged_config.formatter is LinesFormatter
        assert not r.merged_config.add_imports

    def test_normalize(self) -> None:
        r = RuntimeConfig(
            is_in_piped=True,
            is_out_piped=True,
            show_diff=True,
            path_names=[],
            is_print_mode=False,
            show_header=True,
        ).normalize()

        assert r.path_names == ["-"]
        assert r.is_print_mode
        assert not r.show_header
        assert not r.should_add_last_line

    def test_normalize_piped_with_filename(self) -> None:
        r = RuntimeConfig(
            is_in_piped=True,
            is_out_piped=True,
            show_diff=True,
            path_names=["foo"],
            is_print_mode=False,
            show_header=True,
        ).normalize()

        assert r.path_names == ["foo"]
        assert r.is_print_mode
        assert not r.show_header
        assert r.should_add_last_line

    def test_aggregator(self) -> None:
        assert isinstance(RuntimeConfig(is_ci_mode=True).aggregator, CIAggregator)
        assert isinstance(RuntimeConfig(is_list_mode=True).aggregator, ListAggregator)
        assert isinstance(RuntimeConfig(is_print_mode=True).aggregator, PrintAggregator)
        assert isinstance(RuntimeConfig().aggregator, Aggregator)


class TestResult:
    def test_has_changes(self) -> None:
        assert Result(path=Path(), original="foo", organized="bar").has_changes

    def test_is_success(self) -> None:
        assert not Result(path=Path(), error=ValueError()).is_success


class TestImportanize:
    test_data = TEST_DATA
    subconfig_test_data = TEST_DATA / "subconfig"

    input_text = test_data / "input.py"
    output_grouped = test_data / "output_grouped.py"
    output_grouped_single_line = test_data / "output_grouped_single_line.py"
    output_grouped_no_add_lines = test_data / "output_grouped_no_add_lines.py"
    output_inline_grouped = test_data / "output_inline_grouped.py"
    output_lines = test_data / "output_lines.py"

    input_no_imports = test_data / "input_no_imports.py"
    output_no_imports = test_data / "output_no_imports.py"

    input_unused_groups = test_data / "input_unused_groups.py"
    output_unused_groups = test_data / "output_unused_groups.py"

    config_path = test_data / "config.json"
    invalid = test_data / "invalid.py"

    input_few_imports = subconfig_test_data / "input_few_imports.py"

    @cached_property  # type: ignore
    def config(self) -> Config:
        return copy.deepcopy(CONFIG)

    def test_importanize_no_imports(self) -> None:
        result = next(
            run_importanize_on_source(
                self.input_no_imports, RuntimeConfig(_config=self.config)
            )
        )

        assert result.organized == self.output_no_imports.read_text()

    def test_importanize_invalid_python(self) -> None:
        result = next(
            run_importanize_on_source(self.invalid, RuntimeConfig(_config=self.config))
        )

        assert not result.is_success

    def test_importanize_invalid_encoding(self) -> None:
        result = next(
            run_importanize_on_source(
                self.invalid.with_streams(
                    filein=io.BytesIO("# -*- coding: ascii -*-\nпривет".encode("utf-8"))
                ),
                RuntimeConfig(_config=self.config),
            )
        )

        assert not result.is_success

    def test_importanize_incompatible_groups(self) -> None:
        self.config.groups = [GroupConfig(type="stdlib")]
        result = next(
            run_importanize_on_source(
                self.input_text, RuntimeConfig(_config=self.config)
            )
        )

        assert not result.is_success

    def test_importanize_skipping_file(self) -> None:
        self.config.exclude = ["*/test_data/*.py"]
        result = list(
            run_importanize_on_source(
                self.input_text,
                RuntimeConfig(formatter_name="grouped", _config=self.config),
            )
        )

        assert result == []

    def test_importanize_skipping_file_relative(self) -> None:
        self.config.exclude = ["tests\\test_data/*.py"]
        self.config.path = TEST_DATA.parent.parent / "setup.ini"
        result = list(
            run_importanize_on_source(
                self.input_text,
                RuntimeConfig(
                    formatter_name="grouped",
                    is_subconfig_allowed=False,
                    _config=self.config,
                ),
            )
        )

        assert result == []

    def test_importanize_skipping_file_backslash(self) -> None:
        self.config.exclude = ["*\\test_data\\*.py"]
        result = list(
            run_importanize_on_source(
                self.input_text,
                RuntimeConfig(formatter_name="grouped", _config=self.config),
            )
        )

        assert result == []

    def test_importanize_skipping_dir(self) -> None:
        self.config.exclude = ["*/test_data"]
        result = list(
            run_importanize_on_source(
                self.test_data,
                RuntimeConfig(formatter_name="grouped", _config=self.config),
            )
        )

        assert result == []

    def test_importanize_grouped(self) -> None:
        result = next(
            run_importanize_on_source(
                self.input_text,
                RuntimeConfig(formatter_name="grouped", _config=self.config),
            )
        )

        assert result.organized == self.output_grouped.read_text()
        assert result.has_changes
        assert result.is_success

    def test_importanize_grouped_windows_line_endings(self) -> None:
        result = next(
            run_importanize_on_text(
                "\r\n".join(self.input_text.read_text().splitlines()),
                self.input_text,
                self.config,
                RuntimeConfig(formatter_name="grouped", _config=self.config),
            )
        )

        assert (
            result.organized.splitlines()
            == self.output_grouped.read_text().splitlines()
        )
        assert result.organized.splitlines(True)[0].endswith("\r\n")

    def test_importanize_grouped_no_add_lines(self) -> None:
        self.config.after_imports_normalize_new_lines = False
        result = next(
            run_importanize_on_source(
                self.input_text,
                RuntimeConfig(formatter_name="grouped", _config=self.config),
            )
        )

        assert result.organized == self.output_grouped_no_add_lines.read_text()
        assert result.has_changes
        assert result.is_success

    def test_importanize_no_changes(self) -> None:
        result = next(
            run_importanize_on_source(
                self.output_grouped,
                RuntimeConfig(formatter_name="grouped", _config=self.config),
            )
        )

        assert result.organized == self.output_grouped.read_text()
        assert not result.has_changes
        assert result.is_success

    def test_importanize_inline_grouped(self) -> None:
        result = next(
            run_importanize_on_source(
                self.input_text,
                RuntimeConfig(formatter_name="inline-grouped", _config=self.config),
            )
        )

        assert result.organized == self.output_inline_grouped.read_text()

    def test_importanize_lines(self) -> None:
        result = next(
            run_importanize_on_source(
                self.input_text,
                RuntimeConfig(formatter_name="lines", _config=self.config),
            )
        )

        assert result.organized == self.output_lines.read_text()

    def test_importanize_dir(self) -> None:
        result = list(
            run_importanize_on_source(
                self.subconfig_test_data,
                RuntimeConfig(formatter_name="grouped", _config=self.config),
            )
        )

        assert self.input_few_imports in (i.path for i in result)


class TestCIAggregator:
    def test_ci_aggregator_changes(self) -> None:
        out = OpenStringIO()
        result = CIAggregator(
            RuntimeConfig(
                _config=CONFIG,
                _paths=[TEST_DATA / "input.py"],
                stdout=out,
                show_diff=True,
            )
        )()
        assert result == 1
        assert str(TEST_DATA) in out.read()

    def test_ci_aggregator_no_changes(self) -> None:
        out = OpenStringIO()
        result = CIAggregator(
            RuntimeConfig(
                _config=CONFIG,
                _paths=[TEST_DATA / "output_grouped.py"],
                stdout=out,
                show_diff=True,
            )
        )()
        assert result == 0
        assert out.read() == ""


class TestListAggregator:
    def test_list_aggregator(self) -> None:
        out = OpenStringIO()
        result = ListAggregator(
            RuntimeConfig(_config=CONFIG, _paths=[TEST_DATA / "input.py"], stdout=out)
        )()
        assert result == 0
        assert "stdlib\n------" in out.read()


class TestPrintAggregator:
    def test_print_aggregator_header(self) -> None:
        out = OpenStringIO()
        result = PrintAggregator(
            RuntimeConfig(
                _config=CONFIG,
                _paths=[TEST_DATA / "input.py"],
                stdout=out,
                show_header=True,
            )
        )()
        text = out.read()
        assert result == 0
        assert str(TEST_DATA / "input.py") in text
        assert (TEST_DATA / "output_grouped.py").read_text() in text

    def test_print_aggregator_diff(self) -> None:
        out = OpenStringIO()
        result = PrintAggregator(
            RuntimeConfig(
                _config=CONFIG,
                _paths=[TEST_DATA / "input.py"],
                stdout=out,
                show_diff=True,
            )
        )()
        text = out.read()
        assert result == 0
        assert str(TEST_DATA / "input.py") in text
        assert (TEST_DATA / "output_grouped.py").read_text() not in text

    def test_print_aggregator_piped(self) -> None:
        stdin = OpenBytesIO((TEST_DATA / "input.py").read_bytes())
        stdout = OpenBytesIO()
        out = OpenStringIO()
        result = PrintAggregator(
            RuntimeConfig(
                _config=CONFIG,
                _paths=[StdPath("-").with_streams(stdin=stdin, stdout=stdout)],
                show_header=True,
                stdout=out,
                is_subconfig_allowed=False,
            )
        )()
        assert result == 0
        assert str(TEST_DATA / "input.py") not in out.read()
        assert (TEST_DATA / "output_grouped.py").read_text() in stdout.read().decode(
            "utf-8"
        )


class TestAggregator:
    def test_invalid_config(self) -> None:
        stdin = OpenBytesIO((TEST_DATA / "output_grouped.py").read_bytes())
        stdout = OpenBytesIO()
        result = Aggregator(
            RuntimeConfig(
                config_path=__file__,
                _paths=[StdPath("-").with_streams(stdin=stdin, stdout=stdout)],
                show_header=True,
            )
        )()
        assert result == 1
        assert stdout.read().decode("utf-8") == ""

    def test_plugins_not_allowed(self) -> None:
        result = Aggregator(
            RuntimeConfig(
                _paths=[],
                are_plugins_allowed=False,
            )
        )()
        assert result == 0

    def test_no_plugins(self) -> None:
        result = Aggregator(RuntimeConfig(_paths=[], are_plugins_allowed=True))()
        assert result == 0

    def test_aggregator_has_changes(self) -> None:
        stdin = OpenBytesIO((TEST_DATA / "input.py").read_bytes())
        stdout = OpenBytesIO()
        result = Aggregator(
            RuntimeConfig(
                _config=CONFIG,
                _paths=[StdPath("-").with_streams(stdin=stdin, stdout=stdout)],
                show_header=True,
                is_subconfig_allowed=False,
            )
        )()
        assert result == 0
        assert (TEST_DATA / "output_grouped.py").read_text() in stdout.read().decode(
            "utf-8"
        )

    def test_aggregator_no_changes(self) -> None:
        stdin = OpenBytesIO((TEST_DATA / "output_grouped.py").read_bytes())
        stdout = OpenBytesIO()
        result = Aggregator(
            RuntimeConfig(
                _config=CONFIG,
                _paths=[StdPath("-").with_streams(stdin=stdin, stdout=stdout)],
                show_header=True,
                is_subconfig_allowed=False,
            )
        )()
        assert result == 0
        assert stdout.read().decode("utf-8") == ""

    def test_aggregator_invalid(self) -> None:
        stdin = OpenBytesIO((TEST_DATA / "invalid.py").read_bytes())
        stdout = OpenBytesIO()
        result = Aggregator(
            RuntimeConfig(
                _config=CONFIG,
                _paths=[StdPath("-").with_streams(stdin=stdin, stdout=stdout)],
                show_header=True,
            )
        )()
        assert result == 1
        assert stdout.read().decode("utf-8") == ""

    def test_aggregator_subconfig(self) -> None:
        stdout = OpenBytesIO()
        result = Aggregator(
            RuntimeConfig(
                _config=CONFIG,
                _paths=[
                    StdPath(
                        TEST_DATA / "subconfig" / "input_few_imports.py"
                    ).with_streams(fileout=stdout)
                ],
                show_header=True,
            )
        )()
        assert result == 0
        assert (
            TEST_DATA / "subconfig" / "output_grouped_few_imports.py"
        ).read_text() in stdout.read().decode("utf-8")
