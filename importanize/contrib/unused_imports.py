# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
import ast
import lib2to3.pytree
import logging
import typing
from dataclasses import dataclass

import pyflakes.checker  # type: ignore
import pyflakes.messages  # type: ignore

import importanize

from ..plugins import ImportanizePlugin, hookimpl


log = logging.getLogger(__name__)


if typing.TYPE_CHECKING:
    from ..parser import Artifacts
    from ..groups import BaseImportGroup
    from ..statements import ImportStatement, ImportLeaf


@dataclass
class UnsusedImportsArtifacts:
    unused_imports: typing.Iterable[str] = ()


class UnusedImportsPlugin(ImportanizePlugin):
    version = importanize.__version__

    @hookimpl
    def inject_tree_artifacts(
        self, artifacts: "Artifacts", tree: lib2to3.pytree.Node, text: str
    ) -> "Artifacts":
        a = typing.cast(UnsusedImportsArtifacts, artifacts)

        a.unused_imports = []

        ast_tree = ast.parse(text)
        warnings = pyflakes.checker.Checker(ast_tree)
        unused_imports = [
            i
            for i in warnings.messages
            if isinstance(i, pyflakes.messages.UnusedImport)
        ]
        for i in unused_imports:
            a.unused_imports.append(i.message_args[0])

        return typing.cast("Artifacts", a)

    @hookimpl
    def should_include_statement(
        self, group: "BaseImportGroup", statement: "ImportStatement"
    ) -> bool:
        if any("noqa" in i for i in statement.inline_comments):
            return True

        return self._should_include_str(group, statement.full_stem)

    @hookimpl
    def should_include_leaf(
        self, group: "BaseImportGroup", statement: "ImportStatement", leaf: "ImportLeaf"
    ) -> bool:
        if any(
            [
                any("noqa" in i for i in statement.inline_comments),
                any("noqa" in i for i in leaf.statement_comments),
            ]
        ):
            return True

        sep = "" if statement.stem.endswith(".") else "."
        return self._should_include_str(group, f"{statement.stem}{sep}{leaf.full_name}")

    def _should_include_str(self, group: "BaseImportGroup", data: str) -> bool:
        components = data.split(" as ")[-1].split(".")
        possibilities = (
            [data]
            if " as " in data
            else [".".join(components[:i]) for i in range(len(components), 0, -1)]
        )

        for p in possibilities:
            if p in getattr(group.artifacts, "unused_imports", []):
                log.debug(f"Removing {data!r} as it is unused")
                return False

        return True


plugin = UnusedImportsPlugin()
