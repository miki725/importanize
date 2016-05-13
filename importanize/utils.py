# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
import operator
import os
import sys
from contextlib import contextmanager
from importlib import import_module


@contextmanager
def ignore_site_packages_paths():
    paths = sys.path[:]
    try:
        # remove working directory so that all
        # local imports fail
        if os.getcwd() in sys.path:
            sys.path.remove(os.getcwd())
        # remove all third-party paths
        # so that only stdlib imports will succeed
        sys.path = list(set(filter(
            None,
            filter(lambda i: all(('site-packages' not in i,
                                  'python' in i or 'pypy' in i)),
                   map(operator.methodcaller('lower'), sys.path))
        )))
        yield
    finally:
        sys.path = paths

def _safe_import_module(module_name):
    imported_module = sys.modules.pop(module_name, None)
    try:
        return import_module(module_name)
    except ImportError:
        return None
    finally:
        if imported_module:
            sys.modules[module_name] = imported_module

def is_std_lib(module_name):
    if not module_name:
        return False

    if module_name in sys.builtin_module_names:
        return True

    with ignore_site_packages_paths():
        return bool(_safe_import_module(module_name))

def is_site_package(module_name):
    if not module_name:
        return False

    module = _safe_import_module(module_name)
    module_path = getattr(module, "__file__", "")
    if "site-packages" not in module_path:
        return False
    return "python" in module_path or "pypy" in module_path


def list_strip(data):
    """
    Return list of stripped strings from given list
    """
    return list(map(operator.methodcaller('strip'), data))


def read(path):
    with open(path, 'rb') as fid:
        return fid.read().decode('utf-8')


def list_split(iterable, split):
    segment = []

    for i in iterable:
        if i == split:
            yield segment
            segment = []
        else:
            segment.append(i)

    if segment:
        yield segment
