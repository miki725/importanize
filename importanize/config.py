# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
import configparser
import io
import json
import logging
import pathlib

from .formatters import DEFAULT_FORMATTER, DEFAULT_LENGTH


IMPORTANIZE_JSON_CONFIG = ".importanizerc"
IMPORTANIZE_INI_CONFIG = "importanize.ini"
IMPORTANIZE_SETUP_CONFIG = "setup.cfg"
IMPORTANIZE_CONFIG = [
    IMPORTANIZE_JSON_CONFIG,
    IMPORTANIZE_INI_CONFIG,
    IMPORTANIZE_SETUP_CONFIG,
]
PEP8_CONFIG = {
    "groups": [
        {"type": "stdlib"},
        {"type": "sitepackages"},
        {"type": "remainder"},
        {"type": "local"},
    ]
}
log = logging.getLogger(__name__)


class InvalidConfig(Exception):
    """
    Exception to indicate invalid configuration is found
    """


class Config(dict):
    def __init__(self, *args, **kwargs):
        self.path = kwargs.pop("path", None)
        super().__init__(*args, **kwargs)
        self.normalize()

    def normalize(self):
        self["after_imports_new_lines"] = int(
            self.get("after_imports_new_lines", 2)
        )
        self["length"] = int(self.get("length", DEFAULT_LENGTH))
        self["formatter"] = self.get("formatter", DEFAULT_FORMATTER)
        self["groups"] = self.get("groups", PEP8_CONFIG["groups"])

    @classmethod
    def default(cls):
        return cls(PEP8_CONFIG)

    @staticmethod
    def from_json(value):
        try:
            return json.loads(value)
        except ValueError:
            return None

    @staticmethod
    def from_ini(value):
        parser = configparser.ConfigParser()

        try:
            getattr(parser, "read_file", getattr(parser, "readfp", None))(
                io.StringIO(value)
            )
            config = dict(parser.items("importanize"))
        except (KeyError, configparser.MissingSectionHeaderError):
            return None

        config["exclude"] = [
            i.strip()
            for i in config.get("exclude", "").split("\n")
            if i.strip()
        ]
        config["add_imports"] = [
            i.strip()
            for i in config.get("add_imports", "").split("\n")
            if i.strip()
        ]
        config["groups"] = [
            (
                dict(
                    {"type": "packages"},
                    **{
                        "packages": [
                            j.strip()
                            for j in dict(
                                parser.items("importanize:{}".format(i.strip()))
                            )
                            .get("packages", "")
                            .split("\n")
                            if j.strip()
                        ]
                    }
                )
                if parser.has_section("importanize:{}".format(i.strip()))
                else {"type": i.strip()}
            )
            for i in config.get("groups").split("\n")
            if i.strip()
        ]

        return config

    @staticmethod
    def invalid():
        raise InvalidConfig()

    @classmethod
    def from_path(cls, path):
        if not path:
            return cls.default()

        path = pathlib.Path(path)
        data = path.read_text("utf-8")
        return cls(
            Config.from_json(data) or Config.from_ini(data) or Config.invalid(),
            path=path,
        )

    @classmethod
    def find(cls, cwd=None, root=None):
        cwd = cwd or pathlib.Path.cwd()
        path = cwd = cwd.resolve()

        while path.resolve() != pathlib.Path(root or cwd.root).resolve():
            for f in IMPORTANIZE_CONFIG:
                config_path = path / f
                if config_path.exists():
                    try:
                        return Config.from_path(config_path)
                    except InvalidConfig:
                        return cls.default()

            path = path.parent

        return cls.default()

    def __str__(self):
        return str(self.path or "<default pep8>")

    def __bool__(self):
        return bool(self.path)

    __nonzero__ = __bool__
