# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
import difflib
import importlib
import importlib.util
import io
import itertools
import logging
import os
import pathlib
import re
import stat
import sys
import typing
from contextlib import suppress

import click


log = logging.getLogger(__name__)
PREFIX_RE = re.compile(r"^\s+")


def _get_module_path(module_name: str) -> str:
    spec: typing.Optional[importlib.machinery.ModuleSpec] = None
    with suppress(AttributeError, ModuleNotFoundError):
        spec = importlib.util.find_spec(module_name)

    if spec and spec.origin:
        return os.path.normpath(spec.origin.lower())
    else:
        return ""


def _is_py_path(module_path: str) -> bool:
    modules = [
        i
        for i in [
            "typing",  # usually links to system python
            "re",  # usually links to virtualenv
            "math",  # is dynamic lib so path is diff
            "click",  # sometimes site-packages is directly inside venv so get parent folder
        ]
        if i not in sys.builtin_module_names
    ]
    return any(
        module_path.startswith(
            str(pathlib.Path(importlib.import_module(i).__file__).parent)
            .lower()
            .split("site-packages")[0]
        )
        for i in modules
    )


def _is_sitepackages_path(module_path: str) -> bool:
    return "site-packages" in module_path.split(os.sep)


def is_std_lib(module_name: str) -> bool:
    if not module_name:
        return False

    if module_name in sys.builtin_module_names:
        return True

    module_path = _get_module_path(module_name)
    return not _is_sitepackages_path(module_path) and _is_py_path(module_path)


def is_site_package(module_name: str) -> bool:
    if not module_name:
        return False

    module_path = _get_module_path(module_name)
    return _is_sitepackages_path(module_path) and _is_py_path(module_path)


def force_text(data: typing.Union[bytes, str]) -> str:
    if isinstance(data, bytes):
        return data.decode("utf-8")
    return data


def force_bytes(data: typing.Union[bytes, str]) -> bytes:
    if isinstance(data, str):
        return data.encode("utf-8")
    return data


def largest_prefix(strings: typing.Iterable[str]) -> str:
    return "".join(
        c[0]
        for c in itertools.takewhile(lambda chars: len(set(chars)) == 1, zip(*strings))
    )


class TextPrefixSpex(typing.NamedTuple):
    text: str
    prefix: str


def remove_largest_whitespace_prefix(text: str) -> TextPrefixSpex:
    lines = text.splitlines(keepends=True)
    prefix = largest_prefix(
        {next(iter(PREFIX_RE.findall(i.rstrip())), "") for i in lines if i.rstrip()}
    )
    if prefix:
        l_prefix = len(prefix)
        return TextPrefixSpex(
            "".join(l[l_prefix:] if l.startswith(prefix) else l for l in lines), prefix
        )
    else:
        return TextPrefixSpex(text, "")


def add_prefix_to_text(text: str, prefix: str) -> str:
    if not prefix:
        return text
    return "".join(
        prefix + l if l.rstrip() else l for l in text.splitlines(keepends=True)
    )


def generate_diff(text1: str, text2: str, name: str, color: bool = True) -> str:
    color_mapping: typing.Dict[str, str] = {
        "! ": "blue",
        "- ": "red",
        "+ ": "green",
    } if color else {}

    return "\n".join(
        click.style(i, fg=color_mapping[i[:2]]) if i[:2] in color_mapping else i
        for i in difflib.context_diff(
            text1.splitlines(),
            text2.splitlines(),
            fromfile=name,
            tofile=name,
            lineterm="",
            n=3,
        )
    )


def is_piped(fd: typing.Union[typing.BinaryIO, typing.TextIO] = sys.stdin) -> bool:
    return (
        # isatty catches cases when script is redirected from or to a file
        # e.g. script < file
        # e.g. script > file
        not fd.isatty()
        # S_ISFIFO specifically checks if script is being piped to or out of
        # e.g. echo foo | script
        # e.g. script | cat
        or stat.S_ISFIFO(os.fstat(fd.fileno()).st_mode)
    )


class OpenStringIO(io.StringIO):
    def close(self) -> None:
        """
        Dont close io buffer
        """

    def read(self, size: int = -1) -> str:
        self.seek(0)
        return super().read(size)

    def write(self, data: str) -> None:
        """
        Truncate buffer before writing
        """
        super().write(data)


BasePath = pathlib.Path
BasePath = type(pathlib.Path())


class StdPath(BasePath):
    prefix: str = ""
    stdin: typing.TextIO = sys.stdin
    stdout: typing.TextIO = sys.stdout
    filein: typing.TextIO = None
    fileout: typing.TextIO = None

    def with_streams(
        self,
        stdin: typing.TextIO = None,
        stdout: typing.TextIO = None,
        filein: typing.TextIO = None,
        fileout: typing.TextIO = None,
    ) -> "StdPath":
        self.stdin = stdin or self.stdin
        self.stdout = stdout or self.stdout
        self.filein = filein or self.filein
        self.fileout = fileout or self.fileout
        return self

    def open(
        self,
        mode: str = "r",
        buffering: int = -1,
        encoding: str = None,
        errors: str = None,
        newline: str = None,
    ) -> typing.IO[typing.Any]:
        return (self.filein if "r" in mode else self.fileout) or super().open(
            mode=mode,
            buffering=buffering,
            encoding=encoding,
            errors=errors,
            newline=newline,
        )

    def is_file(self) -> bool:
        return True if self.name == "-" else super().is_file()

    def read_text(self, encoding: str = None, errors: str = None) -> str:
        if self.name == "-":
            text, self.prefix = remove_largest_whitespace_prefix(self.stdin.read())
            if self.prefix:
                log.debug(f"Stripping prefix {self.prefix!r} in {self}")
            return text
        else:
            return super().read_text(encoding=encoding, errors=errors)

    def write_text(self, data: str, encoding: str = None, errors: str = None) -> None:
        if self.name == "-":
            self.stdout.write(add_prefix_to_text(data, self.prefix))
            self.stdout.flush()
        else:
            super().write_text(data, encoding=encoding, errors=errors)
