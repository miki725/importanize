# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
import abc
import logging
import os
import sys
import typing
from contextlib import suppress
from dataclasses import dataclass, field
from fnmatch import fnmatch
from pathlib import Path

import click

from .config import Config, InvalidConfig, NoImportanizeConfig
from .formatters import FORMATTERS, Formatter
from .groups import ImportGroups
from .parser import (
    Artifacts,
    ParseError,
    get_tree_artifacts,
    parse_imports_from_tree,
    parse_to_tree,
)
from .plugins import (
    NOT_PIPED_PLUGIN_NAMES,
    deactivate_all_plugins,
    ensure_activated_plugins,
)
from .statements import ImportStatement
from .utils import StdPath, generate_diff, takeafter


log = logging.getLogger(__name__)


@dataclass
class RuntimeConfig:
    _paths: typing.Iterable[Path] = ()
    path_names: typing.Iterable[str] = ()

    formatter_name: typing.Union[str, None] = None
    length: typing.Union[int, None] = Config.length
    should_add_last_line: bool = True

    _config: typing.Optional[Config] = None
    root_config: Config = Config.default()
    config_path: typing.Optional[str] = None
    is_subconfig_allowed: bool = True
    are_plugins_allowed: bool = None
    should_deactivate_piped_plugins: bool = None
    found_configs: typing.Dict[Path, Config] = field(default_factory=lambda: {})

    verbosity: int = 0

    is_version_mode: bool = False
    is_list_mode: bool = False

    is_ci_mode: bool = False
    show_diff: bool = False

    is_print_mode: bool = False
    show_header: bool = True

    is_in_piped: bool = False
    is_out_piped: bool = False
    stdin: typing.TextIO = sys.stdin
    stdout: typing.TextIO = sys.stdout

    @property
    def paths(self) -> typing.List[Path]:
        return list(self._paths) or [StdPath(i) for i in self.path_names]

    @property
    def config(self) -> Config:
        self._config = (
            self._config
            if self._config is not None
            else Config.from_path(self.config_path, strict=True) or self.root_config
        )
        return self._config

    @property
    def formatter(self) -> typing.Type[Formatter]:
        return (
            FORMATTERS[self.formatter_name]
            if self.formatter_name
            else self.config.formatter
        )

    @property
    def add_imports(self) -> typing.Iterable[ImportStatement]:
        return [] if "-" in self.path_names else self.config.add_imports

    @property
    def config_length(self) -> int:
        return self.length or self.config.length

    @property
    def merged_config(self) -> Config:
        try:
            return self._merged_config
        except AttributeError:
            self._merged_config: Config = self.config.merge(
                Config(
                    length=self.config_length,
                    formatter=self.formatter,
                    add_imports=self.add_imports,
                    are_plugins_allowed=self.are_plugins_allowed,
                )
            )
            return self._merged_config

    def normalize(self) -> "RuntimeConfig":
        is_input_stdin = self.is_in_piped or "-" in self.path_names
        any_files_given = bool([i for i in self.path_names if i != "-"])

        if is_input_stdin and not any_files_given:
            assert (
                self.is_in_piped
            ), '"-" is given as input path however stdin is not piped'
            self.path_names = ["-"]
            self.is_print_mode = True
            self.show_header = False
            self.should_add_last_line = False
            self.should_deactivate_piped_plugins = True

        if self.is_out_piped:
            self.is_print_mode = True

        if self.show_diff:
            self.show_header = False

        return self

    @property
    def aggregator(self) -> "BaseAggregator":
        if self.is_ci_mode:
            return CIAggregator(self)
        elif self.is_list_mode:
            return ListAggregator(self)
        elif self.is_print_mode:
            return PrintAggregator(self)
        else:
            return Aggregator(self)


@dataclass
class Result:
    path: Path
    imports: typing.Iterable[ImportStatement] = ()
    groups: ImportGroups = ImportGroups()
    original: str = ""
    organized: str = ""
    error: typing.Optional[Exception] = None

    @property
    def has_changes(self) -> bool:
        return self.original != self.organized

    @property
    def is_success(self) -> bool:
        return self.error is None


def replace_imports_in_text(
    text: str,
    groups: ImportGroups,
    config: Config,
    artifacts: Artifacts,
    runtime_config: RuntimeConfig,
) -> str:
    line_numbers = groups.all_line_numbers()
    line = min(line_numbers) if line_numbers else None
    first_import_line_number = line or artifacts.first_line

    lines = [l for i, l in enumerate(text.splitlines()) if i not in line_numbers]
    lines_after = list(takeafter(lambda i: i.strip(), lines[first_import_line_number:]))

    formatted_imports = groups.formatted()

    return artifacts.sep.join(
        lines[:first_import_line_number]
        + formatted_imports.splitlines()
        + (
            [""] * config.after_imports_new_lines
            if lines_after and formatted_imports
            else []
        )
        + lines_after
        + ([""] if runtime_config.should_add_last_line else [])
    )


def run_importanize_on_text(
    text: str, path: Path, config: Config, runtime_config: RuntimeConfig
) -> typing.Iterator[Result]:
    try:
        tree = parse_to_tree(text)

    except ParseError as e:
        log.error(f"Could not parse {path} {e}")
        yield Result(path=path, error=e)

    else:
        artifacts = get_tree_artifacts(tree, text)
        imports = list(parse_imports_from_tree(tree))

        log.debug(f"Found {len(imports)} imports in {path}")

        try:
            groups = ImportGroups.from_config(
                config=config, artifacts=artifacts, statements=imports
            )

        except ValueError as e:
            log.error(f"Could not importanize {path} {e}")
            yield Result(path=path, error=e)

        else:
            organized = replace_imports_in_text(
                text,
                groups=groups,
                config=config,
                artifacts=artifacts,
                runtime_config=runtime_config,
            )
            log.debug(f"Successfully importanized {path}")

            yield Result(
                path=path,
                imports=imports,
                groups=groups,
                original=text,
                organized=organized,
            )


def run_importanize_on_file(
    source: Path, config: Config, runtime_config: RuntimeConfig
) -> typing.Iterator[Result]:
    log.debug(f"About to importanize {source}")

    if runtime_config.is_subconfig_allowed:
        subconfig = Config.find(
            cwd=source.parent,
            root=getattr(config.path, "parent", None),
            cache=runtime_config.found_configs,
        )
        if subconfig:
            config = subconfig
            log.info(f"Found subconfig {subconfig}")

    if should_skip(source, config):
        log.info(f"Skipping {source} as per {config}")
        return

    try:
        text = source.read_text()

    except UnicodeDecodeError as e:
        log.error(f"Could not read {source} {e}")
        yield Result(path=source, error=e)

    else:
        yield from run_importanize_on_text(
            text, path=source, config=config, runtime_config=runtime_config
        )


def run_importanize_on_dir(
    source: Path, config: Config, runtime_config: RuntimeConfig,
) -> typing.Iterator[Result]:
    if runtime_config.is_subconfig_allowed:
        subconfig = Config.find(
            cwd=source.parent,
            root=getattr(config.path, "parent", None),
            cache=runtime_config.found_configs,
        )
        if subconfig:
            config = subconfig
            log.info(f"Found subconfig {subconfig}")

    if should_skip(source, config):
        log.info(f"Skipping {source} as per {config}")
        return

    items = (
        f
        for f in source.iterdir()
        if not f.is_file() or f.is_file() and f.suffixes == [".py"]
    )

    for i in items:
        yield from run_importanize_on_source(
            i, config=config, runtime_config=runtime_config
        )


def run_importanize_on_source(
    source: Path, runtime_config: RuntimeConfig, config: Config = None
) -> typing.Iterator[Result]:
    config = config if config is not None else runtime_config.merged_config

    if source.is_file():
        yield from run_importanize_on_file(
            source, config=config, runtime_config=runtime_config
        )
    elif source.is_dir():
        yield from run_importanize_on_dir(
            source, config=config, runtime_config=runtime_config
        )


def should_skip(source: Path, config: Config) -> bool:
    norm = relative = os.path.normpath(os.path.abspath(str(source)))
    norm_path = Path(norm)
    with suppress(ValueError):
        relative = str(
            norm_path.relative_to(getattr(config.path, "parent", norm_path.root))
        )
    absolute_match = any(fnmatch(norm, i) for i in config.exclude)
    relative_match = any(fnmatch(relative, i,) for i in config.exclude)
    return absolute_match or relative_match


class BaseAggregator(metaclass=abc.ABCMeta):
    def __init__(self, runtime_config: RuntimeConfig):
        self.runtime_config = runtime_config
        self.is_success = True
        self._init()

    def _init(self) -> None:
        """
        Hook for subclasses to init custom state
        """

    @abc.abstractmethod
    def update(self, result: Result) -> None:
        """
        """

    def finish(self) -> int:
        return 0

    def __call__(self) -> int:
        try:
            merged_config = self.runtime_config.merged_config
        except (NoImportanizeConfig, InvalidConfig) as e:
            log.error(f"{e}")
            return 1

        if not merged_config.are_plugins_allowed:
            deactivate_all_plugins()
        else:
            ensure_activated_plugins(
                set(merged_config.plugins)
                - (
                    set(NOT_PIPED_PLUGIN_NAMES)
                    if self.runtime_config.should_deactivate_piped_plugins
                    else set()
                )
            )

        for source in self.runtime_config.paths:
            for result in run_importanize_on_source(
                source=source, runtime_config=self.runtime_config, config=merged_config
            ):
                if result.is_success:
                    self.update(result)
                else:
                    self.is_success = False

        finished = self.finish()
        return int(not self.is_success) or finished


class DiffAggregator(BaseAggregator):
    def show_diff(self, result: Result) -> None:
        if result.has_changes and self.runtime_config.show_diff:
            click.echo(
                generate_diff(
                    result.original,
                    result.organized,
                    str(result.path),
                    color=(
                        not self.runtime_config.is_in_piped
                        and not self.runtime_config.is_out_piped
                    ),
                ),
                file=self.runtime_config.stdout,
            )


class CIAggregator(DiffAggregator):
    def _init(self) -> None:
        self.changes: int = 0

    def update(self, result: Result) -> None:
        self.changes += int(result.has_changes)
        if result.has_changes:
            log.error(f"Imports not organized {result.path}")
            self.show_diff(result)
        else:
            log.info(f"Nothing to do {result.path}")

    def finish(self) -> int:
        return int(bool(self.changes))


class ListAggregator(BaseAggregator):
    def _init(self) -> None:
        self.groups: ImportGroups = ImportGroups.from_config(
            self.runtime_config.merged_config,
        )

    def update(self, result: Result) -> None:
        for i in result.imports:
            self.groups.add_statement(i)

    def finish(self) -> int:
        for g in self.groups.groups:
            click.echo(g.group_config.type, file=self.runtime_config.stdout)
            click.echo("-" * len(g.group_config.type), file=self.runtime_config.stdout)
            for s in g.unique_statements:
                click.echo(f"{s}", file=self.runtime_config.stdout)
            click.echo("", file=self.runtime_config.stdout)
        return 0


class PrintAggregator(DiffAggregator):
    def update(self, result: Result) -> None:
        if self.runtime_config.show_header and result.path.name != "-":
            click.echo("=" * len(str(result.path)), file=self.runtime_config.stdout)
            click.echo(result.path, file=self.runtime_config.stdout)
            click.echo("=" * len(str(result.path)), file=self.runtime_config.stdout)

        if self.runtime_config.show_diff:
            self.show_diff(result)

        else:
            if result.path.name == "-":
                # stdout files do custom logic to read/write files
                result.path.write_text(result.organized)
            else:
                click.echo(result.organized, file=self.runtime_config.stdout)


class Aggregator(BaseAggregator):
    def update(self, result: Result) -> None:
        if result.has_changes:
            log.info(f"Importanized {result.path}")
            result.path.write_text(result.organized)
        else:
            log.info(f"Nothing to do {result.path}")
