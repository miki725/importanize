# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
import argparse
import inspect
import json
import logging
import os
import sys
from fnmatch import fnmatch
from stat import S_ISFIFO

import pathlib2 as pathlib
import six

from . import __description__, __version__, formatters
from .formatters import DEFAULT_FORMATTER
from .groups import ImportGroups
from .parser import (
    find_imports_from_lines,
    get_text_artifacts,
    parse_statements,
)
from .utils import force_text, read


LOGGING_FORMAT = '%(message)s'
IMPORTANIZE_CONFIG = '.importanizerc'
PEP8_CONFIG = {
    'groups': [
        {
            'type': 'stdlib',
        },
        {
            'type': 'sitepackages',
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
    if (inspect.isclass(formatter) and
        formatter is not formatters.Formatter and
        issubclass(formatter, formatters.Formatter))
}

# setup logging
logging.basicConfig(format=LOGGING_FORMAT)
logging.getLogger('').setLevel(logging.ERROR)
log = logging.getLogger(__name__)


def find_config():
    path = pathlib.Path.cwd()
    default_config = None

    while path != pathlib.Path(path.root):
        config_path = path / IMPORTANIZE_CONFIG
        if config_path.exists():
            default_config = six.text_type(config_path)
            break
        else:
            path = path.parent

    return default_config


parser = argparse.ArgumentParser(
    description=__description__,
)
parser.add_argument(
    'path',
    type=six.text_type,
    nargs='*',
    help='Path either to a file or directory where '
         'all Python files imports will be organized.',
)
parser.add_argument(
    '-c', '--config',
    type=argparse.FileType('rb'),
    help='Path to importanize config json file. '
         'If "{}" is present in either current folder '
         'or any parent folder, that config '
         'will be used. Otherwise crude default pep8 '
         'config will be used.'
         ''.format(IMPORTANIZE_CONFIG),
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
    '--no-header',
    action='store_false',
    default=True,
    dest='header',
    help='If provided, when printing files will not print header '
         'before each file. '
         'Useful to leave when multiple files are importanized.'
)
parser.add_argument(
    '--ci',
    action='store_true',
    default=False,
    help='When used CI mode will check if file contains expected '
         'imports as per importanize configuration.'
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


class CIFailure(Exception):
    pass


def run_importanize_on_text(text, config, args):
    file_artifacts = get_text_artifacts(text)

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

    lines = (
        lines[:first_import_line_number] +
        formatted_imports.splitlines() +
        ([''] * config.get('after_imports_new_lines', 2)
         if lines[first_import_line_number:] and formatted_imports
         else []) +
        lines[first_import_line_number:] +
        ['']
    )

    lines = file_artifacts.get('sep', '\n').join(lines)

    if args.ci and text != lines:
        raise CIFailure()

    return lines


def run(source, config, args, path=None):
    if isinstance(source, six.string_types):
        msg = 'About to importanize'
        if path:
            msg += ' {}'.format(path)
        log.debug(msg)

        try:
            organized = run_importanize_on_text(source, config, args)

        except CIFailure:
            msg = 'Imports not organized'
            if path:
                msg += ' in {}'.format(path)
            print(msg, file=sys.stderr)
            raise

        else:
            if args.print and args.header and path:
                print('=' * len(six.text_type(path)))
                print(six.text_type(path))
                print('-' * len(six.text_type(path)))

            if args.print:
                print(organized.encode('utf-8') if not six.PY3 else organized)

            else:
                if source == organized:
                    msg = 'Nothing to do'
                    if path:
                        msg += ' in {}'.format(path)
                    log.info(msg)

                else:
                    path.write_text(organized)

                    msg = 'Successfully importanized'
                    if path:
                        msg += ' {}'.format(path)
                    log.info(msg)

            return organized

    elif source.is_file():
        if config.get('exclude'):
            norm = os.path.normpath(os.path.abspath(six.text_type(source)))
            if any(map(lambda i: fnmatch(norm, i),
                       config.get('exclude'))):
                log.info('Skipping {}'.format(source))
                return

        text = source.read_text('utf-8')
        return run(text, config, args, source)

    elif source.is_dir():
        if config.get('exclude'):
            norm = os.path.normpath(os.path.abspath(six.text_type(source)))
            if any(map(lambda i: fnmatch(norm, i),
                       config.get('exclude'))):
                log.info('Skipping {}'.format(source))
                return

        files = (
            f for f in source.iterdir()
            if not f.is_file() or f.is_file() and f.suffixes == ['.py']
        )

        all_successes = True
        for f in files:
            try:
                run(f, config, args, f)
            except CIFailure:
                all_successes = False

        if not all_successes:
            raise CIFailure()


def is_piped():
    return S_ISFIFO(os.fstat(0).st_mode)


def main(args=None):
    args = args if args is not None else sys.argv[1:]
    args = parser.parse_args(args=args)

    # adjust logging level
    (logging.getLogger('')
     .setLevel(VERBOSITY_MAPPING.get(args.verbose, 0)))

    log.debug('Running importanize with {}'.format(args))

    config_path = getattr(args.config, 'name', '') or find_config()

    if args.version:
        msg = (
            'importanize\n'
            '===========\n'
            '{description}\n\n'
            'version: {version}\n'
            'python: {python}\n'
            'config: {config}\n'
            'source: https://github.com/miki725/importanize'
        )
        print(msg.format(
            description=__description__,
            version=__version__,
            python=sys.executable,
            config=config_path or '<default pep8>',
        ))
        return 0

    config = json.loads(read(config_path)) if config_path else PEP8_CONFIG

    to_importanize = [pathlib.Path(i) for i in (args.path or ['.'])]

    if is_piped() and not args.path:
        to_importanize = [force_text(sys.stdin.read())]
        args.print = True
        args.header = False

    if args.ci:
        args.print = False
        args.header = False

    all_successes = True

    for p in to_importanize:
        try:
            run(p, config, args)
        except CIFailure:
            all_successes = False
        except Exception:
            log.exception('Error running importanize')
            return 1

    return int(not all_successes)


sys.exit(main()) if __name__ == '__main__' else None
