# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
import lib2to3.pytree
import typing
from contextlib import suppress

import pluggy  # type: ignore


if typing.TYPE_CHECKING:
    from .groups import BaseImportGroup
    from .parser import Artifacts
    from .statements import ImportStatement, ImportLeaf


F = typing.TypeVar("F")
hookspec = typing.cast(typing.Callable[[F], F], pluggy.HookspecMarker("importanize"))
hookimpl = typing.cast(typing.Callable[[F], F], pluggy.HookimplMarker("importanize"))


class ImportanizePlugin:
    version: str

    def inject_tree_artifacts(
        self, artifacts: "Artifacts", tree: lib2to3.pytree.Node, text: str
    ) -> "Artifacts":
        """
        """

    def should_include_statement(
        self, group: "BaseImportGroup", statement: "ImportStatement"
    ) -> bool:
        """
        """

    def should_include_leaf(
        self, group: "BaseImportGroup", statement: "ImportStatement", leaf: "ImportLeaf"
    ) -> bool:
        """
        """


class ImportanizeSpec:
    @hookspec
    def inject_tree_artifacts(
        self, artifacts: "Artifacts", tree: lib2to3.pytree.Node, text: str
    ) -> typing.List["Artifacts"]:
        """
        """

    @hookspec
    def should_include_statement(
        self, group: "BaseImportGroup", statement: "ImportStatement"
    ) -> typing.List[bool]:
        """
        """

    @hookspec
    def should_include_leaf(
        self, group: "BaseImportGroup", statement: "ImportStatement", leaf: "ImportLeaf"
    ) -> typing.List[bool]:
        """
        """


plugin_manager = pluggy.PluginManager("importanize")
plugin_manager.add_hookspecs(ImportanizeSpec)
plugin_hooks = plugin_manager.hook = typing.cast(ImportanizeSpec, plugin_manager.hook)


with suppress(Exception):
    plugin_manager.load_setuptools_entrypoints("importanize")

PLUGINS: typing.Dict[str, ImportanizePlugin] = dict(plugin_manager.list_name_plugin())
INSTALLED_PLUGINS: typing.List[str] = list(PLUGINS)


def deactivate_all_plugins() -> None:
    for name, plugin in plugin_manager.list_name_plugin():
        plugin_manager.unregister(name=name, plugin=plugin)
