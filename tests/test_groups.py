# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import pytest

from importanize.groups import (
    BaseImportGroup as _BaseImportGroup,
    ImportGroups,
    LocalGroup,
    PackagesGroup,
    RemainderGroup,
    SitePackagesGroup,
    StdLibGroup,
)
from importanize.statements import ImportLeaf, ImportStatement


class BaseImportGroup(_BaseImportGroup):
    def should_add_statement(self, statement):
        return "add" in statement.stem


class TestBaseImportGroup:
    def test_unique_statements(self):
        group = BaseImportGroup(
            statements=[
                ImportStatement("a", leafs=[ImportLeaf("b")]),
                ImportStatement("a", leafs=[ImportLeaf("b")]),
            ]
        )

        assert group.unique_statements == [
            ImportStatement("a", leafs=[ImportLeaf("b")])
        ]

    def test_merged_statements(self):
        group = BaseImportGroup(
            statements=[
                ImportStatement("a", leafs=[ImportLeaf("b")]),
                ImportStatement("a", leafs=[ImportLeaf("c")]),
                ImportStatement("b", leafs=[ImportLeaf("c")]),
            ]
        )

        assert sorted(group.merged_statements) == [
            ImportStatement("a", leafs=[ImportLeaf("b"), ImportLeaf("c")]),
            ImportStatement("b", leafs=[ImportLeaf("c")]),
        ]

    def test_merged_statements_leafless(self):
        group = BaseImportGroup(
            statements=[
                ImportStatement("a", leafs=[ImportLeaf("b")]),
                ImportStatement("a", leafs=[]),
                ImportStatement("b", leafs=[ImportLeaf("c")]),
            ]
        )

        assert sorted(group.merged_statements) == [
            ImportStatement("a", leafs=[]),
            ImportStatement("a", leafs=[ImportLeaf("b")]),
            ImportStatement("b", leafs=[ImportLeaf("c")]),
        ]

    def test_merged_statements_special(self):
        group = BaseImportGroup(
            statements=[
                ImportStatement("a", leafs=[ImportLeaf("*")]),
                ImportStatement("b", leafs=[ImportLeaf("c")]),
            ]
        )

        assert sorted(group.merged_statements) == [
            ImportStatement("a", leafs=[ImportLeaf("*")]),
            ImportStatement("b", leafs=[ImportLeaf("c")]),
        ]

    def test_all_line_numbers(self):
        s2 = ImportStatement("b", line_numbers=[2, 7])
        s1 = ImportStatement("a", line_numbers=[1, 2])

        group = BaseImportGroup(statements=[s1, s2])

        assert group.all_line_numbers() == [1, 2, 7]

    def test_add_statement_true(self):
        group = BaseImportGroup()
        group.add_statement(ImportStatement("add"))

        assert ImportStatement("add") in group.statements

    def test_add_statement_false(self):
        group = BaseImportGroup()
        group.add_statement(ImportStatement("ignore"))

        assert ImportStatement("ignore") not in group.statements

    def test_as_string(self):
        group = BaseImportGroup(
            statements=[ImportStatement("b"), ImportStatement("a")]
        )

        assert str(group.as_string()) == "import a\n" "import b"

    def test_as_string_with_artifacts(self):
        group = BaseImportGroup(
            file_artifacts={"sep": "\r\n"},
            statements=[ImportStatement("b"), ImportStatement("a")],
        )

        assert str(group.as_string()) == "import a\r\n" "import b"

    def test_formatted(self):
        group = BaseImportGroup(
            statements=[
                ImportStatement(
                    "b" * 80, leafs=[ImportLeaf("c"), ImportLeaf("d")]
                ),
                ImportStatement("a"),
            ]
        )

        assert group.formatted() == (
            "import a\n"
            + "from {} import (\n".format("b" * 80)
            + "    c,\n"
            + "    d,\n"
            + ")"
        )

    def test_formatted_with_artifacts(self):
        artifacts = {"sep": "\r\n"}
        group = BaseImportGroup(
            file_artifacts=artifacts,
            statements=[
                ImportStatement(
                    "b" * 80,
                    leafs=[ImportLeaf("c"), ImportLeaf("d")],
                    file_artifacts=artifacts,
                ),
                ImportStatement("a", file_artifacts=artifacts),
            ],
        )

        assert group.formatted() == (
            "import a\r\n"
            + "from {} import (\r\n".format("b" * 80)
            + "    c,\r\n"
            + "    d,\r\n"
            + ")"
        )


class TestSitePackagesGroup:
    group = SitePackagesGroup

    def test_should_add_statement(self):
        assert self.group().should_add_statement(ImportStatement("pytest.test"))
        assert not self.group().should_add_statement(ImportStatement("os.path"))


class TestStdLibGroup:
    group = StdLibGroup

    def test_should_add_statement(self):
        assert self.group().should_add_statement(ImportStatement("os.path"))
        assert not self.group().should_add_statement(
            ImportStatement("pytest.test")
        )


class TestPackagesGroup:
    group = PackagesGroup

    def test_should_add_statement(self):
        assert self.group({"packages": ["foo"]}).should_add_statement(
            ImportStatement("foo.bar")
        )
        assert not self.group({"packages": ["foo"]}).should_add_statement(
            ImportStatement("os.path")
        )


class TestLocalGroup:
    group = LocalGroup

    def test_should_add_statement(self):
        assert self.group().should_add_statement(ImportStatement(".foo.bar"))
        assert not self.group({"packages": ["foo"]}).should_add_statement(
            ImportStatement("os.path")
        )


class TestRemainderGroup:
    group = RemainderGroup

    def test_should_add_statement(self):
        assert self.group().should_add_statement(ImportStatement(".foo.bar"))


class TestImportGroups:
    def test_all_line_numbers(self):
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

    def test_add_group(self):
        with pytest.raises(ValueError):
            ImportGroups().add_group({})

        with pytest.raises(ValueError):
            ImportGroups().add_group({"type": "foo"})

        groups = ImportGroups()
        groups.add_group({"type": "stdlib"})

        assert len(groups) == 1
        assert isinstance(groups[0], StdLibGroup)

    def test_add_statement_to_group(self):
        groups = ImportGroups([LocalGroup()])

        with pytest.raises(ValueError):
            groups.add_statement_to_group(ImportStatement("a"))

        groups.add_statement_to_group(ImportStatement(".a"))

        assert groups[0].statements == [ImportStatement(".a")]

    def test_add_statement_to_group_priority(self):
        groups = ImportGroups([RemainderGroup(), LocalGroup()])
        groups.add_statement_to_group(ImportStatement(".a"))

        assert groups[0].statements == []
        assert groups[1].statements == [ImportStatement(".a")]

    def test_as_string(self):
        assert str(ImportGroups().as_string()) == ""

    def test_formatted_empty(self):
        assert ImportGroups().formatted() == ""

    def test_formatted_with_artifacts(self):
        artifacts = {"sep": "\r\n"}

        groups = ImportGroups(
            [
                RemainderGroup(file_artifacts=artifacts),
                LocalGroup(file_artifacts=artifacts),
            ],
            file_artifacts=artifacts,
        )

        groups.add_statement_to_group(
            ImportStatement(".a", file_artifacts=artifacts)
        )
        groups.add_statement_to_group(
            ImportStatement("foo", file_artifacts=artifacts)
        )

        assert groups.formatted() == "import foo\r\n" "\r\n" "import .a"
