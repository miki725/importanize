# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
import contextlib
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
import tokenize
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


T = typing.TypeVar("T")


def takeafter(
    predicate: typing.Callable[[T], typing.Any], iterable: typing.Iterable[T]
) -> typing.Iterator[T]:
    found = False
    for i in iterable:
        if not found and predicate(i):
            found = True
        if found:
            yield i


def list_set(iterable: typing.Iterable[T]) -> typing.List[T]:
    items: typing.List[T] = []
    for i in iterable:
        if i not in items:
            items.append(i)
    return items


class TextPrefixSpex(typing.NamedTuple):
    text: str
    prefix: str


def get_number_clusters(numbers: typing.List[int]) -> typing.List[typing.List[int]]:
    """
    Get the number clusters

    ::

        >>> get_number_clusters([1, 2, 3, 5, 6, 8, 9])
        [[1, 2, 3], [5, 6], [8, 9]]
    """
    clusters = []
    cluster = []
    for i, number in enumerate(numbers):
        previous_number = numbers[max(i - 1, 0)]
        if previous_number <= number <= previous_number + 1:
            cluster.append(number)
        else:
            clusters.append(cluster)
            cluster = []
            cluster.append(number)
    if cluster:
        clusters.append(cluster)
    return clusters


def get_number_cluster_gaps(numbers: typing.List[int]) -> typing.List[typing.List[int]]:
    """
    Get the gaps between number clusters

    ::

        >>> get_number_cluster_gaps([1, 2, 3, 5, 6, 8, 9, 13, 14, 16])
        [[4], [7], [10, 11, 12], [15]]
    """
    clusters = get_number_clusters(numbers)
    gaps = []

    for i, cluster in enumerate(clusters[1:]):
        previous_cluster = clusters[i]
        gaps.append(list(range(previous_cluster[-1] + 1, cluster[0])))

    return gaps


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
        "@": "blue",
        "-": "red",
        "+": "green",
    } if color else {}

    return "\n".join(
        click.style(i, fg=color_mapping[i[:1]]) if i[:1] in color_mapping else i
        for i in difflib.unified_diff(
            text1.splitlines(),
            text2.splitlines(),
            fromfile=f"original{os.sep}{name}",
            tofile=f"importanized{os.sep}{name}",
            lineterm="",
            n=3,
        )
    )


def is_piped(
    fd: typing.Union[typing.BinaryIO, typing.TextIO] = sys.stdin,
    check_file_redirection: bool = True,
) -> bool:
    with contextlib.suppress(Exception):
        return (
            # isatty catches cases when script is redirected from or to a file
            # e.g. script < file
            # e.g. script > file
            (not fd.isatty() and check_file_redirection)
            # S_ISFIFO specifically checks if script is being piped to or out of
            # e.g. echo foo | script
            # e.g. script | cat
            or stat.S_ISFIFO(os.fstat(fd.fileno()).st_mode)
        )


class OpenBytesIO(io.BytesIO):
    def close(self) -> None:
        """
        Dont close io buffer
        """

    def read(self, size: int = -1) -> bytes:
        self.seek(0)
        return super().read(size)


class OpenStringIO(io.StringIO):
    def close(self) -> None:
        """
        Dont close io buffer
        """

    def read(self, size: int = -1) -> str:
        self.seek(0)
        return super().read(size)


BasePath = pathlib.Path
BasePath = type(pathlib.Path())  # type: ignore


class StdPath(BasePath):
    prefix: str = ""
    encoding: str = "utf-8"
    stdin: typing.BinaryIO = sys.stdin.buffer
    stdout: typing.BinaryIO = sys.stdout.buffer
    filein: typing.BinaryIO = None
    fileout: typing.BinaryIO = None

    def with_streams(
        self,
        stdin: typing.BinaryIO = None,
        stdout: typing.BinaryIO = None,
        filein: typing.BinaryIO = None,
        fileout: typing.BinaryIO = None,
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

    def is_std_stream(self) -> bool:
        return self.name == "-"

    def is_file(self) -> bool:
        return self.is_std_stream() or super().is_file()

    def decode_pep263(self, data: bytes) -> typing.Tuple[str, str]:
        encoding, lines = tokenize.detect_encoding(io.BytesIO(data).readline)

        try:
            return data.decode(encoding), encoding
        except UnicodeDecodeError as e:
            raise UnicodeDecodeError(
                e.encoding,
                e.object,
                e.start,
                e.end,
                (
                    f"\n"
                    f"Cannot read Python file {self.name!r} "
                    f"with PEP263 encoding={self.encoding!r}. \n"
                    f"Make sure encoding comment is correct in the begining of the file. \n"
                    f"For example: \n"
                    f"# -*- coding: utf-8 -*-"
                ),
            ) from e

    def read_text(self, encoding: str = None, errors: str = None) -> str:
        if self.is_std_stream():
            text, self.encoding = self.decode_pep263(self.stdin.read())
            text_without_whitespace, self.prefix = remove_largest_whitespace_prefix(
                text
            )
            if self.prefix:
                log.debug(f"Stripping prefix {self.prefix!r} in {self}")
            return text_without_whitespace

        else:
            text, self.encoding = self.decode_pep263(super().read_bytes())
            return text

    def write_text(self, data: str, encoding: str = None, errors: str = None) -> None:
        if self.is_std_stream():
            self.stdout.write(
                add_prefix_to_text(data, self.prefix).encode(self.encoding)
            )
            self.stdout.flush()
        else:
            super().write_bytes(data.encode(encoding or self.encoding))
