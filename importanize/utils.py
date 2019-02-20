# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
import importlib
import os
import sys


def _get_module_path(module_name):
    paths = sys.path[:]
    if os.getcwd() in sys.path:
        paths.remove(os.getcwd())

    try:
        return importlib.util.find_spec(module_name).origin
    except (AttributeError, ModuleNotFoundError):
        return ""


def is_std_lib(module_name):
    if not module_name:
        return False

    if module_name in sys.builtin_module_names:
        return True

    module_path = _get_module_path(module_name)
    if "site-packages" in module_path:
        return False
    return "python" in module_path or "pypy" in module_path


def is_site_package(module_name):
    if not module_name:
        return False

    module_path = _get_module_path(module_name)
    if "site-packages" not in module_path:
        return False
    return "python" in module_path or "pypy" in module_path


def force_text(data):
    try:
        return data.decode("utf-8")
    except AttributeError:
        return data


def force_bytes(data):
    try:
        return data.encode("utf-8")
    except AttributeError:
        return data


def isinstance_iter(i, *args):
    return filter(lambda j: isinstance(j, args), i)
