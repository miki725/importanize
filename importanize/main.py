# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
import argparse
import inspect
import json
import logging
import operator
import os
import sys
from fnmatch import fnmatch

import six

from . import __description__, __version__, formatters
from .formatters import DEFAULT_FORMATTER
from .groups import ImportGroups
from .parser import (
    find_imports_from_lines,
    get_file_artifacts,
    parse_statements,
)
from .utils import read


LOGGING_FORMAT = '%(levelname)s %(name)s %(message)s'
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
VERBOSITY_MAPPING = {
    0: logging.ERROR,
    1: logging.INFO,
    2: logging.DEBUG,
}

# initialize FORMATTERS dict
FORMATTERS = {
    formatter.name: formatter
    for formatter in vars(formatters).values()
    if (inspect.isclass(formatter)
        and formatter is not formatters.Formatter
        and issubclass(formatter, formatters.Formatter))
}

# setup logging
logging.basicConfig(format=LOGGING_FORMAT)
logging.getLogger('').setLevel(logging.ERROR)
log = logging.getLogger(__name__)


def find_config():
    path = os.getcwd()
    default_config = None
    found_default = ''

    while path != os.sep:
        config_path = os.path.join(path, IMPORTANIZE_CONFIG)
        if os.path.exists(config_path):
            default_config = config_path
            found_default = (' Found configuration file at {}'
                             ''.format(default_config))
            break
        else:
            path = os.path.dirname(path)

    return default_config, found_default


default_config, found_default = find_config()

parser = argparse.ArgumentParser(
    description=__description__,
)
parser.add_argument(
    'path',
    type=six.text_type,
    nargs='*',
    default=['.'],
    help='Path either to a file or directory where '
         'all Python files imports will be organized.',
)
parser.add_argument(
    '-c', '--config',
    type=six.text_type,
    default=default_config,
    help='Path to importanize config json file. '
         'If "{}" is present in either current folder '
         'or any parent folder, that config '
         'will be used. Otherwise crude default pep8 '
         'config will be used.{}'
         ''.format(IMPORTANIZE_CONFIG,
                   found_default),
)
parser.add_argument(
    '-f', '--formatter',
    type=six.text_type,
    default=DEFAULT_FORMATTER,
    choices=sorted(FORMATTERS.keys()),
    help='Formatter used.'
)
parser.add_argument(
    '--print',
    action='store_true',
    default=False,
    help='If provided, instead of changing files, modified '
         'files will be printed to stdout.'
)
parser.add_argument(
    '--version',
    action='store_true',
    default=False,
    help='Show the version number of importanize'
)
parser.add_argument(
    '-v', '--verbose',
    action='count',
    default=0,
    help='Print out fascinated debugging information. '
         'Can be supplied multiple times to increase verbosity level',
)


def run_importanize(path, config, args):
    if config.get('exclude'):
        if any(map(lambda i: fnmatch(path, i), config.get('exclude'))):
            log.info('Skipping {}'.format(path))
            return False

    text = read(path)
    file_artifacts = get_file_artifacts(path)

    # Get formatter from args or config
    formatter = FORMATTERS.get(args.formatter or config.get('formatter'),
                               DEFAULT_FORMATTER)
    log.debug('Using {} formatter'.format(formatter))

    lines_iterator = enumerate(iter(text.splitlines()))
    imports = list(parse_statements(find_imports_from_lines(lines_iterator)))

    groups = ImportGroups()

    for c in config['groups']:
        groups.add_group(c)

    for i in imports:
        groups.add_statement_to_group(i)

    formatted_imports = groups.formatted(formatter=formatter)
    line_numbers = groups.all_line_numbers()

    lines = text.splitlines()
    for line_number in sorted(groups.all_line_numbers(), reverse=True):
        lines.pop(line_number)

    first_import_line_number = min(line_numbers) if line_numbers else 0
    i = first_import_line_number

    while i is not None and len(lines) > i:
        if not lines[i]:
            lines.pop(i)
        else:
            i = None

    lines = (lines[:first_import_line_number]
             + formatted_imports.splitlines()
             + ([''] * 2
                if lines[first_import_line_number:] and formatted_imports
                else [])
             + lines[first_import_line_number:]
             + [''])

    lines = file_artifacts.get('sep', '\n').join(lines)

    if args.print:
        print(lines.encode('utf-8') if not six.PY3 else lines)
    else:
        with open(path, 'wb') as fid:
            fid.write(lines.encode('utf-8'))

    log.info('Successfully importanized {}'.format(path))
    return True


def run(path, config, args):
    if not os.path.isdir(path):
        try:
            run_importanize(path, config, args)
        except Exception as e:
            log.exception('Error running importanize for {}'
                          ''.format(path))
            parser.error(six.text_type(e))

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
                    run_importanize(path, config, args)
                except Exception as e:
                    log.exception('Error running importanize for {}'
                                  ''.format(path))
                    parser.error(six.text_type(e))


def main():
    args = parser.parse_args()

    # adjust logging level
    (logging.getLogger('')
     .setLevel(VERBOSITY_MAPPING.get(args.verbose, 0)))

    log.debug('Running importanize with {}'.format(args))

    if args.version:
        msg = (
            'importanize\n'
            '===========\n'
            '{}\n\n'
            'version: {}\n'
            'python: {}\n'
            'source: https://github.com/miki725/importanize'
        )
        print(msg.format(__description__, __version__, sys.executable))
        sys.exit(0)

    if args.config is None:
        config = PEP8_CONFIG
    else:
        config = json.loads(read(args.config))

    for p in args.path:
        path = os.path.abspath(p)
        run(path, config, args)
