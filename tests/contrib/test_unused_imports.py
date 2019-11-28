# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
import typing

from importanize.contrib.unused_imports import (
    UnsusedImportsArtifacts,
    UnusedImportsPlugin,
)
from importanize.groups import RemainderGroup
from importanize.parser import Artifacts, parse_to_tree
from importanize.statements import ImportLeaf, ImportStatement


class TestUnusedImportsPlugin:
    def test_inject_tree_artifacts(self) -> None:
        text = "\n".join(
            [
                "import os",
                "from contextlib import suppress",
                "from itertools import chain, count",
                "chain",
            ]
        )
        artifacts = UnusedImportsPlugin().inject_tree_artifacts(
            Artifacts.default(), parse_to_tree(text), text
        )

        assert typing.cast(UnsusedImportsArtifacts, artifacts).unused_imports == [
            "os",
            "contextlib.suppress",
            "itertools.count",
        ]

    def test_should_include_statement(self) -> None:
        plugin = UnusedImportsPlugin()
        artifacts = Artifacts.default()
        typing.cast(UnsusedImportsArtifacts, artifacts).unused_imports = [
            "os",
            "sys as system",
        ]

        assert plugin.should_include_statement(
            RemainderGroup(artifacts=artifacts),
            ImportStatement("os", inline_comments=["noqa"]),
        )
        assert not plugin.should_include_statement(
            RemainderGroup(artifacts=artifacts), ImportStatement("os")
        )
        assert plugin.should_include_statement(
            RemainderGroup(artifacts=artifacts), ImportStatement("sys")
        )
        assert not plugin.should_include_statement(
            RemainderGroup(artifacts=artifacts),
            ImportStatement("sys", as_name="system"),
        )

    def test_should_include_leaf(self) -> None:
        plugin = UnusedImportsPlugin()
        artifacts = Artifacts.default()
        typing.cast(UnsusedImportsArtifacts, artifacts).unused_imports = [
            "os",
            "itertools.chain as ichain",
        ]

        assert plugin.should_include_leaf(
            RemainderGroup(artifacts=artifacts),
            ImportStatement("os", leafs=[ImportLeaf("path")], inline_comments=["noqa"]),
            ImportLeaf("path"),
        )
        assert plugin.should_include_leaf(
            RemainderGroup(artifacts=artifacts),
            ImportStatement(
                "os", leafs=[ImportLeaf("path", statement_comments=["noqa"])]
            ),
            ImportLeaf("path", statement_comments=["noqa"]),
        )
        assert not plugin.should_include_leaf(
            RemainderGroup(artifacts=artifacts),
            ImportStatement("os", leafs=[ImportLeaf("path")]),
            ImportLeaf("path"),
        )
        assert plugin.should_include_leaf(
            RemainderGroup(artifacts=artifacts),
            ImportStatement("itertools", leafs=[ImportLeaf("chain")]),
            ImportLeaf("chain"),
        )
        assert not plugin.should_include_leaf(
            RemainderGroup(artifacts=artifacts),
            ImportStatement("itertools", leafs=[ImportLeaf("chain", as_name="ichain")]),
            ImportLeaf("chain", as_name="ichain"),
        )
