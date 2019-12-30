# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
import json
from pathlib import Path
from unittest import mock

import pytest  # type: ignore

from importanize.config import (
    IMPORTANIZE_SETUP_CONFIG,
    Config,
    GroupConfig,
    InvalidConfig,
    NoImportanizeConfig,
)
from importanize.formatters import LinesFormatter
from importanize.statements import ImportStatement
from importanize.utils import StdPath


class TestGroupConfig:
    def test_default(self) -> None:
        assert GroupConfig.default().type == "default"

    def test_as_dict(self) -> None:
        assert GroupConfig.default().as_dict() == {"type": "default"}
        assert GroupConfig(type="packages", packages=["foo"]).as_dict() == {
            "type": "packages",
            "packages": ["foo"],
        }


class TestConfig:
    def test_default(self) -> None:
        assert "*/.tox/*" in Config.default().exclude

    def test_json_invalid_json(self) -> None:
        with pytest.raises(NoImportanizeConfig):
            Config.from_json(StdPath("invalid.json"), "invalid data")
        with pytest.raises(InvalidConfig):
            Config.from_json(StdPath("invalid.json"), "{'length': 'a'}")

    def test_json(self) -> None:
        assert Config.from_json(StdPath("config.json"), "{}") == Config(
            StdPath("config.json")
        )
        assert Config.from_json(
            StdPath("config.json"),
            json.dumps(
                {
                    "after_imports_new_lines": "5",
                    "length": "100",
                    "formatter": "lines",
                    "groups": [{"type": "remainder"}],
                    "exclude": ["exclude"],
                    "add_imports": ["import foo"],
                }
            ),
        ) == Config(
            path=StdPath("config.json"),
            after_imports_new_lines=5,
            length=100,
            formatter=LinesFormatter,
            groups=[GroupConfig(type="remainder")],
            exclude=["exclude"],
            add_imports=(ImportStatement("foo"),),
        )

    def test_ini_no_section(self) -> None:
        with pytest.raises(NoImportanizeConfig):
            Config.from_ini(StdPath("invalid.ini"), "")

    def test_ini_invalid_group_name(self) -> None:
        with pytest.raises(InvalidConfig):
            Config.from_ini(
                StdPath("invalid.ini"),
                "\n".join(["[importanize]", "groups=", "  foo"]),
            )

    def test_ini_invalid_require_packages(self) -> None:
        with pytest.raises(InvalidConfig):
            Config.from_ini(
                StdPath("invalid.ini"),
                "\n".join(["[importanize]", "groups=", "  packages"]),
            )

    def test_ini_invalid_add_imports(self) -> None:
        with pytest.raises(InvalidConfig):
            Config.from_ini(
                StdPath("invalid.ini"),
                "\n".join(["[importanize]", "add_imports=", "  from foo from bar"]),
            )

    def test_ini_invalid_formatter(self) -> None:
        with pytest.raises(InvalidConfig):
            Config.from_ini(
                StdPath("invalid.ini"), "\n".join(["[importanize]", "formatter=foo"]),
            )

    def test_ini_invalid_length(self) -> None:
        with pytest.raises(InvalidConfig):
            Config.from_ini(
                StdPath("invalid.ini"), "\n".join(["[importanize]", "length=a"])
            )
        with pytest.raises(InvalidConfig):
            Config.from_ini(
                StdPath("invalid.ini"), "\n".join(["[importanize]", "length=1"])
            )

    def test_ini_invalid_new_lines(self) -> None:
        with pytest.raises(InvalidConfig):
            Config.from_ini(
                StdPath("invalid.ini"),
                "\n".join(["[importanize]", "after_imports_new_lines=a"]),
            )
        with pytest.raises(InvalidConfig):
            Config.from_ini(
                StdPath("invalid.ini"),
                "\n".join(["[importanize]", "after_imports_new_lines=10"]),
            )

    def test_ini_invalid_plugins(self) -> None:
        with pytest.raises(InvalidConfig):
            Config.from_ini(
                StdPath("invalid.ini"), "\n".join(["[importanize]", "plugins=\n  foo"]),
            )

    def test_ini(self) -> None:
        Config.from_ini(StdPath("config.ini"), "\n".join(["[importanize]"])) == Config(
            StdPath("config.ini")
        )
        Config.from_ini(
            StdPath("config.ini"),
            "\n".join(
                [
                    "[importanize]",
                    "after_imports_new_lines=5",
                    "length=100",
                    "formatter=lines",
                    "groups=",
                    "   stdlib",
                    "   packages:mypackage",
                    "exclude=exclude",
                    "add_imports=",
                    "   import foo",
                    "allow_plugins=false",
                ]
            ),
        ) == Config(
            path=StdPath("config.json"),
            after_imports_new_lines=5,
            length=100,
            formatter=LinesFormatter,
            groups=[
                GroupConfig(type="stdlib"),
                GroupConfig(type="packages", packages=["foo"]),
            ],
            exclude=["exclude"],
            add_imports=[ImportStatement("foo")],
            are_plugins_allowed=False,
        )

    def test_from_path_no_path(self) -> None:
        assert not Config.from_path(None)

    def test_from_path_strict(self) -> None:
        with pytest.raises(NoImportanizeConfig):
            Config.from_path(__file__, strict=True)

    def test_find_invalid(self) -> None:
        path = Path(__file__).parent / "test_data" / "invalid"
        assert not Config.find(path, root=path.parent)

    def test_find_config(self) -> None:
        config = Config.find(Path(__file__))
        expected_config = Path(__file__).parent.parent / IMPORTANIZE_SETUP_CONFIG

        assert config.path == expected_config

    def test_find_config_current_dir(self) -> None:
        # If path is a file, and we have a config for the project and no
        # subconfig, and we dont find the config for the file, return the
        # passed config.
        config = Config.find(Path("tests/test_main.py"))
        # Instead of thekabsolute path, assume, user is running importanize
        # from the current directory.
        expected_config = Path(__file__).parent.parent / IMPORTANIZE_SETUP_CONFIG

        assert config.path == expected_config

    @mock.patch.object(Path, "read_text", mock.Mock(return_value="invalid data"))
    def test_find_config_current_dir_invalid(self) -> None:
        assert not Config.find(StdPath("tests/test_main.py"))

    def test_find_config_nonfound(self) -> None:
        assert not Config.find(Path(Path(__file__).root))

    def test_merge(self) -> None:
        c = Config.default().merge(Config(length=100, formatter=LinesFormatter))
        assert c.length == 100
        assert c.formatter is LinesFormatter

    def test_as_dict(self) -> None:
        assert Config.default().as_dict()["formatter"] == "grouped"
        assert Config.default().as_dict()["groups"][0] == {"type": "stdlib"}

    def test_as_json(self) -> None:
        c = Config.default()
        assert json.loads(c.as_json()) == c.as_dict()

    def test_str(self) -> None:
        assert str(Config.default()) == "<default pep8>"
        assert str(Config(path=Path("setup.py"))) == "setup.py"

    def test_repr(self) -> None:
        assert repr(Config.default()) == Config.default().as_ini()

    def test_bool(self) -> None:
        assert not Config.default()
        assert Config(path=Path("setup.py"))
