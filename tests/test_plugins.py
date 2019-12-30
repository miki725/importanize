# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from importanize.plugins import (
    activate_plugin,
    deactivate_all_plugins,
    deactivate_piped_plugins,
    plugin_manager,
)


def test_plugins() -> None:
    activate_plugin("unused_imports")
    activate_plugin("separate_libs")

    assert len(plugin_manager.list_name_plugin()) == 2

    deactivate_piped_plugins()

    assert len(plugin_manager.list_name_plugin()) == 1

    deactivate_all_plugins()

    assert not plugin_manager.list_name_plugin()
