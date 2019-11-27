# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
import subprocess
import typing
from doctest import (  # type: ignore
    ELLIPSIS_MARKER,
    _ellipsis_match as ellipsis_match,
)

import docutils.frontend
import docutils.nodes
import docutils.parsers.rst
import docutils.utils
import pytest  # type: ignore


def parse_rst(text: str) -> docutils.nodes.document:
    parser = docutils.parsers.rst.Parser()
    components = (docutils.parsers.rst.Parser,)
    settings = docutils.frontend.OptionParser(
        components=components
    ).get_default_values()
    document = docutils.utils.new_document("<rst-doc>", settings=settings)
    parser.parse(text, document)
    return document


class CodeBlocksVisitor(docutils.nodes.NodeVisitor):  # type: ignore
    def __init__(self, *args, **kwargs) -> None:  # type: ignore
        super().__init__(*args, **kwargs)
        self.literal_blocks: typing.List[docutils.nodes.literal_block] = []

    def visit_literal_block(self, node: docutils.nodes.reference) -> None:
        self.literal_blocks.append(node)

    def unknown_visit(self, node: docutils.nodes.Node) -> None:
        pass


def literal_blocks(text: str) -> typing.List[str]:
    doc = parse_rst(text)
    visitor = CodeBlocksVisitor(doc)
    doc.walk(visitor)
    return [
        i.rawsource.encode("ascii", "ignore").decode("utf-8")
        for i in visitor.literal_blocks
    ]


def test_readme() -> None:
    with open("README.rst", "r") as fid:
        blocks = literal_blocks(fid.read())

    for block in blocks:
        if block.startswith("$"):
            lines = block.rstrip().splitlines()
            command = lines[0].lstrip("$ ")

            try:
                actual_lines = (
                    i.rstrip()
                    for i in subprocess.check_output(
                        command, shell=True, stderr=subprocess.PIPE
                    )
                    .decode("utf-8")
                    .rstrip()
                    .splitlines()
                )
            except subprocess.CalledProcessError as e:
                pytest.fail(e.stdout.decode("utf-8") + e.stderr.decode("utf-8"))

            expected = "\n".join(lines[1:])
            actual = "\n".join(actual_lines)

            if ELLIPSIS_MARKER in expected:
                assert ellipsis_match(expected, actual)
            else:
                assert expected == actual
