# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from importanize.utils import (
    force_bytes,
    force_text,
    is_site_package,
    is_std_lib,
    isinstance_iter,
)


def test_is_std_lib():
    assert not is_std_lib("")
    assert not is_std_lib("foo")

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


def test_is_site_package():
    assert not is_site_package("")
    assert not is_site_package("foo")

    stdlib_modules = ("argparse", "codecs")
    for module in stdlib_modules:
        assert not is_site_package(module)

    # these packages come from requirements-dev.txt
    site_packages_modules = ("pytest", "tox")
    for module in site_packages_modules:
        assert is_site_package(module)


def test_force_text():
    assert force_text(b"foo") == "foo"
    assert force_text("foo") == "foo"


def test_force_bytes():
    assert force_bytes("foo") == b"foo"
    assert force_bytes(b"foo") == b"foo"


def test_isinstance_iter():
    assert list(isinstance_iter([1, "1", 2, "2"], int)) == [1, 2]
