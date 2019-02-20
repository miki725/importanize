# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
import typing

import fissix
import fissix.pygram

from .statements import ImportLeaf, ImportStatement


ENCODING_COMMENTS = ("coding=", "coding:")
STATEMENT_COMMENTS = ("noqa",)
GRAMMARS = [
    fissix.pygram.python_grammar_no_print_statement,
    fissix.pygram.python_grammar,
]


class ParseError(Exception):
    pass


class Comment(str):
    def __new__(cls, value: str, **kwargs):
        return str.__new__(cls, value.lstrip().replace("#", "", 1).lstrip())


def parse_to_tree(text: str) -> fissix.pytree.Node:
    if not text:
        return fissix.pytree.Node(
            fissix.pygram.python_symbols.simple_stmt,
            [fissix.pytree.Leaf(fissix.pgen2.token.ENDMARKER, "")],
        )

    if text[-1] != "\n":
        text += "\n"

    error = None
    for grammar in GRAMMARS:
        try:
            return fissix.pgen2.driver.Driver(
                grammar, fissix.pytree.convert
            ).parse_string(text)
        except fissix.pgen2.parse.ParseError as e:
            error = e
    raise ParseError("Invalid Python syntax") from error


def get_text_artifacts(text: str) -> typing.Dict[str, typing.Union[str]]:
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
    try:
        tree = parse_to_tree(text)
    except ParseError:
        sep = "\n"
        first_line = 0
    else:
        pre_order = list(tree.pre_order())
        sep = next(
            filter(lambda i: i.type == fissix.pgen2.token.NEWLINE, pre_order),
            fissix.pytree.Leaf(fissix.pgen2.token.NEWLINE, "\n"),
        ).value

        first_node = next(
            filter(
                lambda i: isinstance(i, fissix.pytree.Leaf)
                and i.type
                not in {fissix.pgen2.token.NEWLINE, fissix.pgen2.token.STRING},
                pre_order,
            )
        )
        offset = 0
        for line in reversed(first_node.prefix.splitlines()):
            if not line:
                offset += 1
            else:
                break
        first_line = first_node.get_lineno() - 1 - offset

    return {"sep": sep, "first_line": max(first_line, 0)}


class Leaf:
    COMBINABLE_TYPES: set = {
        fissix.pgen2.token.NAME,
        fissix.pgen2.token.DOT,
        fissix.pgen2.token.COMMA,
        fissix.pgen2.token.STAR,
    }

    def __init__(self, leaf: fissix.pytree.Leaf, combinable_types: set = None):
        self.leaf: fissix.pytree.Leaf = leaf
        self.previous: fissix.pytree.Leaf = None
        self.next: fissix.pytree.Leaf = None

        self.type: int = self.leaf.type
        self.prefix: str = self.leaf.prefix
        self.value: str = self.leaf.value
        self.combinable_types: set = combinable_types or self.COMBINABLE_TYPES
        self.combinable_value: str = f" {self.leaf.value} " if self.leaf.value in {
            "as"
        } else self.leaf.value
        self.comments: typing.List[Comment] = []
        self.immediate_comments: typing.List[Comment] = []
        self.comment_lines: typing.List[str] = self.prefix.splitlines()

        immediate = self.immediate_comments
        for comment in reversed(self.comment_lines):
            if any(i in comment for i in ENCODING_COMMENTS):
                break
            if not comment.strip().startswith("#"):
                immediate = []
                continue
            self.comments.insert(0, Comment(comment))
            immediate.insert(0, Comment(comment))

    def get_lineno(self) -> int:
        return self.leaf.get_lineno() - 1

    @property
    def is_combinable(self):
        return self.type in self.combinable_types and self.value not in {
            "import"
        }

    def until(
        self,
        until: typing.Union[typing.List[typing.Union[str, int]], None] = None,
    ) -> typing.Iterable["Leaf"]:
        node = self
        yield node
        while node.next and (
            all(node.next != i for i in until) if until else True
        ):
            node = node.next
            yield node

    def split_until(
        self, sep: typing.List[typing.Union[str, int]]
    ) -> typing.Iterable[typing.List["Leaf"]]:
        node = self
        # import pdb; pdb.set_trace()
        while node:
            elements = list(node.until(sep))
            if any(i.is_combinable for i in elements):
                yield elements
            node = getattr(elements[-1].next, "next", None)

    def __eq__(self, other: object) -> bool:
        return (
            self.type == other
            if isinstance(other, int)
            else self.value == other
        )

    def __hash__(self):
        return id(self)


class Statement:
    IMPORT_TYPES = {
        v
        for k, v in vars(fissix.pygram.python_symbols).items()
        if k.startswith("import")
    }

    def __init__(self, node: fissix.pytree.Node):
        self.node: fissix.pytree.Node = node

    @property
    def is_import(self) -> bool:
        return (
            self.node.type == fissix.pygram.python_symbols.simple_stmt
            and self.node.children[0].type in self.IMPORT_TYPES
        )

    @property
    def import_type(self) -> str:
        return self.leafs[0].value

    @property
    def leafs(self) -> typing.List[Leaf]:
        try:
            return self._leafs
        except AttributeError:
            self._leafs: typing.List[Leaf] = []
            _leafs = [
                i
                for i in self.node.pre_order()
                if isinstance(i, fissix.pytree.Leaf)
            ]

            combinable_types = Leaf.COMBINABLE_TYPES.copy()
            if _leafs[0].value == "from":
                combinable_types.remove(fissix.pgen2.token.COMMA)

            self._leafs = _leafs = [Leaf(i, combinable_types) for i in _leafs]
            _prev = [None] + _leafs[:-1]
            _next = _leafs[1:] + [None]

            for p, l, n in zip(_prev, _leafs, _next):
                l.previous = p
                l.next = n

            return self._leafs

    @property
    def standalone_comments(self) -> typing.List[Comment]:
        return self.leafs[0].immediate_comments

    @property
    def line_numbers(self) -> typing.List[int]:
        line_numbers = {l.get_lineno() for l in self.leafs}
        return list(
            range(
                min(line_numbers) - len(self.standalone_comments),
                max(line_numbers) + 1,
            )
        )


def parse_imports(text: str, **kwargs) -> typing.Iterable[ImportStatement]:
    tree = parse_to_tree(text)

    for statement in filter(
        lambda i: i.is_import, map(Statement, tree.children)
    ):
        # import pdb; pdb.set_trace()
        leafs: typing.List[ImportLeaf] = []
        standalone_comments = statement.standalone_comments
        inline_comments: typing.List[Comment] = []
        line_numbers = kwargs.pop("line_numbers", statement.line_numbers)
        nodes = statement.leafs[1:]

        if statement.import_type == "import":
            # import statement has only inline comments
            # in all nodes within a statment so we can immediatly
            # add all of them to inline_comments
            for node in nodes:
                inline_comments += node.comments

            # much simpler to do splits on string and since
            # comments are already handled this is much simpler route
            data = "".join(n.combinable_value for n in nodes if n.is_combinable)

            # loop to handle multiple comma delimited imports
            for imp in data.split(","):
                leafs = []
                as_name: typing.Union[str, None] = None
                try:
                    stem, as_name = imp.split(" as ")
                except ValueError:
                    stem, as_name = imp, None

                stem_split = stem.rsplit(".", 1)
                # if import has "as" name and stem can be split to multiple imports
                # import can be transformed to from..import
                # e.g. import a.b.c as d -> from a.b import c as d
                # no need to handle local imports (e.g. import .a)
                # since that is invalid python syntax
                if as_name and all(stem_split) and len(stem_split) > 1:
                    stem = stem_split[0]
                    leafs.append(ImportLeaf(stem_split[1], as_name))
                    as_name = None

                yield ImportStatement(
                    stem=stem,
                    as_name=as_name,
                    leafs=leafs,
                    line_numbers=line_numbers,
                    standalone_comments=standalone_comments,
                    inline_comments=inline_comments,
                    **kwargs,
                )

        else:
            # all comments only within stem nodes
            # can be safely added as inline comments
            stem_nodes = list(nodes[0].until(["import"]))
            for i in stem_nodes:
                inline_comments += i.comments
            stem = "".join(
                n.combinable_value for n in stem_nodes if n.is_combinable
            )

            # get all nodes after "import" node
            # and split them by comma to hand e parse multiple import leafs
            last_node: Leaf = None
            for leaf_nodes in stem_nodes[-1].next.split_until([",", ")"]):
                last_node = leaf_nodes[-1]
                leaf_nodes = {v: k for k, v in enumerate(leaf_nodes)}

                imp_standalone_comments: typing.List[Comment] = []
                imp_inline_comments: typing.List[Comment] = []

                combinable_nodes = {
                    v: k for k, v in enumerate(leaf_nodes) if v.is_combinable
                }
                name = "".join(
                    n.combinable_value for n in combinable_nodes.keys()
                )
                try:
                    name, as_name = name.split(" as ")
                except ValueError:
                    name, as_name = name, None

                # find all imports within leaf nodes
                # and add to appropriate target either leaf comments
                # or to overall import statement inline comments
                # for comments such as "noqa"
                #
                # only exception here is handling comments
                # directly after a comma
                # in that case comment is added to next node
                # hence will be part of next import leaf which is not desired
                # therefore it manually needs to be added to previous leaf
                comment_nodes = {
                    v: k for k, v in enumerate(leaf_nodes) if v.comments
                }
                for inode, node in enumerate(comment_nodes):
                    prev_comment = Comment(next(iter(node.comment_lines), ""))

                    for ci, comment in enumerate(node.comments):
                        target = (
                            imp_standalone_comments
                            if node.is_combinable
                            else imp_inline_comments
                        )

                        if any(j in comment for j in STATEMENT_COMMENTS):
                            inline_comments.append(comment)
                        else:
                            if (
                                inode == 0
                                and ci == 0
                                and comment == prev_comment
                                and comment_nodes[node]
                                <= max(combinable_nodes.values())
                            ):
                                target = (
                                    leafs[-1].inline_comments
                                    if leafs
                                    else inline_comments
                                )
                            target.append(comment)

                leafs.append(
                    ImportLeaf(
                        name=name,
                        as_name=as_name,
                        standalone_comments=imp_standalone_comments,
                        inline_comments=imp_inline_comments,
                        **kwargs,
                    )
                )

            # possible to have more nodes after all leafs are exhausted
            # e.g. if last leaf as a comma
            # so those comments need to be accounted for
            # there are 2 possibilities
            # 1) comment belongs to last leaf
            # 2) unless comment is after newline or ")" in which case belogs
            #    as statement inline comment
            imp_rest_nodes = list(getattr(last_node.next, "until", list)())
            try:
                par_index = imp_rest_nodes.index(")")
            except ValueError:
                par_index = len(imp_rest_nodes)
            for inode, node in enumerate(
                [i for i in imp_rest_nodes if i.comments]
            ):
                prev_comment = Comment(next(iter(node.comment_lines), ""))

                for ci, comment in enumerate(node.comments):
                    target = inline_comments

                    if any(j in comment for j in STATEMENT_COMMENTS):
                        inline_comments.append(comment)
                    else:
                        if (
                            inode == 0
                            and ci == 0
                            and inode < par_index
                            and comment == prev_comment
                        ):
                            target = leafs[-1].inline_comments
                        target.append(comment)

            yield ImportStatement(
                stem=stem,
                as_name=None,
                leafs=leafs,
                line_numbers=line_numbers,
                standalone_comments=standalone_comments,
                inline_comments=inline_comments,
                **kwargs,
            )
