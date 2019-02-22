# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
import argparse
import inspect
import logging
import os
import pathlib
import pprint
import sys
from fnmatch import fnmatch
from itertools import chain
from stat import S_ISFIFO

from . import __description__, __version__, formatters
from .config import IMPORTANIZE_CONFIG, Config
from .formatters import DEFAULT_FORMATTER, DEFAULT_LENGTH
from .groups import ImportGroups
from .parser import ParseError, get_text_artifacts, parse_imports
from .utils import force_text


LOGGING_FORMAT = "%(message)s"
VERBOSITY_MAPPING = {0: logging.ERROR, 1: logging.INFO, 2: logging.DEBUG}

# initialize FORMATTERS dict
FORMATTERS = {
    formatter.name: formatter
    for formatter in vars(formatters).values()
    if (
        inspect.isclass(formatter)
        and formatter is not formatters.Formatter
        and issubclass(formatter, formatters.Formatter)
    )
}

# setup logging
logging.basicConfig(format=LOGGING_FORMAT)
logging.getLogger("").setLevel(logging.ERROR)
log = logging.getLogger(__name__)


parser = argparse.ArgumentParser(description=__description__)
parser.add_argument(
    "path",
    type=str,
    nargs="*",
    help=(
        "Path either to a file or directory where "
        "all Python files imports will be organized."
    ),
)
parser.add_argument(
    "-c",
    "--config",
    type=argparse.FileType("rb"),
    help=(
        "Path to importanize config file. "
        "If one of {} is present in either current folder "
        "or any parent folder, that config "
        "will be used. Otherwise crude default pep8 "
        "config will be used."
        "".format(", ".join(f'"{i}"' for i in IMPORTANIZE_CONFIG))
    ),
)
parser.add_argument(
    "-f",
    "--formatter",
    type=str,
    default=DEFAULT_FORMATTER,
    choices=sorted(FORMATTERS.keys()),
    help="Formatter used.",
)
parser.add_argument(
    "-l",
    "--length",
    type=int,
    help="Line length when formatters will break imports.",
)
parser.add_argument(
    "--print",
    action="store_true",
    default=False,
    help=(
        "If provided, instead of changing files, modified "
        "files will be printed to stdout."
    ),
)
parser.add_argument(
    "--no-header",
    action="store_false",
    default=True,
    dest="header",
    help=(
        "If provided, when printing files will not print header "
        "before each file. "
        "Useful to leave when multiple files are importanized."
    ),
)
parser.add_argument(
    "--no-subconfig",
    action="store_false",
    default=True,
    dest="subconfig",
    help="If provided, sub-configurations will not be used.",
)
parser.add_argument(
    "--ci",
    action="store_true",
    default=False,
    help=(
        "When used CI mode will check if file contains expected "
        "imports as per importanize configuration."
    ),
)
parser.add_argument(
    "--py",
    choices=[3, 2],
    type=int,
    help="Only run importanize with specific specified version.",
)
parser.add_argument(
    "--list",
    action="store_true",
    default=False,
    help="List all imports found in all parsed files",
)
parser.add_argument(
    "--version",
    action="store_true",
    default=False,
    help="Show the version number of importanize",
)
parser.add_argument(
    "-v",
    "--verbose",
    action="count",
    default=0,
    help=(
        "Print out fascinated debugging information. "
        "Can be supplied multiple times to increase verbosity level"
    ),
)


class CIFailure(Exception):
    pass


def run_importanize_on_text(text, config, args):
    file_artifacts = get_text_artifacts(text)

    # Get formatter from args or config
    formatter = FORMATTERS.get(
        args.formatter or config.get("formatter"), DEFAULT_FORMATTER
    )
    log.debug(f"Using {formatter} formatter")

    imports = list(parse_imports(text))

    groups = ImportGroups()

    for c in config["groups"]:
        groups.add_group(c)

    for i in imports:
        groups.add_statement_to_group(i)

    if args.list:
        return groups

    line_numbers = groups.all_line_numbers()
    line = min(line_numbers) if line_numbers else None
    first_import_line_number = line or file_artifacts["first_line"]

    lines = text.splitlines()
    for line_number in sorted(set(groups.all_line_numbers()), reverse=True):
        if lines:
            lines.pop(line_number)

    while line is not None and len(lines) > line:
        if not lines[line]:
            lines.pop(line)
        else:
            line = None

    for i in config.get("add_imports", []):
        for j in parse_imports(i, line_numbers=[first_import_line_number]):
            groups.add_statement_to_group(j)

    formatted_imports = groups.formatted(
        formatter=formatter,
        length=args.length or config.get("length") or DEFAULT_LENGTH,
    )

    lines = (
        lines[:first_import_line_number]
        + formatted_imports.splitlines()
        + (
            [""] * config.get("after_imports_new_lines", 2)
            if lines[first_import_line_number:] and formatted_imports
            else []
        )
        + lines[first_import_line_number:]
        + [""]
    )

    lines = file_artifacts.get("sep", "\n").join(lines)

    if args.ci and text != lines:
        raise CIFailure()

    return lines


def run(source, config, args, path=None):
    if isinstance(source, str):
        msg = "About to importanize"
        if path:
            msg += f" {path}"
        log.debug(msg)

        try:
            organized = run_importanize_on_text(source, config, args)

        except CIFailure:
            msg = "Imports not organized"
            if path:
                msg += f" in {path}"
            print(msg, file=sys.stderr)
            raise

        else:
            if args.list:
                yield organized
                return

            if args.print and args.header and path:
                print("=" * len(str(path)))
                print(str(path))
                print("-" * len(str(path)))

            if args.print:
                print(organized)

            else:
                if source == organized:
                    msg = "Nothing to do"
                    if path:
                        msg += f" in {path}"
                    log.info(msg)

                else:
                    path.write_text(organized)

                    msg = "Successfully importanized"
                    if path:
                        msg += f" {path}"
                    log.info(msg)

            yield organized

    elif source.is_file():
        if args.subconfig:
            config = (
                Config.find(
                    cwd=source.parent, root=getattr(config.path, "parent", None)
                )
                or config
            )

        if config.get("exclude"):
            norm = os.path.normpath(os.path.abspath(str(source)))
            if any(map(lambda i: fnmatch(norm, i), config.get("exclude"))):
                log.info(f"Skipping {source} as per {config}")
                return

        text = source.read_text("utf-8")
        try:
            yield from run(text, config, args, source)
        except ParseError:
            log.exception(f"Skipping {source} as it has invalid Python syntax")
            raise CIFailure()

    elif source.is_dir():
        if config.get("exclude"):
            norm = os.path.normpath(os.path.abspath(str(source)))
            if any(map(lambda i: fnmatch(norm, i), config.get("exclude"))):
                log.info(f"Skipping {source} as per {config}")
                return

        files = (
            f
            for f in source.iterdir()
            if not f.is_file() or f.is_file() and f.suffixes == [".py"]
        )

        all_successes = True
        for f in files:
            try:
                yield from run(f, config, args, f)
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
    (logging.getLogger("").setLevel(VERBOSITY_MAPPING.get(args.verbose, 0)))

    log.debug(f"Running importanize with {args}")

    if args.py and args.py != sys.version_info.major:
        log.debug(
            "Exiting as running in Python {} but only allowed to run in Python {}"
            "".format(sys.version_info.major, args.py)
        )
        return 0

    config = Config.from_path(getattr(args.config, "name", "")) or Config.find()

    if args.version:
        msg = (
            "importanize\n"
            "===========\n"
            "{description}\n\n"
            "version: {version}\n"
            "python: {python}\n"
            "source: https://github.com/miki725/importanize\n\n"
            "root config ({config}):\n"
            "{all_config}"
        )
        print(
            msg.format(
                description=__description__,
                version=__version__,
                python=sys.executable,
                config=config,
                all_config=pprint.pformat(config),
            )
        )
        return 0

    to_importanize = [pathlib.Path(i) for i in (args.path or ["."])]

    if is_piped() and not args.path:
        to_importanize = [force_text(sys.stdin.read())]
        args.print = True
        args.header = False

    if args.ci or args.list:
        args.print = False
        args.header = False

    all_successes = True
    all_groups = []

    for p in to_importanize:
        try:
            all_groups += [i for i in run(p, config, args)]
        except CIFailure:
            all_successes = False
        except Exception:
            log.exception("Error running importanize")
            return 1

    if args.list:
        groups = ImportGroups()
        for c in config["groups"]:
            groups.add_group(c)
        statements = chain(*(i.statements for i in chain(*all_groups)))
        for s in statements:
            groups.add_statement_to_group(s)
        for g in groups:
            print(g.config["type"])
            print("-" * len(g.config["type"]))
            for s in g.unique_statements:
                print(str(s))
            print()

    return int(not all_successes)


sys.exit(main()) if __name__ == "__main__" else None
