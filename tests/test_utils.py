# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
import io

import pytest  # type: ignore

from importanize.utils import (
    OpenBytesIO,
    OpenStringIO,
    StdPath,
    add_prefix_to_text,
    force_bytes,
    force_text,
    generate_diff,
    is_piped,
    is_site_package,
    is_std_lib,
    largest_prefix,
    list_set,
    remove_largest_whitespace_prefix,
    takeafter,
)


def test_is_std_lib() -> None:
    assert not is_std_lib("")
    assert not is_std_lib("foo")
    assert not is_std_lib("pytest")

    stdlib_modules = (
        "argparse",
        "codecs",
        "collections",
        "copy",
        "csv",
        "datetime",
        "decimal",
        "fileinput",
        "fnmatch",
        "functools",
        "glob",
        "gzip",
        "hashlib",
        "hmac",
        "importlib",
        "io",
        "itertools",
        "json",
        "logging",
        "math",
        "numbers",
        "operator",
        "optparse",
        "os",
        "pickle",
        "pprint",
        "random",
        "re",
        "shelve",
        "shutil",
        "socket",
        "sqlite3",
        "ssl",
        "stat",
        "string",
        "struct",
        "subprocess",
        "sys",
        "typing",
        "sysconfig",
        "tempfile",
        "time",
        "timeit",
        "trace",
        "traceback",
        "unittest",
        "uuid",
        "xml",
        "zlib",
    )
    for module in stdlib_modules:
        assert is_std_lib(module)


def test_is_site_package() -> None:
    assert not is_site_package("")
    assert not is_site_package("foo")

    stdlib_modules = ("argparse", "codecs")
    for module in stdlib_modules:
        assert not is_site_package(module)

    # these packages come from requirements-dev.txt
    site_packages_modules = ("pytest", "tox")
    for module in site_packages_modules:
        assert is_site_package(module)


def test_force_text() -> None:
    assert force_text(b"foo") == "foo"
    assert force_text("foo") == "foo"


def test_force_bytes() -> None:
    assert force_bytes("foo") == b"foo"
    assert force_bytes(b"foo") == b"foo"


def test_takeafter() -> None:
    assert list(takeafter(lambda i: i.strip(), ["  ", "\t", "foo", "  ", "bar"])) == [
        "foo",
        "  ",
        "bar",
    ]


def test_list_set() -> None:
    assert list_set(["hello", "world", "hello", "mars"]) == ["hello", "world", "mars"]


def test_largest_prefix() -> None:
    assert largest_prefix(["  hello", " world"]) == " "


def test_remove_largest_prefix_from_text() -> None:
    assert remove_largest_whitespace_prefix("  hello\n  world\n") == (
        "hello\nworld\n",
        "  ",
    )
    assert remove_largest_whitespace_prefix("hello\nworld\n") == ("hello\nworld\n", "")


def test_add_prefix_to_text() -> None:
    assert add_prefix_to_text("hello\nworld\n", "  ") == "  hello\n  world\n"
    assert add_prefix_to_text("hello\nworld\n", "") == "hello\nworld\n"


def test_generate_diff() -> None:
    assert generate_diff(
        "hello\nworld", "hello\nmars", "test.py", color=False
    ) == "\n".join(
        [
            # preserve multiline
            "--- original/test.py",
            "+++ importanized/test.py",
            "@@ -1,2 +1,2 @@",
            " hello",
            "-world",
            "+mars",
        ]
    )


def test_is_piped() -> None:
    assert is_piped(io.StringIO())


def test_open_bytes_io() -> None:
    fid = OpenBytesIO(b"hello")
    assert fid.read() == b"hello"
    assert fid.read() == b"hello"
    fid.close()
    assert fid.read() == b"hello"


def test_open_string_io() -> None:
    fid = OpenStringIO("hello")
    assert fid.read() == "hello"
    assert fid.read() == "hello"
    fid.close()
    assert fid.read() == "hello"


class TestStdPath:
    def test_stdin(self) -> None:
        p = StdPath("-").with_streams(
            stdin=io.BytesIO(b"  hello\n  world\n"), stdout=io.BytesIO()
        )

        assert p.is_file()

        assert p.read_text() == "hello\nworld\n"

        p.write_text("hello\nmars\n")
        p.stdout.seek(0)

        assert p.stdout.read() == b"  hello\n  mars\n"

    def test_file(self) -> None:
        p = StdPath("test").with_streams(
            filein=OpenBytesIO(b"hello world"), fileout=OpenBytesIO()
        )

        assert p.read_text() == "hello world"

        p.write_text("hello mars")

        assert p.fileout.read() == b"hello mars"

    def test_pep263(self) -> None:
        p = StdPath("-").with_streams(
            stdin=io.BytesIO("# -*- coding: ascii -*-\nпривет".encode("utf-8")),
            stdout=io.BytesIO(),
        )

        assert p.is_file()

        with pytest.raises(UnicodeDecodeError):
            assert p.read_text()
