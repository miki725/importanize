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
from dataclasses import dataclass

from . import formatters
from .groups import GROUPS
from .parser import ParseError, parse_imports
from .statements import ImportStatement


IMPORTANIZE_HIDDEN_CONFIG = ".importanizerc"
IMPORTANIZE_JSON_CONFIG = "importanize.json"
IMPORTANIZE_INI_CONFIG = "importanize.ini"
IMPORTANIZE_SETUP_CONFIG = "setup.cfg"
IMPORTANIZE_TOX_CONFIG = "tox.ini"
IMPORTANIZE_CONFIG = [
    IMPORTANIZE_HIDDEN_CONFIG,
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


class NoImportanizeConfig(Exception):
    """
    Exception to indicate importanize configuration is not present
    """


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
    are_plugins_allowed: bool = True

    @classmethod
    def default(cls) -> "Config":
        return cls()

    @property
    def relpath(self) -> str:
        return os.path.relpath(self.path) if self.path else "<default pep8>"

    @classmethod
    def _parse_group(
        cls, group_type: str, packages: typing.Iterable[str]
    ) -> GroupConfig:
        try:
            return GROUPS[group_type.strip()].validate_group_config(
                GroupConfig(type=group_type, packages=packages)
            )
        except KeyError as e:
            raise InvalidConfig(
                f"{group_type!r} is unsupported group type. "
                f'Only {", ".join(GROUPS.keys())} are supported.'
            ) from e
        except ValueError as e:
            raise InvalidConfig(f"{e}") from e

    @classmethod
    def _parse_add_imports(
        cls, add_imports: typing.List[str]
    ) -> typing.Iterable[ImportStatement]:
        try:
            return tuple(
                itertools.chain(
                    *[
                        [s.with_line_numbers([]) for s in parse_imports(i.strip())]
                        for i in add_imports
                        if i.strip()
                    ]
                )
            )
        except ParseError as e:
            raise InvalidConfig(
                "'add_imports' has invalid Python import statement"
            ) from e

    @classmethod
    def _parse_formatter(
        cls, formatter: typing.Optional[str]
    ) -> typing.Type[formatters.Formatter]:
        try:
            return FORMATTERS[formatter] if formatter else cls.formatter
        except KeyError as e:
            raise InvalidConfig(
                f"{formatter!r} is unsupported formatter. "
                f"Only {', '.join(FORMATTERS.keys())} are supported."
            ) from e

    @classmethod
    def _parse_length(cls, length: str) -> int:
        try:
            result = int(length)
        except ValueError as e:
            raise InvalidConfig(f"{length!r} is not an integer") from e
        if 10 <= result <= 200:
            return result
        raise InvalidConfig("Length must be between 10 and 200")

    @classmethod
    def _parse_after_imports_new_lines(cls, new_lines: str) -> int:
        try:
            result = int(new_lines)
        except ValueError as e:
            raise InvalidConfig(f"{new_lines!r} is not an integer") from e
        if 0 <= result <= 5:
            return result
        raise InvalidConfig("Can only add between 0 and 5 new lines after imports")

    @classmethod
    def from_json(cls, path: pathlib.Path, data: str) -> "Config":
        # not a json file altogether
        if not data.strip().startswith("{") or not data.strip().endswith("}"):
            raise NoImportanizeConfig("Not a json file")

        # looks like a json file but syntax could be incorrect
        try:
            loaded_data = json.loads(data)
        except ValueError as e:
            raise InvalidConfig(f"{type(e).__name__}: not a json file") from e

        groups = []
        for i in loaded_data.get("groups", []):
            groups.append(cls._parse_group(i.get("type"), i.get("packages") or ()))

        return cls(
            path=path,
            after_imports_new_lines=cls._parse_after_imports_new_lines(
                loaded_data.get(
                    "after_imports_new_lines", str(cls.after_imports_new_lines)
                )
            ),
            length=cls._parse_length(loaded_data.get("length", str(cls.length))),
            formatter=cls._parse_formatter(loaded_data.get("formatter", "")),
            groups=groups or cls.groups,
            exclude=loaded_data.get("exclude", cls.exclude),
            add_imports=cls._parse_add_imports(
                loaded_data.get("add_imports", [str(i) for i in cls.add_imports])
            ),
            are_plugins_allowed=(
                str(loaded_data.get("allow_plugins", str(cls.are_plugins_allowed)))
                .strip()
                .lower()
                == "true"
            ),
        )

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
        ) as e:
            raise NoImportanizeConfig(f"{type(e).__name__}: {e}") from e

        groups: typing.List[GroupConfig] = []
        for i in (i for i in loaded_data.get("groups", "").split("\n") if i.strip()):
            try:
                group_type, packages_str = i.split(":", 1)
                packages = packages_str.split(",")
            except ValueError:
                group_type, packages = i.split(":")[0], []
            finally:
                groups.append(cls._parse_group(group_type, packages))

        return cls(
            path=path,
            after_imports_new_lines=cls._parse_after_imports_new_lines(
                loaded_data.get(
                    "after_imports_new_lines", str(cls.after_imports_new_lines)
                )
            ),
            length=cls._parse_length(loaded_data.get("length", str(cls.length))),
            formatter=cls._parse_formatter(loaded_data.get("formatter", "")),
            groups=groups or cls.groups,
            exclude=[
                i.strip()
                for i in loaded_data.get("exclude", "\n".join(cls.exclude)).split("\n")
                if i.strip()
            ],
            add_imports=cls._parse_add_imports(
                loaded_data.get(
                    "add_imports", "\n".join(str(i) for i in cls.add_imports)
                ).split("\n")
            ),
            are_plugins_allowed=(
                loaded_data.get("allow_plugins", str(cls.are_plugins_allowed))
                .strip()
                .lower()
                == "true"
            ),
        )

    @classmethod
    def from_path(cls, path: str = None, strict: bool = False) -> "Config":
        if not path:
            return cls.default()

        parsed_path = pathlib.Path(path)
        data = parsed_path.read_text("utf-8")
        no_config_errors = []
        errors = []

        json_prefix = f"{os.path.relpath(path)}[json] - "
        try:
            return cls.from_json(parsed_path, data)
        except NoImportanizeConfig as e:
            msg = f"{json_prefix}{type(e).__name__}: {e}"
            no_config_errors.append(msg)
            if not strict:
                log.debug(msg)
        except Exception as e:
            errors.append(f"{json_prefix}{type(e).__name__}: {e}")

        ini_prefix = f"{os.path.relpath(path)}[ini] - "
        try:
            return cls.from_ini(parsed_path, data)
        except NoImportanizeConfig as e:
            msg = f"{ini_prefix}{type(e).__name__}: {e}"
            no_config_errors.append(msg)
            if not strict:
                log.debug(msg)
        except Exception as e:
            errors.append(f"{ini_prefix}{type(e).__name__}: {e}")

        if errors:
            raise InvalidConfig("\n".join(errors))
        elif strict:
            raise NoImportanizeConfig("\n".join(no_config_errors))
        else:
            return cls.default()

    @classmethod
    def find(
        cls,
        cwd: pathlib.Path = None,
        root: pathlib.Path = None,
        log_errors: bool = True,
        cache: typing.Dict[pathlib.Path, "Config"] = None,
    ) -> "Config":
        cache = cache if cache is not None else {}
        cwd = cwd or pathlib.Path.cwd()
        path = cwd = cwd.resolve()

        try:
            return cache[cwd]

        except KeyError:
            while path.resolve() != pathlib.Path(root or cwd.root).resolve():
                try:
                    return cache[path]

                except KeyError:
                    config = Config.default()
                    exists = [
                        j for j in (path / i for i in IMPORTANIZE_CONFIG) if j.exists()
                    ]

                    for f in exists:
                        try:
                            config = Config.from_path(str(f))
                            if config:
                                break
                        except InvalidConfig as e:
                            if log_errors:
                                log.error(f"{e}")

                    cache[path] = cache[cwd] = config

                    if config:
                        return config

                path = path.parent

            default = cls.default()
            return default

    def merge(self, other: "Config") -> "Config":
        self.length = other.length
        self.formatter = other.formatter
        self.add_imports = other.add_imports
        self.are_plugins_allowed = (
            other.are_plugins_allowed
            if other.are_plugins_allowed is not None
            else self.are_plugins_allowed
        )
        return self

    def as_dict(self) -> typing.Dict[str, typing.Any]:
        return {
            "path": str(self.relpath or ""),
            "after_imports_new_lines": self.after_imports_new_lines,
            "length": self.length,
            "formatter": self.formatter.name,
            "groups": [i.as_dict() for i in self.groups],
            "exclude": list(self.exclude),
            "add_imports": [str(i) for i in self.add_imports],
            "allow_plugins": self.are_plugins_allowed,
        }

    def _as_ini_groups(
        self, packages: typing.List[typing.Dict[str, typing.Any]]
    ) -> typing.List[str]:
        return [
            ":".join(filter(None, [i["type"], ",".join(i.get("packages", []))],))
            for i in packages
        ]

    def as_ini(self) -> str:
        return "[importanize]\n" + "\n".join(
            [
                "{}={}".format(
                    k,
                    "\n  ".join([""] + getattr(self, f"_as_ini_{k}", lambda x: x)(v))
                    if isinstance(v, list)
                    else str(v),
                ).rstrip()
                for k, v in self.as_dict().items()
            ]
        )

    def as_json(self) -> str:
        return json.dumps(self.as_dict(), indent=2, sort_keys=True)

    def __repr__(self) -> str:
        return self.as_ini()

    def __str__(self) -> str:
        return self.relpath

    def __bool__(self) -> bool:
        return bool(self.path)
