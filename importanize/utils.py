# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
import operator
import os
import sys
from contextlib import contextmanager
from importlib import import_module


@contextmanager
def site_packages_paths(filter_func):
    paths = sys.path[:]
    # remove working directory so that all
    # local imports fail
    if os.getcwd() in sys.path:
        sys.path.remove(os.getcwd())
    # remove all third-party paths
    # so that only stdlib imports will succeed
    sys.path = list(set(filter(
        None,
        filter(lambda i: all((filter_func(i), 'python' in i or 'pypy' in i)),
               map(operator.methodcaller('lower'), sys.path))
    )))
    yield
    sys.path = paths


def _is_installed_module(module, filter_func, builtin_result):
    if not module:
        return False

    if module in sys.builtin_module_names:
        return builtin_result

    with site_packages_paths(filter_func):
        imported_module = sys.modules.pop(module, None)
        try:
            import_module(module)
        except ImportError:
            return False
        else:
            return True
        finally:
            if imported_module:
                sys.modules[module] = imported_module

def is_std_lib(module):
    return _is_installed_module(
                        module,
                        lambda i: "site-packages" not in i,
                        True)

def is_site_packages(module):
    return _is_installed_module(
                        module,
                        lambda i: "site-packages" in i,
                        False)


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
