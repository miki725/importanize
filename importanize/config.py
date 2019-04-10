# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
import configparser
import io
import itertools
import json
import logging
import os
import pathlib
import typing
from contextlib import suppress
from dataclasses import dataclass

from . import formatters
from .groups import GROUPS
from .parser import parse_imports
from .statements import ImportStatement


IMPORTANIZE_JSON_CONFIG = ".importanizerc"
IMPORTANIZE_INI_CONFIG = "importanize.ini"
IMPORTANIZE_SETUP_CONFIG = "setup.cfg"
IMPORTANIZE_TOX_CONFIG = "tox.ini"
IMPORTANIZE_CONFIG = [
    IMPORTANIZE_JSON_CONFIG,
    IMPORTANIZE_INI_CONFIG,
    IMPORTANIZE_SETUP_CONFIG,
    IMPORTANIZE_TOX_CONFIG,
]

FORMATTERS: typing.Dict[str, typing.Type[formatters.Formatter]] = {
    formatter.name: formatter
    for formatter in vars(formatters).values()
    if (
        isinstance(formatter, type)
        and formatter is not formatters.Formatter
        and issubclass(formatter, formatters.Formatter)
    )
}

log = logging.getLogger(__name__)


class InvalidConfig(Exception):
    """
    Exception to indicate invalid configuration is found
    """


@dataclass
class GroupConfig:
    type: str
    packages: typing.Iterable[str] = ()

    @classmethod
    def default(cls) -> "GroupConfig":
        return cls(type="default")

    def as_dict(self) -> typing.Dict[str, typing.Any]:
        return {
            "type": self.type,
            **({"packages": self.packages} if self.packages else {}),
        }


@dataclass
class Config:
    path: typing.Union[pathlib.Path, None] = None
    after_imports_new_lines: int = 2
    length: int = 80
    formatter: typing.Type[formatters.Formatter] = formatters.GroupedFormatter
    groups: typing.Iterable[GroupConfig] = (
        GroupConfig(type="stdlib"),
        GroupConfig(type="sitepackages"),
        GroupConfig(type="remainder"),
        GroupConfig(type="local"),
    )
    exclude: typing.Iterable[str] = ("*/.tox/*",)
    add_imports: typing.Iterable[ImportStatement] = ()

    @classmethod
    def default(cls) -> "Config":
        return cls()

    @property
    def relpath(self) -> str:
        return os.path.relpath(self.path) if self.path else "<default pep8>"

    @classmethod
    def from_json(cls, path: pathlib.Path, data: str) -> "Config":
        try:
            loaded_data = json.loads(data)
        except ValueError:
            raise InvalidConfig

        try:
            return cls(
                path=path,
                after_imports_new_lines=int(
                    loaded_data.get(
                        "after_imports_new_lines", cls.after_imports_new_lines
                    )
                ),
                length=int(loaded_data.get("length", cls.length)),
                formatter=(
                    FORMATTERS[loaded_data.get("formatter")]
                    if "formatter" in loaded_data
                    else cls.formatter
                ),
                groups=(
                    [
                        GROUPS[i.get("type")].validate_group_config(
                            GroupConfig(
                                type=i.get("type"), packages=i.get("packages") or ()
                            )
                        )
                        for i in loaded_data.get("groups", [])
                    ]
                    or cls.groups
                ),
                exclude=loaded_data.get("exclude", cls.exclude),
                add_imports=list(
                    itertools.chain(
                        *[
                            [s.with_line_numbers([]) for s in parse_imports(i)]
                            for i in loaded_data.get("add_imports", [])
                        ]
                    )
                )
                or cls.add_imports,
            )
        except Exception as e:
            raise InvalidConfig from e

    @classmethod
    def from_ini(cls, path: pathlib.Path, data: str) -> "Config":
        parser = configparser.ConfigParser()

        try:
            getattr(parser, "read_file", getattr(parser, "readfp", None))(
                io.StringIO(data)
            )
            loaded_data = dict(parser.items("importanize"))
        except (
            KeyError,
            configparser.MissingSectionHeaderError,
            configparser.NoSectionError,
        ):
            raise InvalidConfig

        try:
            return cls(
                path=path,
                after_imports_new_lines=int(
                    loaded_data.get(
                        "after_imports_new_lines", cls.after_imports_new_lines
                    )
                ),
                length=int(loaded_data.get("length", cls.length)),
                formatter=FORMATTERS.get(
                    loaded_data.get("formatter", ""), cls.formatter
                ),
                groups=(
                    [
                        GROUPS[i.split(":")[0].strip()].validate_group_config(
                            GroupConfig(
                                type=i.split(":")[0].strip(),
                                packages=[
                                    j.strip() for j in i.split(":", 1)[1].split(",")
                                ]
                                if ":" in i
                                else [],
                            )
                        )
                        for i in loaded_data.get("groups", "").split("\n")
                        if i.strip()
                    ]
                    or cls.groups
                ),
                exclude=[
                    i.strip()
                    for i in loaded_data.get("exclude", "").split("\n")
                    if i.strip()
                ]
                or cls.exclude,
                add_imports=list(
                    itertools.chain(
                        *[
                            [s.with_line_numbers([]) for s in parse_imports(i.strip())]
                            for i in loaded_data.get("add_imports", "").split("\n")
                            if i.strip()
                        ]
                    )
                )
                or cls.add_imports,
            )
        except Exception:
            raise InvalidConfig

    @classmethod
    def from_path(cls, path: str = None, log_errors: bool = True) -> "Config":
        if not path:
            return cls.default()

        parsed_path = pathlib.Path(path)
        data = parsed_path.read_text("utf-8")

        with suppress(InvalidConfig):
            return cls.from_json(parsed_path, data)
        with suppress(InvalidConfig):
            return cls.from_ini(parsed_path, data)

        if log_errors:
            log.error(f"Could not read config {path!r} in either json or ini formats")

        raise InvalidConfig

    @classmethod
    def find(
        cls,
        cwd: pathlib.Path = None,
        root: pathlib.Path = None,
        log_errors: bool = True,
    ) -> "Config":
        cwd = cwd or pathlib.Path.cwd()
        path = cwd = cwd.resolve()

        while path.resolve() != pathlib.Path(root or cwd.root).resolve():
            for f in IMPORTANIZE_CONFIG:
                config_path = path / f
                if config_path.exists():
                    try:
                        return Config.from_path(str(config_path), log_errors=log_errors)
                    except InvalidConfig:
                        return cls.default()

            path = path.parent

        return cls.default()

    def merge(self, other: "Config") -> "Config":
        self.length = other.length
        self.formatter = other.formatter
        self.add_imports = other.add_imports
        return self

    def as_dict(self) -> typing.Dict[str, typing.Any]:
        return {
            "path": str(self.path or ""),
            "after_imports_new_lines": self.after_imports_new_lines,
            "length": self.length,
            "formatter": self.formatter.name,
            "groups": [i.as_dict() for i in self.groups],
            "exclude": list(self.exclude),
            "add_imports": [str(i) for i in self.add_imports],
        }

    def as_json(self) -> str:
        return json.dumps(self.as_dict(), indent=2, sort_keys=True)

    def __repr__(self) -> str:
        return self.as_json()

    def __str__(self) -> str:
        return self.relpath

    def __bool__(self) -> bool:
        return bool(self.path)
