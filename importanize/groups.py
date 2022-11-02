# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
import abc
import itertools
import typing
from collections import OrderedDict, defaultdict
from functools import reduce

from .parser import Artifacts
from .plugins import plugin_hooks
from .statements import ImportStatement
from .utils import is_site_package, is_std_lib


if typing.TYPE_CHECKING:
    from .config import Config, GroupConfig


class BaseImportGroup(metaclass=abc.ABCMeta):
    name: str
    priority: int

    def __init__(
        self,
        statements: typing.List[ImportStatement] = None,
        group_config: "GroupConfig" = None,
        config: "Config" = None,
        artifacts: Artifacts = None,
    ):
        # avoid circular imports
        from .config import Config, GroupConfig

        self.statements = statements or []
        self.group_config = group_config or GroupConfig.default()
        self.config = config or Config.default()
        self.artifacts = artifacts or Artifacts.default()

    @classmethod
    def validate_group_config(cls, group: "GroupConfig") -> "GroupConfig":
        """
        Validate configuration hook
        """
        return group

    @property
    def unique_statements(self) -> typing.List[ImportStatement]:
        try:
            return self._unique_statements
        except AttributeError:
            self._unique_statements: typing.List[ImportStatement] = sorted(
                list(set(self.merged_statements))
            )
            return self._unique_statements

    @property
    def merged_statements(self) -> typing.List[ImportStatement]:
        """
        Merge statements with the same import stems
        """
        leafless_counter: typing.Dict[str, typing.List[ImportStatement]] = defaultdict(
            list
        )
        counter: typing.Dict[str, typing.List[ImportStatement]] = defaultdict(list)
        for statement in self.statements:
            if statement.leafs:
                counter[statement.stem].append(statement)
            else:
                leafless_counter[statement.stem].append(statement)

        merged_statements = list(
            filter(
                lambda s: not any(
                    j is False
                    for j in plugin_hooks.should_include_statement(
                        group=self, statement=s
                    )
                ),
                itertools.chain(
                    *leafless_counter.values(),
                ),
            )
        )

        def filter_leafs(statement: ImportStatement) -> ImportStatement:
            statement.leafs = list(
                filter(
                    lambda l: not any(
                        j is False
                        for j in plugin_hooks.should_include_leaf(
                            group=self, statement=statement, leaf=l
                        )
                    ),
                    statement.leafs,
                )
            )
            return statement

        def merge(
            statements: typing.List[ImportStatement],
        ) -> typing.List[ImportStatement]:
            _special = []
            _standard = []
            _statements = []

            for i in statements:
                if i.leafs and i.leafs[0].name == "*":
                    _special.append(i)
                else:
                    _statements.append(i)

            if _statements:
                merged = filter_leafs(reduce(lambda a, b: a + b, _statements))
                if merged.leafs:
                    _standard.append(merged)

            return _special + _standard

        for statements in counter.values():
            merged_statements.extend(merge(statements))

        return merged_statements

    def all_line_numbers(self) -> typing.List[int]:
        return sorted(set(itertools.chain(*[i.line_numbers for i in self.statements])))

    @abc.abstractmethod
    def should_add_statement(self, statement: ImportStatement) -> bool:
        """Subclass must implement"""

    def add_statement(self, statement: ImportStatement) -> bool:
        if self.should_add_statement(statement):
            self.statements.append(statement)
            return True
        return False

    def as_string(self) -> str:
        return self.artifacts.sep.join([i.as_string() for i in self.unique_statements])

    def formatted(self) -> str:
        lines: typing.List[str] = []

        for i, statement in enumerate(self.unique_statements):
            lines += filter(
                lambda x: x is not None,
                plugin_hooks.group_prepend_to_statement(
                    group=self, index=i, statement=statement
                ),
            )
            lines.append(
                self.config.formatter(
                    statement, config=self.config, artifacts=self.artifacts
                ).format()
            )
            lines += filter(
                lambda x: x is not None,
                plugin_hooks.group_append_to_statement(
                    group=self, index=i, statement=statement
                ),
            )

        return self.artifacts.sep.join(lines)

    def __str__(self) -> str:
        return self.as_string()

    def __bool__(self) -> bool:
        return bool(self.unique_statements)


class StdLibGroup(BaseImportGroup):
    name: str = "stdlib"
    priority: int = 0

    def should_add_statement(self, statement: ImportStatement) -> bool:
        return is_std_lib(statement.root_module)


class SitePackagesGroup(BaseImportGroup):
    name: str = "sitepackages"
    priority: int = 2

    def should_add_statement(self, statement: ImportStatement) -> bool:
        return is_site_package(statement.root_module)


class PackagesGroup(BaseImportGroup):
    name: str = "packages"
    priority: int = 1

    @classmethod
    def validate_group_config(cls, group: "GroupConfig") -> "GroupConfig":
        if not group.packages:
            msg = f'"{cls.name}" config group must define at least one Python package'
            raise ValueError(msg)
        return super().validate_group_config(group)

    def should_add_statement(self, statement: ImportStatement) -> bool:
        return statement.root_module in self.group_config.packages


class LocalGroup(BaseImportGroup):
    name: str = "local"
    priority: int = 3

    def should_add_statement(self, statement: ImportStatement) -> bool:
        return statement.stem.startswith(".")


class RemainderGroup(BaseImportGroup):
    name: str = "remainder"
    priority: int = 4

    def should_add_statement(self, statement: ImportStatement) -> bool:
        return True


# -- RemainderGroup goes last and catches everything left over
GROUPS: typing.Dict[str, typing.Type[BaseImportGroup]] = OrderedDict(
    sorted(
        (
            (i.name, i)
            for i in list(globals().values()) + plugin_hooks.register_import_group()
            if (
                isinstance(i, type)
                and i is not BaseImportGroup
                and issubclass(i, BaseImportGroup)
            )
        ),
        key=lambda i: i[1].priority,
    )
)


class ImportGroups:
    def __init__(
        self,
        groups: typing.List[BaseImportGroup] = None,
        config: "Config" = None,
        artifacts: Artifacts = None,
    ):
        # avoid circular imports
        from .config import Config

        self.groups = groups or []
        self.config = config or Config.default()
        self.artifacts = artifacts or Artifacts.default()

    @classmethod
    def from_config(
        cls,
        config: "Config",
        artifacts: Artifacts = None,
        statements: typing.List[ImportStatement] = None,
    ) -> "ImportGroups":
        artifacts = artifacts or Artifacts.default()
        statements = statements or []

        groups = [
            GROUPS[g.type](group_config=g, config=config, artifacts=artifacts)
            for g in config.groups
        ]

        import_groups = cls(groups=groups, config=config, artifacts=artifacts)
        [import_groups.add_statement(s) for s in statements]
        [import_groups.add_statement(s) for s in config.add_imports]
        return import_groups

    def all_line_numbers(self) -> typing.List[int]:
        return sorted(
            set(itertools.chain(*[i.all_line_numbers() for i in self.groups]))
        )

    @property
    def sorted_groups(self) -> typing.List[BaseImportGroup]:
        return sorted(self.groups, key=lambda i: list(GROUPS.values()).index(type(i)))

    def add_statement(self, statement: ImportStatement) -> bool:
        for group in self.sorted_groups:
            if group.add_statement(statement):
                return True

        msg = (
            "Import statement was not added into "
            "any of the import groups. "
            "Perhaps you can consider adding "
            '"remaining" import group which will '
            "catch all remaining import statements."
        )
        raise ValueError(msg)

    def as_string(self) -> str:
        sep = self.artifacts.sep * 2
        return sep.join(i.as_string() for i in self.groups if i)

    def formatted(self) -> str:
        sep = self.artifacts.sep * 2
        return sep.join(i.formatted() for i in self.groups if i)

    def __str__(self) -> str:
        return self.as_string()
