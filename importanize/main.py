# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function
import argparse
import json
import operator
import os
import six

from .parser import find_imports_from_lines, parse_statements
from .groups import ImportGroups
from .utils import read


IMPORTANIZE_CONFIG = '.importanizerc'
PEP8_CONFIG = {
    'groups': [
        {
            'type': 'stdlib',
        },
        {
            'type': 'remainder',
        },
        {
            'type': 'local',
        }
    ],
}

pwd = os.getcwd()
default_config = None
if os.path.exists(os.path.join(pwd, IMPORTANIZE_CONFIG)):
    default_config = IMPORTANIZE_CONFIG

parser = argparse.ArgumentParser(
    description='Utility for organizing Python imports '
                'using PEP8 or custom rules',
)
parser.add_argument(
    'path',
    type=six.text_type,
    nargs='?',
    default='.',
    help='Path either to a file or directory where '
         'all Python import will be organized. ',
)
parser.add_argument(
    '-c', '--config',
    type=six.text_type,
    default=default_config,
    help='Path to importanize config json file. '
         'If importanize.json is present, that config '
         'will be used. Otherwise crude default pep8 '
         'config will be used.',
)


def run(path, config):
    text = read(path)

    lines_iterator = enumerate(iter(text.splitlines()))
    imports = list(parse_statements(find_imports_from_lines(lines_iterator)))

    groups = ImportGroups()
    for c in config['groups']:
        groups.add_group(c)

    for i in imports:
        groups.add_statement_to_group(i)

    formatted_imports = groups.formatted()
    line_numbers = groups.all_line_numbers()

    lines = text.splitlines()
    for line_number in sorted(groups.all_line_numbers(), reverse=True):
        lines.pop(line_number)

    first_import_line_number = min(line_numbers)
    i = first_import_line_number

    while i:
        if not lines[i]:
            lines.pop(i)
        else:
            i = None

    lines = (lines[:first_import_line_number]
             + formatted_imports.splitlines()
             + [''] * 2
             + lines[first_import_line_number:])

    print('\n'.join(lines))


def main():
    args = parser.parse_args()

    path = os.path.abspath(args.path)
    if args.config is None:
        config = PEP8_CONFIG
    else:
        config = json.loads(read(args.config))

    if not os.path.isdir(path):
        run(path, config)

    else:
        for dirpath, dirnames, filenames in os.walk(path):
            python_files = filter(
                operator.methodcaller('endswith', '.py'),
                filenames
            )
            for file in python_files:
                path = os.path.join(dirpath, file)
                print('=' * len(path))
                print(path)
                print('-' * len(path))
                run(path, config)
