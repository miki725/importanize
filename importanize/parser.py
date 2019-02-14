# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
from functools import partial

import redbaron
import six

from .statements import ImportLeaf, ImportStatement
from .utils import isinstance_iter


IGNORE_COMMENTS = ("coding=", "coding:")
STATEMENT_COMMENTS = ("noqa",)


class Comment(six.text_type):
    def __new__(cls, value, **kwargs):
        return six.text_type.__new__(
            cls, value.lstrip().replace("#", "", 1).lstrip()
        )


def get_text_artifacts(text):
    """
    Get artifacts for the given file.

    Parameters
    ----------
    path : str
        File content to analyze

    Returns
    -------
    artifacts : dict
        Dictionary of file artifacts which should be
        considered while processing imports.
    """
    tree = redbaron.RedBaron(text)

    return {"sep": getattr(tree.endl, "value", "\n")}


def parse_imports(text, **kwargs):
    tree = redbaron.RedBaron(text)

    for node in isinstance_iter(
        tree, redbaron.ImportNode, redbaron.FromImportNode
    ):
        pre_comments = []
        inline_comments = []
        line_numbers = kwargs.pop("line_numbers", _node_line_numbers(node))

        for prev_node in _prev_nodes(
            node,
            stop=lambda i: (
                not isinstance(i, (redbaron.CommentNode, redbaron.EndlNode))
                or any(j in i.value for j in IGNORE_COMMENTS)
                or (
                    isinstance(i, redbaron.CommentNode)
                    and i.absolute_bounding_box.top_left.column != 1
                )
            ),
            predicate=lambda i: isinstance(i, redbaron.CommentNode),
        ):
            pre_comments.insert(0, Comment(prev_node.value))
            line_numbers = list(
                sorted(set(line_numbers + _node_line_numbers(prev_node)))
            )

        if isinstance(node, redbaron.ImportNode):
            for next_node in _next_nodes(
                node,
                stop=lambda i: (
                    not set(_node_line_numbers(i)) & set(line_numbers)
                ),
                predicate=lambda i: isinstance(i, redbaron.CommentNode),
            ):
                inline_comments.append(Comment(next_node.value))
                line_numbers = list(
                    sorted(set(line_numbers + _node_line_numbers(next_node)))
                )

            for imp in isinstance_iter(
                node.value.node_list, redbaron.DottedAsNameNode
            ):
                stem = "".join(
                    [
                        "." if isinstance(i, redbaron.DotNode) else i.value
                        for i in imp.value.node_list
                    ]
                )
                stem_split = stem.rsplit(".", 1)
                as_name = imp.target or None
                leafs = []

                # if using local import you cannot refer to import anywhere in file
                # since symbol starts with a dot therefore it can safely transformed to from..import
                if stem.startswith("."):
                    _stem, _as_name = stem_split
                    stem = (
                        "." + _stem
                        if not _stem or _stem.endswith(".")
                        else _stem
                    )
                    leafs.append(ImportLeaf(_as_name, as_name, **kwargs))
                    as_name = None

                # if import has as target but stem can be split to multiple imports
                # import can be transformed to from..import
                elif as_name and all(stem_split) and len(stem_split) > 1:
                    stem = stem_split[0]
                    leafs.append(ImportLeaf(stem_split[1], as_name))
                    as_name = None

                yield ImportStatement(
                    stem=stem,
                    as_name=as_name,
                    leafs=leafs,
                    line_numbers=line_numbers,
                    pre_comments=pre_comments,
                    inline_comments=inline_comments,
                    **kwargs
                )

        elif isinstance(node, redbaron.FromImportNode):
            leafs = []
            seen_comments = []

            for imp in isinstance_iter(
                node.targets.node_list,
                redbaron.NameAsNameNode,
                redbaron.StarNode,
            ):
                imp_pre_comments = []
                imp_inline_comments = []
                all_comments = node.find_all("comment")

                for comment in filter(
                    lambda i: (
                        i.absolute_bounding_box.top_left.line
                        <= imp.absolute_bounding_box.top_left.line
                        and id(i) not in seen_comments
                    ),
                    all_comments,
                ):
                    target = (
                        imp_pre_comments
                        if comment.absolute_bounding_box.top_left.line
                        < imp.absolute_bounding_box.top_left.line
                        else imp_inline_comments
                    )
                    if any(i in comment.value for i in STATEMENT_COMMENTS):
                        target = inline_comments
                    target.insert(0, Comment(comment.value))
                    seen_comments.append(id(comment))

                leafs.append(
                    ImportLeaf(
                        name=imp.value,
                        as_name=getattr(imp, "target", None) or None,
                        pre_comments=imp_pre_comments,
                        inline_comments=imp_inline_comments,
                        **kwargs
                    )
                )

            for next_node in _next_nodes(
                node,
                stop=lambda i: (
                    not set(_node_line_numbers(i)) & set(line_numbers)
                ),
                predicate=lambda i: isinstance(i, redbaron.CommentNode),
            ):
                target = leafs[-1].inline_comments
                if any(
                    i in next_node.value for i in STATEMENT_COMMENTS
                ) or not set(_node_line_numbers(imp)) & set(
                    _node_line_numbers(next_node)
                ):
                    target = inline_comments
                target.append(Comment(next_node.value))
                line_numbers = list(
                    sorted(set(line_numbers + _node_line_numbers(next_node)))
                )

            yield ImportStatement(
                stem="".join(
                    [
                        "." if isinstance(i, redbaron.DotNode) else i.value
                        for i in node.value.node_list
                    ]
                ),
                leafs=leafs,
                line_numbers=line_numbers,
                pre_comments=pre_comments,
                inline_comments=inline_comments,
                **kwargs
            )


def _nodes(node, stop=None, predicate=None, direction=None):
    node = getattr(node, direction)
    stop = stop or (lambda i: False)
    predicate = predicate or (lambda i: True)
    while node:
        if stop(node):
            break
        if predicate(node):
            yield node
        node = getattr(node, direction)


_prev_nodes = partial(_nodes, direction="previous")
_next_nodes = partial(_nodes, direction="next")


def _node_line_numbers(node):
    return list(
        range(
            node.absolute_bounding_box.top_left.line - 1,
            node.absolute_bounding_box.bottom_right.line,
        )
    )
