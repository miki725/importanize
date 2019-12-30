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
    enabled_by_default: bool
    enabled_for_pipes: bool

    def register_import_group(self) -> "BaseImportGroup":
        """
        """

    def statement_gt_overwrite(
        self, a: "ImportStatement", b: "ImportStatement", result: bool
    ) -> typing.Optional[bool]:
        """
        """

    def group_prepend_to_statement(
        self, group: "BaseImportGroup", index: int, statement: "ImportStatement"
    ) -> str:
        """
        """

    def group_append_to_statement(
        self, group: "BaseImportGroup", index: int, statement: "ImportStatement"
    ) -> str:
        """
        """

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
    def register_import_group(self) -> typing.List["BaseImportGroup"]:
        """
        """

    @hookspec
    def statement_gt_overwrite(
        self, a: "ImportStatement", b: "ImportStatement", result: bool
    ) -> typing.List[typing.Optional[bool]]:
        """
        """

    @hookspec
    def inject_tree_artifacts(
        self, artifacts: "Artifacts", tree: lib2to3.pytree.Node, text: str
    ) -> typing.List["Artifacts"]:
        """
        """

    @hookspec
    def group_prepend_to_statement(
        self, group: "BaseImportGroup", index: int, statement: "ImportStatement"
    ) -> typing.List[str]:
        """
        """

    @hookspec
    def group_append_to_statement(
        self, group: "BaseImportGroup", index: int, statement: "ImportStatement"
    ) -> typing.List[str]:
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


ALL_PLUGINS: typing.Dict[str, ImportanizePlugin] = dict(
    plugin_manager.list_name_plugin()
)
INSTALLED_PLUGIN_NAMES: typing.List[str] = list(ALL_PLUGINS)
DEFAULT_PLUGIN_NAMES = [
    name
    for name, plugin in ALL_PLUGINS.items()
    if getattr(plugin, "enabled_by_default", False)
]
NOT_PIPED_PLUGIN_NAMES = [
    name
    for name, plugin in ALL_PLUGINS.items()
    if not getattr(plugin, "enabled_for_pipes", True)
]


def deactivate_plugin(name: str) -> None:
    with suppress(Exception):
        plugin_manager.unregister(name=name, plugin=ALL_PLUGINS[name])


def activate_plugin(name: str) -> None:
    with suppress(Exception):
        plugin_manager.register(name=name, plugin=ALL_PLUGINS[name])


def deactivate_all_plugins() -> None:
    for name, _plugin in plugin_manager.list_name_plugin():
        deactivate_plugin(name)


def ensure_activated_plugins(names: typing.Iterable[str]) -> None:
    activated_plugins = set(dict(plugin_manager.list_name_plugin()))

    to_deactivate = activated_plugins - set(names)
    to_activate = set(names) - activated_plugins

    list(map(deactivate_plugin, to_deactivate))
    list(map(activate_plugin, to_activate))


def deactivate_piped_plugins() -> None:
    list(map(deactivate_plugin, NOT_PIPED_PLUGIN_NAMES))


ensure_activated_plugins(DEFAULT_PLUGIN_NAMES)
