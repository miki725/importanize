# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
import argparse
import json
import operator
import os

import six

from .groups import ImportGroups
from .parser import find_imports_from_lines, parse_statements
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
parser.add_argument(
    '--print',
    action='store_true',
    default=False,
    help='If provided, instead of changing files, modified '
         'files will be printed to stdout.'
)


def run(path, config, args):
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

    first_import_line_number = min(line_numbers) if line_numbers else 0
    i = first_import_line_number

    while i and len(lines) > i:
        if not lines[i]:
            lines.pop(i)
        else:
            i = None

    lines = (lines[:first_import_line_number]
             + formatted_imports.splitlines()
             + ([''] * 2 if lines[first_import_line_number:] else [])
             + lines[first_import_line_number:]
             + [''])

    lines = '\n'.join(lines)

    if args.print:
        print(lines)
    else:
        with open(path, 'wb') as fid:
            fid.write(lines.encode('utf-8'))


def main():
    args = parser.parse_args()

    path = os.path.abspath(args.path)
    if args.config is None:
        config = PEP8_CONFIG
    else:
        config = json.loads(read(args.config))

    if not os.path.isdir(path):
        try:
            run(path, config, args)
        except Exception as e:
            parser.error(e.message)

    else:
        for dirpath, dirnames, filenames in os.walk(path):
            python_files = filter(
                operator.methodcaller('endswith', '.py'),
                filenames
            )
            for file in python_files:
                path = os.path.join(dirpath, file)
                if args.print:
                    print('=' * len(path))
                    print(path)
                    print('-' * len(path))
                try:
                    run(path, config, args)
                except Exception as e:
                    msg = '{} - {}'.format(path, e.message)
                    parser.error(msg)
