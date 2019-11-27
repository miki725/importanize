# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
import logging
import sys
import typing

import click

from . import __description__, __version__
from .config import FORMATTERS, IMPORTANIZE_CONFIG, Config
from .importanize import RuntimeConfig
from .plugins import INSTALLED_PLUGINS, PLUGINS
from .utils import is_piped


LOGGING_FORMAT = "%(message)s"
VERBOSITY_MAPPING = {0: logging.ERROR, 1: logging.INFO, 2: logging.DEBUG}
logging.basicConfig(format=LOGGING_FORMAT, handlers=[logging.StreamHandler(sys.stderr)])
logging.getLogger("").setLevel(logging.ERROR)
log = logging.getLogger(__name__)


ROOT_CONFIG = Config.find(log_errors=False)


@click.command(help=__description__)
@click.argument(
    "path",
    type=click.Path(
        exists=True, file_okay=True, dir_okay=True, allow_dash=True, path_type=str
    ),
    nargs=-1,
    required=False,
)
@click.option(
    "-c",
    "--config",
    "config_path",
    type=click.Path(
        exists=True, file_okay=True, dir_okay=False, allow_dash=False, path_type=str
    ),
    help=(
        "Path to importanize config file. "
        "By default config {} is searched for in working "
        "and parent folders. "
        "If not found default pep8 configuration is used. "
        "[default {!r}]"
        "".format(", ".join(f'"{i}"' for i in IMPORTANIZE_CONFIG), str(ROOT_CONFIG))
    ),
)
@click.option(
    "--no-subconfig",
    "is_subconfig_allowed",
    default=True,
    is_flag=True,
    help="If provided, sub-configurations will not be used.",
)
@click.option(
    "--plugins/--no-plugins",
    "are_plugins_allowed",
    default=None,
    is_flag=True,
    help="If provided, no plugins will be activated.",
)
@click.option(
    "-f",
    "--formatter",
    type=click.Choice(sorted(FORMATTERS.keys())),
    help=(f"Formatter used. " f"[default {ROOT_CONFIG.formatter.name!r}]"),
)
@click.option(
    "-l",
    "--length",
    type=click.IntRange(10, 200),
    help=(
        f"Line length threshold when formatter will line break imports. "
        f"[default {ROOT_CONFIG.length}]"
    ),
)
@click.option(
    "--print",
    "is_print_mode",
    default=False,
    is_flag=True,
    help=(
        "If provided, instead of changing files, "
        "modified files are printed to stdout. "
        "Useful to check how importanize will importanize "
        "organizes imports without changing files."
    ),
)
@click.option(
    "--no-header",
    "show_header",
    default=True,
    is_flag=True,
    help=(
        "If provided, when printing files will not print header "
        "before each file. "
        "Useful to leave when multiple files are importanized."
    ),
)
@click.option(
    "--ci",
    "is_ci_mode",
    default=False,
    is_flag=True,
    help=(
        "When used CI mode will check if PATH contains expected "
        "imports as per importanize configuration. "
        "Exits with 1 if PATH is not importanized."
    ),
)
@click.option(
    "--diff",
    "show_diff",
    default=False,
    is_flag=True,
    help="When provided, in either CI or print mode will print diff within imports.",
)
@click.option(
    "--list",
    "is_list_mode",
    default=False,
    is_flag=True,
    help="List all imports found in all parsed files.",
)
@click.option(
    "--version",
    "is_version_mode",
    default=False,
    is_flag=True,
    help="Show the version number of importanize.",
)
@click.option(
    "-v",
    "--verbose",
    "verbosity",
    count=True,
    default=0,
    help=(
        "Print out fascinated debugging information. "
        "Can be supplied multiple times to increase verbosity level."
    ),
)
@click.pass_context
def cli(
    ctx: click.Context,
    path: typing.Iterable[str],
    # verbosity
    verbosity: int,
    # modes
    is_version_mode: bool,
    is_list_mode: bool,
    # ci mode
    is_ci_mode: bool,
    show_diff: bool,
    # print mode
    is_print_mode: bool,
    show_header: bool,
    # config
    is_subconfig_allowed: bool,
    are_plugins_allowed: bool = None,
    config_path: str = None,
    # config overwrites
    formatter: str = None,
    length: int = None,
) -> int:
    is_in_piped = is_piped(sys.stdin)
    is_out_piped = is_piped(sys.stdout, check_file_redirection=False)

    ctx.exit(
        main(
            RuntimeConfig(
                path_names=path or (["."] if not is_in_piped else []),
                formatter_name=formatter,
                length=length,
                root_config=ROOT_CONFIG,
                config_path=config_path,
                is_subconfig_allowed=is_subconfig_allowed,
                are_plugins_allowed=are_plugins_allowed,
                verbosity=verbosity,
                is_version_mode=is_version_mode,
                is_list_mode=is_list_mode,
                is_ci_mode=is_ci_mode,
                show_diff=show_diff,
                is_print_mode=is_print_mode,
                show_header=show_header,
                is_in_piped=is_in_piped,
                is_out_piped=is_out_piped,
            ).normalize()
        )
    )


def version(runtime_config: RuntimeConfig) -> int:
    plugins = (
        "\n" + "\n".join(f"{k}=={v.version}" for k, v in PLUGINS.items())
    ).rstrip()
    click.echo(
        f"importanize\n"
        f"===========\n"
        f"{__description__}\n\n"
        f"version: {__version__}\n"
        f"python: {sys.executable}\n"
        f"source: https://github.com/miki725/importanize\n\n"
        f"installed plugins:"
        f"{plugins}\n\n"
        f"root config ({runtime_config.merged_config}):\n\n"
        f"{runtime_config.merged_config!r}"
    )
    return 0


def main(runtime_config: RuntimeConfig) -> int:
    # adjust logging level
    logging.getLogger("").setLevel(VERBOSITY_MAPPING.get(runtime_config.verbosity, 0))

    log.debug(f"Running importanize with {runtime_config}")
    log.debug(f"Running with python {sys.executable}")
    log.debug(f"Installed plugins: {', '.join(INSTALLED_PLUGINS)}")

    if runtime_config.is_version_mode:
        return version(runtime_config)

    return runtime_config.aggregator()
