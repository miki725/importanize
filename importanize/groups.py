# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
import itertools
import operator
from collections import OrderedDict, defaultdict
from functools import reduce

import six

from .formatters import DEFAULT_FORMATTER
from .utils import is_site_package, is_std_lib


@six.python_2_unicode_compatible
class BaseImportGroup(object):
    def __init__(self, config=None, **kwargs):
        self.config = config or {}

        self.statements = []
        self.file_artifacts = kwargs.get('file_artifacts', {})

    @property
    def unique_statements(self):
        return sorted(list(set(self.merged_statements)))

    @property
    def merged_statements(self):
        """
        Merge statements with the same import stems
        """
        leafless_counter = defaultdict(list)
        counter = defaultdict(list)
        for statement in self.statements:
            if statement.leafs:
                counter[statement.stem].append(statement)
            else:
                leafless_counter[statement.stem].append(statement)

        merged_statements = list(itertools.chain(*leafless_counter.values()))

        def merge(statements):
            _special = []
            _statements = []

            for i in statements:
                if i.leafs and i.leafs[0].name == '*':
                    _special.append(i)
                else:
                    _statements.append(i)

            _reduced = []
            if _statements:
                _reduced = [reduce(lambda a, b: a + b, _statements)]

            return _special + _reduced

        for statements in counter.values():
            merged_statements.extend(merge(statements))

        return merged_statements

    def all_line_numbers(self):
        return sorted(list(set(list(
            itertools.chain(*map(operator.attrgetter('line_numbers'),
                                 self.statements))
        ))))

    def should_add_statement(self, statement):
        raise NotImplementedError

    def add_statement(self, statement):
        if self.should_add_statement(statement):
            self.statements.append(statement)
            return True
        return False

    def as_string(self):
        sep = self.file_artifacts.get('sep', '\n')
        return sep.join(map(operator.methodcaller('as_string'),
                            self.unique_statements))

    def formatted(self, formatter=DEFAULT_FORMATTER):
        sep = self.file_artifacts.get('sep', '\n')
        return sep.join(map(operator.methodcaller('formatted',
                                                  formatter=formatter),
                            self.unique_statements))

    def __str__(self):
        return self.as_string()


class StdLibGroup(BaseImportGroup):
    def should_add_statement(self, statement):
        return is_std_lib(statement.root_module)


class SitePackagesGroup(BaseImportGroup):
    def should_add_statement(self, statement):
        return is_site_package(statement.root_module)


class PackagesGroup(BaseImportGroup):
    def __init__(self, *args, **kwargs):
        super(PackagesGroup, self).__init__(*args, **kwargs)

        if 'packages' not in self.config:
            msg = ('"package" config must be supplied '
                   'for packages import group')
            raise ValueError(msg)

    def should_add_statement(self, statement):
        return statement.root_module in self.config.get('packages', [])


class LocalGroup(BaseImportGroup):
    def should_add_statement(self, statement):
        return statement.stem.startswith('.')


class RemainderGroup(BaseImportGroup):
    def should_add_statement(self, statement):
        return True


# -- RemainderGroup goes last and catches everything left over
GROUP_MAPPING = OrderedDict((
    ('stdlib', StdLibGroup),
    ('sitepackages', SitePackagesGroup),
    ('packages', PackagesGroup),
    ('local', LocalGroup),
    ('remainder', RemainderGroup),
))


@six.python_2_unicode_compatible
class ImportGroups(object):
    def __init__(self, **kwargs):
        self.groups = []
        self.file_artifacts = kwargs.get('file_artifacts', {})

    def all_line_numbers(self):
        return sorted(list(set(list(
            itertools.chain(*map(operator.methodcaller('all_line_numbers'),
                                 self.groups))
        ))))

    def add_group(self, config):
        if 'type' not in config:
            msg = ('"type" must be specified in '
                   'import group config')
            raise ValueError(msg)

        if config['type'] not in GROUP_MAPPING:
            msg = ('"{}" is not supported import group'.format(config['type']))
            raise ValueError(msg)

        self.groups.append(GROUP_MAPPING[config['type']](config))

    def add_statement_to_group(self, statement):
        groups_by_priority = sorted(
            self.groups,
            key=lambda i: list(GROUP_MAPPING.values()).index(type(i))
        )

        added = False

        for group in groups_by_priority:
            if group.add_statement(statement):
                added = True
                break

        if not added:
            msg = ('Import statement was not added into '
                   'any of the import groups. '
                   'Perhaps you can consider adding '
                   '"remaining" import group which will '
                   'catch all remaining import statements.')
            raise ValueError(msg)

    def as_string(self):
        sep = self.file_artifacts.get('sep', '\n') * 2
        return sep.join(filter(
            None, map(operator.methodcaller('as_string'),
                      self.groups)
        ))

    def formatted(self, formatter=DEFAULT_FORMATTER):
        sep = self.file_artifacts.get('sep', '\n') * 2
        return sep.join(filter(
            None, map(operator.methodcaller('formatted',
                                            formatter=formatter),
                      self.groups)
        ))

    def __str__(self):
        return self.as_string()
