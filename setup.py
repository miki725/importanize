#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
import os

from setuptools import find_packages, setup  # type: ignore

from importanize import __author__, __description__, __version__


def read(fname):
    # type: (str) -> str
    with open(os.path.join(os.path.dirname(__file__), fname), "rb") as fid:
        return fid.read().decode("utf-8")


authors = read("AUTHORS.rst")
history = read("HISTORY.rst").replace(".. :changelog:", "")
licence = read("LICENSE.rst")
readme = read("README.rst")

requirements = read("requirements.txt").splitlines() + ["setuptools"]

test_requirements = (
    read("requirements.txt").splitlines()
    + read("requirements-dev.txt").splitlines()[3:]
)

setup(
    name="importanize",
    version=__version__,
    author=__author__,
    description=__description__,
    long_description="\n\n".join([readme, history, authors, licence]),
    long_description_content_type="text/x-rst",
    url="https://github.com/miki725/importanize",
    license="MIT",
    packages=find_packages(exclude=["test", "test.*"]),
    python_requires=">=3.6",
    install_requires=requirements,
    test_suite="tests",
    tests_require=test_requirements,
    entry_points={"console_scripts": ["importanize = importanize.__main__:cli"]},
    keywords=" ".join(["importanize"]),
    classifiers=[
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Development Status :: 2 - Pre-Alpha",
    ],
)
