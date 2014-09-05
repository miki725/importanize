# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function
import sys

from .parser import find_imports_from_lines, parse_statements
from .groups import ImportGroups


def main():
    path = sys.argv[1]
    text = open(path, 'rb').read().decode('utf-8')

    lines_iterator = enumerate(iter(text.splitlines()))
    imports = list(parse_statements(find_imports_from_lines(lines_iterator)))

    config = [
        {
            'type': 'stdlib',
        },
        {
            'type': 'remainder',
        },
        {
            'type': 'local',
        }
    ]
    groups = ImportGroups()
    for c in config:
        groups.add_group(c)

    for i in imports:
        groups.add_statement_to_group(i)

    print(groups.as_string())
