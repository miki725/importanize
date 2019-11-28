# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
import itertools
import lib2to3
import lib2to3.pgen2.driver
import lib2to3.pgen2.parse
import lib2to3.pgen2.token
import lib2to3.pygram
import lib2to3.pytree
import typing
from dataclasses import dataclass

from .plugins import plugin_hooks
from .statements import ImportLeaf, ImportStatement


ENCODING_COMMENTS = ("coding=", "coding:")
STATEMENT_COMMENTS = ("noqa", "type:")
GRAMMARS = [
    lib2to3.pygram.python_grammar_no_print_statement,
    lib2to3.pygram.python_grammar,
]


def normalize_comment(value: str) -> str:
    """
    Normalize a comment to remove all the #
    """
    return value.lstrip().replace("#", "", 1).lstrip()


def is_comment(value: str) -> bool:
    return value.strip().startswith("#")


def is_comment_encoding(comment: str) -> bool:
    return any(
        [
            any(i in comment for i in ENCODING_COMMENTS),
            normalize_comment(comment).startswith("!"),
        ]
    )


class ParseError(Exception):
    """
    Exception to indicate code text cannot be parsed
    """


@dataclass
class Artifacts:
    sep: str = "\n"
    """
    Line separator
    """
    first_line: int = 0
    """
    First line where imports should be placed
    if no imports are already present in file
    """

    @classmethod
    def default(cls) -> "Artifacts":
        return cls()


def parse_to_tree(text: str) -> lib2to3.pytree.Node:
    """
    Parse given code text to lib2to3 ``Node`` tree
    """
    text = text.rstrip("\n") + "\n"

    error = None
    for grammar in GRAMMARS:
        try:
            node = lib2to3.pgen2.driver.Driver(
                grammar, lib2to3.pytree.convert
            ).parse_string(text)
        except lib2to3.pgen2.parse.ParseError as e:
            error = e
        else:
            if isinstance(node, lib2to3.pytree.Leaf):
                return lib2to3.pytree.Node(
                    lib2to3.pygram.python_symbols.simple_stmt, [node]
                )
            return node
    raise ParseError(str(error)) from error


def get_tree_artifacts(tree: lib2to3.pytree.Node, text: str) -> Artifacts:
    """
    Get artifacts for the given parsed file tree
    """
    pre_order = [i for i in tree.pre_order() if isinstance(i, lib2to3.pytree.Leaf)]

    sep = next(
        filter(lambda i: i.type == lib2to3.pgen2.token.NEWLINE, pre_order),
        lib2to3.pytree.Leaf(lib2to3.pgen2.token.NEWLINE, "\n"),
    ).value

    first_node = next(
        filter(
            lambda i: (
                i.type not in {lib2to3.pgen2.token.NEWLINE, lib2to3.pgen2.token.STRING}
            ),
            pre_order,
        )
    )

    # node prefix includes comments hence to calculate first line
    # we need to get node lineno and subtract number of
    # non-empty lines in the prefix
    non_empty_offset = len(
        list(
            itertools.takewhile(
                lambda i: i.strip()
                and not any(c in i for c in ENCODING_COMMENTS)
                and not i.strip().startswith("#!"),
                reversed(first_node.prefix.splitlines()),
            )
        )
    )
    # there could be empty lines immeately before comments
    # so we need to offset those as well
    empty_offset = len(
        list(
            itertools.takewhile(
                lambda i: not i.strip(),
                list(reversed(first_node.prefix.splitlines()))[non_empty_offset:],
            )
        )
    )

    first_line = (
        first_node.get_lineno()
        - 1  # lines are 1-index based
        - non_empty_offset
        - empty_offset
    )

    artifacts = Artifacts(sep=sep, first_line=max(first_line, 0))
    plugin_hooks.inject_tree_artifacts(artifacts=artifacts, tree=tree, text=text)
    return artifacts


def get_text_artifacts(text: str) -> Artifacts:
    """
    Get artifacts for the given file.
    """
    try:
        tree = parse_to_tree(text)
    except ParseError:
        return Artifacts(sep="\n", first_line=0)
    else:
        return get_tree_artifacts(tree, text)


class Leaf:
    """
    Wrapper around ``lib2to3.pytree.Leaf`` with useful shortcuts for parsing imports
    """

    IMPORT_FROM_COMBINABLE_TYPES: typing.Set[int] = {
        lib2to3.pgen2.token.NAME,
        lib2to3.pgen2.token.DOT,
        lib2to3.pgen2.token.STAR,
    }
    IMPORT_COMBINABLE_TYPES: typing.Set[int] = IMPORT_FROM_COMBINABLE_TYPES | {
        lib2to3.pgen2.token.COMMA
    }

    def __init__(
        self, leaf: lib2to3.pytree.Leaf, combinable_types: typing.Set[int] = None
    ):
        self.leaf: lib2to3.pytree.Leaf = leaf
        self.previous: typing.Union["Leaf", None]
        self.next: typing.Union["Leaf", None]

        self.type: int = self.leaf.type
        self.prefix: str = self.leaf.prefix
        self.value: str = self.leaf.value

        self.combinable_types: typing.Set[
            int
        ] = combinable_types or self.IMPORT_COMBINABLE_TYPES
        self.combinable_value: str = f" {self.leaf.value} " if self.leaf.value in {
            "as"
        } else self.leaf.value

        self.prefix_lines: typing.List[str] = self.prefix.splitlines()
        self.relevant_prefix_lines: typing.List[str] = list(
            reversed(
                [
                    l
                    for l in itertools.takewhile(
                        lambda k: not is_comment_encoding(k),
                        reversed(self.prefix.splitlines()),
                    )
                ]
            )
        )

        # literally immediate comments before node itself
        # in other words consecutive comments without
        # any blank lines in between them
        self.immediate_comments: typing.List[str] = list(
            reversed(
                [
                    normalize_comment(l)
                    for l in itertools.takewhile(
                        lambda k: is_comment(k), reversed(self.relevant_prefix_lines)
                    )
                ]
            )
        )

        self.enumerated_comments: typing.List[typing.Tuple[int, str]] = list(
            reversed(
                [
                    (i, normalize_comment(l))
                    for i, l in itertools.takewhile(
                        lambda k: not is_comment_encoding(k[1]),
                        reversed(list(enumerate(self.relevant_prefix_lines))),
                    )
                    if is_comment(l)
                ]
            )
        )
        self.comments: typing.List[str] = [l for i, l in self.enumerated_comments]

    def get_lineno(self) -> int:
        return self.leaf.get_lineno() - 1

    @property
    def is_combinable(self) -> bool:
        return self.type in self.combinable_types and self.value not in {"import"}

    def until(
        self, until: typing.Union[typing.List[typing.Union[str, int]], None] = None
    ) -> typing.Iterable["Leaf"]:
        """
        Generate all next leaf nodes while ``until`` condition is not met if given
        """
        node = self
        yield node
        while node.next and (all(node.next != i for i in until) if until else True):
            node = node.next
            yield node

    def split_until(
        self, sep: typing.List[typing.Union[str, int]]
    ) -> typing.Iterable[typing.List["Leaf"]]:
        """
        Split all next leafs by separator if split contains any combinable leafs
        """
        node = self
        while node:
            elements = list(node.until(sep))
            if any(i.is_combinable for i in elements):
                yield elements
            node = getattr(elements[-1].next, "next", None)

    def __eq__(self, other: object) -> bool:
        return self.type == other if isinstance(other, int) else self.value == other

    def __hash__(self) -> int:
        return id(self)

    def __repr__(self) -> str:
        return repr(self.leaf)


class Statement:
    """
    Wrapper around ``lib2to3.pytree.Node`` which handles file top-level statements
    """

    IMPORT_TYPES = {
        v
        for k, v in vars(lib2to3.pygram.python_symbols).items()
        if k.startswith("import")
    }

    def __init__(self, node: lib2to3.pytree.Node):
        self.node: lib2to3.pytree.Node = node

    @property
    def is_import(self) -> bool:
        return (
            self.node.type == lib2to3.pygram.python_symbols.simple_stmt
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
                i for i in self.node.pre_order() if isinstance(i, lib2to3.pytree.Leaf)
            ]

            combinable_types_mapping = {
                "from": Leaf.IMPORT_FROM_COMBINABLE_TYPES,
                "import": Leaf.IMPORT_COMBINABLE_TYPES,
            }
            combinable_types = combinable_types_mapping[_leafs[0].value]

            self._leafs = [Leaf(i, combinable_types=combinable_types) for i in _leafs]
            for i, _leaf in enumerate(self._leafs):
                _leaf.previous = self._leafs[i - 1] if i else None
                _leaf.next = self._leafs[i + 1] if i < len(self._leafs) - 1 else None

            return self._leafs

    @property
    def standalone_comments(self) -> typing.List[str]:
        return self.leafs[0].immediate_comments

    @property
    def line_numbers(self) -> typing.List[int]:
        line_numbers = {l.get_lineno() for l in self.leafs}
        return list(
            range(
                min(line_numbers) - len(self.standalone_comments), max(line_numbers) + 1
            )
        )

    @property
    def nodes(self) -> typing.List[Leaf]:
        return self.leafs[1:]


def parse_imports_from_import_statement(
    statement: Statement, strict: bool = False
) -> typing.Iterable[ImportStatement]:
    """
    Parse import statements
    """
    # import statement standalone_comments are the only possible possible
    standalone_comments = statement.standalone_comments

    # import statement has only inline comments
    # in all nodes within a statment so we can immediatly
    # add all of them to inline_comments
    inline_comments = list(itertools.chain(*[i.comments for i in statement.nodes]))

    # much simpler to do splits on string and since
    # comments are already handled this is much simpler route
    # compared to inspecting tree structure
    # go string parsing!
    data = "".join(n.combinable_value for n in statement.nodes if n.is_combinable)

    # loop to handle multiple comma delimited imports
    for imp in data.split(","):
        leafs: typing.List[ImportLeaf] = []
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
            line_numbers=statement.line_numbers,
            standalone_comments=standalone_comments,
            inline_comments=inline_comments,
            strict=strict,
        )


def parse_imports_from_import_from_statement(
    statement: Statement, strict: bool = False
) -> typing.Iterable[ImportStatement]:
    leafs: typing.List[ImportLeaf] = []

    # import statement standalone_comments are the only possibility
    standalone_comments = statement.standalone_comments
    inline_comments: typing.List[str] = []

    stem_nodes = list(statement.nodes[0].until(["import"]))
    stem = "".join(n.combinable_value for n in stem_nodes if n.is_combinable)

    # get all nodes after "import" node
    # and split them by comma to hand parse multiple import leafs
    last_node: Leaf
    for leaf_nodes in (
        stem_nodes[-1].next.split_until([",", ")"]) if stem_nodes[-1].next else []
    ):
        last_node = leaf_nodes[-1]
        leaf_nodes_enumerated = {v: k for k, v in enumerate(leaf_nodes)}

        imp_standalone_comments: typing.List[str] = []
        imp_inline_comments: typing.List[str] = []
        imp_statement_comments: typing.List[str] = []

        combinable_nodes = {
            v: k for k, v in enumerate(leaf_nodes_enumerated) if v.is_combinable
        }

        # instead of parsing nodes to get leaf leaf name as as_name
        # much simpler to simply parse a string
        complete_name = "".join(n.combinable_value for n in combinable_nodes)
        name: str
        as_name: typing.Optional[str]
        try:
            name, as_name = complete_name.split(" as ")
        except ValueError:
            name, as_name = complete_name, None

        # find all comments within leaf nodes
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
            v: k for k, v in enumerate(leaf_nodes_enumerated) if v.comments
        }
        for inode, node in enumerate(comment_nodes):
            for ci, comment in node.enumerated_comments:
                target = (
                    imp_standalone_comments
                    if node.is_combinable
                    else imp_inline_comments
                )

                if any(j in comment for j in STATEMENT_COMMENTS):
                    target = imp_statement_comments

                if (
                    inode == 0
                    and ci == 0
                    and comment_nodes[node] <= max(combinable_nodes.values())
                ):
                    target = leafs[-1].inline_comments if leafs else inline_comments

                    if any(j in comment for j in STATEMENT_COMMENTS):
                        target = (
                            leafs[-1].statement_comments if leafs else inline_comments
                        )

                target.append(comment)

        leafs.append(
            ImportLeaf(
                name=name,
                as_name=as_name,
                standalone_comments=imp_standalone_comments,
                inline_comments=imp_inline_comments,
                statement_comments=imp_statement_comments,
                strict=strict,
            )
        )

    # possible to have more nodes after all leafs are exhausted
    # e.g. if last leaf is a comma
    # so those comments need to be accounted for
    # there are 2 possibilities
    # 1) comment belongs to last leaf
    # 2) unless comment is after newline or ")" in which case belogs
    #    as statement inline comment
    imp_rest_nodes = {
        v: k for k, v in enumerate(getattr(last_node.next, "until", list)())
    }
    try:
        par_index = list(imp_rest_nodes).index(")")
    except ValueError:
        par_index = len(imp_rest_nodes)
    for inode, node in enumerate(i for i in imp_rest_nodes if i.comments):
        for ci, comment in node.enumerated_comments:
            target = inline_comments

            if inode == 0 and ci == 0 and imp_rest_nodes[node] <= par_index:
                target = leafs[-1].inline_comments
                if any(j in comment for j in STATEMENT_COMMENTS):
                    target = leafs[-1].statement_comments

            target.append(comment)

    yield ImportStatement(
        stem=stem,
        as_name=None,
        leafs=leafs,
        line_numbers=statement.line_numbers,
        standalone_comments=standalone_comments,
        inline_comments=inline_comments,
        strict=strict,
    )


def parse_imports_from_tree(
    tree: lib2to3.pytree.Node, strict: bool = False
) -> typing.Iterable[ImportStatement]:
    """
    Parse imports from given tree
    """
    for statement in filter(
        lambda i: i.is_import,
        (Statement(i) for i in tree.children if isinstance(i, lib2to3.pytree.Node)),
    ):
        if statement.import_type == "import":
            yield from parse_imports_from_import_statement(
                statement=statement, strict=strict
            )

        else:
            yield from parse_imports_from_import_from_statement(
                statement=statement, strict=strict
            )


def parse_imports(text: str, strict: bool = False) -> typing.Iterable[ImportStatement]:
    """
    Parse imports from given code text
    """
    tree = parse_to_tree(text)
    return parse_imports_from_tree(tree, strict=strict)
