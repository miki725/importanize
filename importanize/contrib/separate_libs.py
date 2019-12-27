# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
import logging
import typing

import importanize

from ..plugins import ImportanizePlugin, hookimpl


log = logging.getLogger(__name__)


if typing.TYPE_CHECKING:
    from ..groups import BaseImportGroup
    from ..statements import ImportStatement


class SeparateLibsPlugin(ImportanizePlugin):
    version = importanize.__version__
    enabled_by_default = False
    enabled_for_pipes = True

    @hookimpl
    def statement_gt_overwrite(
        self, a: "ImportStatement", b: "ImportStatement", result: bool
    ) -> typing.Optional[bool]:
        self_len = len(a.leafs)
        other_len = len(b.leafs)
        if any([not self_len and other_len, self_len and not other_len]):
            if a.root_module == b.root_module:
                return a._gt(b)
            else:
                return a.full_stem > b.full_stem
        return None

    @hookimpl
    def group_append_to_statement(
        self, group: "BaseImportGroup", index: int, statement: "ImportStatement"
    ) -> typing.Optional[str]:
        if group.name == "stdlib" and statement.root_module != "__future__":
            return None

        try:
            next_statement = group.unique_statements[index + 1]
        except IndexError:
            return None

        if next_statement.root_module == statement.root_module:
            return None

        return ""


plugin = SeparateLibsPlugin()
