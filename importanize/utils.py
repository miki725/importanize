# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
import imp
import operator
import os
import sys


def _get_module_path(module_name):
    paths = sys.path[:]
    if os.getcwd() in sys.path:
        paths.remove(os.getcwd())

    try:
        # TODO deprecated in Py3.
        # TODO Find better way for py2 and py3 compatibility.
        return imp.find_module(module_name, paths)[1]
    except ImportError:
        return ''


def is_std_lib(module_name):
    if not module_name:
        return False

    if module_name in sys.builtin_module_names:
        return True

    module_path = _get_module_path(module_name)
    if 'site-packages' in module_path:
        return False
    return 'python' in module_path or 'pypy' in module_path


def is_site_package(module_name):
    if not module_name:
        return False

    module_path = _get_module_path(module_name)
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


def force_text(data):
    try:
        return data.decode('utf-8')
    except AttributeError:
        return data


def force_bytes(data):
    try:
        return data.encode('utf-8')
    except AttributeError:
        return data
