# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import pytest  # type: ignore

from importanize.config import Config, GroupConfig
from importanize.groups import (
    BaseImportGroup as _BaseImportGroup,
    ImportGroups,
    LocalGroup,
    PackagesGroup,
    RemainderGroup,
    SitePackagesGroup,
    StdLibGroup,
)
from importanize.parser import Artifacts
from importanize.statements import ImportLeaf, ImportStatement


class BaseImportGroup(_BaseImportGroup):
    def should_add_statement(self, statement: ImportStatement) -> bool:
        return "add" in statement.stem


class TestBaseImportGroup:
    def test_validate_group_config(self) -> None:
        g = GroupConfig(type="packages", packages=["foo"])
        assert BaseImportGroup.validate_group_config(g) is g

    def test_unique_statements(self) -> None:
        group = BaseImportGroup(
            statements=[
                ImportStatement("a", leafs=[ImportLeaf("b")]),
                ImportStatement("a", leafs=[ImportLeaf("b")]),
                ImportStatement("a", leafs=[ImportLeaf("c")]),
                ImportStatement("b", leafs=[ImportLeaf("c")]),
            ]
        )

        assert sorted(group.unique_statements) == [
            ImportStatement("a", leafs=[ImportLeaf("b"), ImportLeaf("c")]),
            ImportStatement("b", leafs=[ImportLeaf("c")]),
        ]

    def test_unique_statements_leafless(self) -> None:
        group = BaseImportGroup(
            statements=[
                ImportStatement("a", leafs=[ImportLeaf("b")]),
                ImportStatement("a", leafs=[]),
                ImportStatement("b", leafs=[ImportLeaf("c")]),
            ]
        )

        assert sorted(group.unique_statements) == [
            ImportStatement("a", leafs=[]),
            ImportStatement("a", leafs=[ImportLeaf("b")]),
            ImportStatement("b", leafs=[ImportLeaf("c")]),
        ]

    def test_unique_statements_special(self) -> None:
        group = BaseImportGroup(
            statements=[
                ImportStatement("b", leafs=[ImportLeaf("c")]),
                ImportStatement("a", leafs=[ImportLeaf("*")]),
            ]
        )

        assert sorted(group.unique_statements) == [
            ImportStatement("a", leafs=[ImportLeaf("*")]),
            ImportStatement("b", leafs=[ImportLeaf("c")]),
        ]

    def test_all_line_numbers(self) -> None:
        s2 = ImportStatement("b", line_numbers=[2, 7])
        s1 = ImportStatement("a", line_numbers=[1, 2])

        group = BaseImportGroup(statements=[s1, s2])

        assert group.all_line_numbers() == [1, 2, 7]

    def test_add_statement_true(self) -> None:
        group = BaseImportGroup()
        group.add_statement(ImportStatement("add"))

        assert ImportStatement("add") in group.statements

    def test_add_statement_false(self) -> None:
        group = BaseImportGroup()
        group.add_statement(ImportStatement("ignore"))

        assert ImportStatement("ignore") not in group.statements

    def test_as_string(self) -> None:
        group = BaseImportGroup(statements=[ImportStatement("b"), ImportStatement("a")])

        assert str(group) == "import a\nimport b"

    def test_as_string_with_artifacts(self) -> None:
        group = BaseImportGroup(
            statements=[ImportStatement("b"), ImportStatement("a")],
            artifacts=Artifacts(sep="\r\n"),
        )

        assert str(group.as_string()) == "import a\r\nimport b"

    def test_formatted(self) -> None:
        stem = "b" * 80
        group = BaseImportGroup(
            statements=[
                ImportStatement(stem, leafs=[ImportLeaf("c"), ImportLeaf("d")]),
                ImportStatement("a"),
            ]
        )

        assert group.formatted() == "\n".join(
            [f"import a", f"from {stem} import (", f"    c,", f"    d,", f")"]
        )

    def test_formatted_with_artifacts(self) -> None:
        stem = "b" * 80
        group = BaseImportGroup(
            statements=[
                ImportStatement(stem, leafs=[ImportLeaf("c"), ImportLeaf("d")]),
                ImportStatement("a"),
            ],
            artifacts=Artifacts(sep="\r\n"),
        )

        assert group.formatted() == "\r\n".join(
            [f"import a", f"from {stem} import (", f"    c,", f"    d,", f")"]
        )


class TestSitePackagesGroup:
    group = SitePackagesGroup

    def test_should_add_statement(self) -> None:
        assert self.group().should_add_statement(ImportStatement("pytest.test"))
        assert not self.group().should_add_statement(ImportStatement("os.path"))


class TestStdLibGroup:
    group = StdLibGroup

    def test_should_add_statement(self) -> None:
        assert self.group().should_add_statement(ImportStatement("os.path"))
        assert not self.group().should_add_statement(ImportStatement("pytest.test"))


class TestPackagesGroup:
    group = PackagesGroup

    def test_should_add_statement(self) -> None:
        assert self.group(
            group_config=GroupConfig(type="packages", packages=["foo"])
        ).should_add_statement(ImportStatement("foo.bar"))
        assert not self.group(
            group_config=GroupConfig(type="packages", packages=["foo"])
        ).should_add_statement(ImportStatement("os.path"))

    def test_validate_group_config(self) -> None:
        g = GroupConfig(type="packages", packages=["foo"])
        assert self.group.validate_group_config(g) is g
        with pytest.raises(ValueError):
            self.group.validate_group_config(GroupConfig(type="packages"))


class TestLocalGroup:
    group = LocalGroup

    def test_should_add_statement(self) -> None:
        assert self.group().should_add_statement(ImportStatement(".foo.bar"))
        assert not self.group(
            group_config=GroupConfig(type="local")
        ).should_add_statement(ImportStatement("os.path"))


class TestRemainderGroup:
    group = RemainderGroup

    def test_should_add_statement(self) -> None:
        assert self.group().should_add_statement(ImportStatement(".foo.bar"))


class TestImportGroups:
    def test_all_line_numbers(self) -> None:
        assert ImportGroups().all_line_numbers() == []
        assert ImportGroups(
            [
                BaseImportGroup(
                    statements=[ImportStatement("foo", line_numbers=[2, 7])]
                ),
                BaseImportGroup(
                    statements=[ImportStatement("bar", line_numbers=[1, 2])]
                ),
            ]
        ).all_line_numbers() == [1, 2, 7]

    def test_from_config(self) -> None:
        groups = ImportGroups.from_config(
            config=Config(groups=[GroupConfig(type="stdlib")])
        )

        assert len(groups.groups) == 1
        assert isinstance(groups.groups[0], StdLibGroup)

    def test_add_statement(self) -> None:
        groups = ImportGroups([LocalGroup()])

        with pytest.raises(ValueError):
            groups.add_statement(ImportStatement("a"))

        groups.add_statement(ImportStatement(".a"))

        assert groups.groups[0].statements == [ImportStatement(".a")]

    def test_add_statement_priority(self) -> None:
        groups = ImportGroups([RemainderGroup(), LocalGroup()])
        groups.add_statement(ImportStatement(".a"))

        assert groups.groups[0].statements == []
        assert groups.groups[1].statements == [ImportStatement(".a")]

    def test_as_string(self) -> None:
        assert str(ImportGroups()) == ""

    def test_formatted_empty(self) -> None:
        assert ImportGroups().formatted() == ""

    def test_formatted_with_artifacts(self) -> None:
        artifacts = Artifacts(sep="\r\n")

        groups = ImportGroups(
            [RemainderGroup(artifacts=artifacts), LocalGroup(artifacts=artifacts)],
            artifacts=artifacts,
        )

        groups.add_statement(ImportStatement(".a"))
        groups.add_statement(ImportStatement("foo"))

        assert groups.formatted() == "import foo\r\n\r\nimport .a"
