# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from importanize.contrib.unused_imports import UnusedImportsPlugin
from importanize.plugins import deactivate_all_plugins, plugin_manager


def test_plugins() -> None:
    plugin_manager.register(UnusedImportsPlugin())

    assert plugin_manager.list_name_plugin()

    deactivate_all_plugins()

    assert not plugin_manager.list_name_plugin()
