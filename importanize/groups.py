# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
import itertools
import operator
from collections import OrderedDict

from future.utils import python_2_unicode_compatible

from .utils import is_std_lib


@python_2_unicode_compatible
class BaseImportGroup(object):
    def __init__(self, config=None):
        self.config = config or {}

        self.statements = []

    @property
    def unique_statements(self):
        return sorted(list(set(self.statements)))

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
        return '\n'.join(map(operator.methodcaller('as_string'),
                             self.unique_statements))

    def formatted(self):
        return '\n'.join(map(operator.methodcaller('formatted'),
                             self.unique_statements))

    def __str__(self):
        return self.as_string()


class StdLibGroup(BaseImportGroup):
    def should_add_statement(self, statement):
        return is_std_lib(statement.root_module)


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


GROUP_MAPPING = OrderedDict((
    ('stdlib', StdLibGroup),
    ('packages', PackagesGroup),
    ('local', LocalGroup),
    ('remainder', RemainderGroup),
))


@python_2_unicode_compatible
class ImportGroups(object):
    def __init__(self):
        self.groups = []

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
            msg = ('"{}" is not supported import group')
            raise ValueError(msg)

        self.groups.append(GROUP_MAPPING[config['type']](config))

    def add_statement_to_group(self, statement):
        priority = lambda i: list(GROUP_MAPPING.values()).index(type(i))
        groups_by_priority = sorted(self.groups, key=priority)

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
        return '\n\n'.join(filter(
            None, map(operator.methodcaller('as_string'),
                      self.groups)
        ))

    def formatted(self):
        return '\n\n'.join(filter(
            None, map(operator.methodcaller('formatted'),
                      self.groups)
        ))

    def __str__(self):
        return self.as_string()
