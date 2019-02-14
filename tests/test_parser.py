# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
from functools import partial

from importanize.parser import Comment, get_text_artifacts, parse_imports
from importanize.statements import ImportLeaf, ImportStatement


parse_imports = partial(parse_imports, strict=True)
ImportStatement = partial(ImportStatement, strict=True)
ImportLeaf = partial(ImportLeaf, strict=True)


def test_comment():
    assert Comment("# foo") == "foo"
    assert Comment("#foo") == "foo"
    assert Comment("foo") == "foo"


def test_get_text_artifacts():
    assert get_text_artifacts("Hello\nWorld\n")["sep"] == "\n"
    assert get_text_artifacts("Hello\r\nWorld\n")["sep"] == "\r\n"
    assert get_text_artifacts("Hello")["sep"] == "\n"


def test_parse_imports_no_imports():
    assert list(parse_imports("''' docstring here '''")) == []


def test_parse_imports_import_to_from_import():
    assert list(parse_imports("import .a"))[0].as_string() == "from . import a"
    assert (
        list(parse_imports("import ..a"))[0].as_string() == "from .. import a"
    )
    assert (
        list(parse_imports("import .a.b"))[0].as_string() == "from .a import b"
    )
    assert (
        list(parse_imports("import ..a.b"))[0].as_string()
        == "from ..a import b"
    )
    assert (
        list(parse_imports("import .a.b.c.d"))[0].as_string()
        == "from .a.b.c import d"
    )
    assert (
        list(parse_imports("import ..a.b.c.d"))[0].as_string()
        == "from ..a.b.c import d"
    )
    assert (
        list(parse_imports("import .a.b as c"))[0].as_string()
        == "from .a import b as c"
    )
    assert (
        list(parse_imports("import ..a.b as c"))[0].as_string()
        == "from ..a import b as c"
    )
    assert (
        list(parse_imports("import .a.b.c.d as e"))[0].as_string()
        == "from .a.b.c import d as e"
    )
    assert (
        list(parse_imports("import ..a.b.c.d as e"))[0].as_string()
        == "from ..a.b.c import d as e"
    )
    assert (
        list(parse_imports("import a.b as b"))[0].as_string()
        == "from a import b"
    )
    assert (
        list(parse_imports("import a.b as c"))[0].as_string()
        == "from a import b as c"
    )
    assert (
        list(parse_imports("import a.b.c.d as e"))[0].as_string()
        == "from a.b.c import d as e"
    )


def test_parse_imports_import():
    assert list(parse_imports("import a")) == [ImportStatement("a")]
    assert list(parse_imports("import a.b")) == [ImportStatement("a.b")]
    assert list(parse_imports("import a.\\\nb")) == [ImportStatement("a.b")]
    assert list(parse_imports("import a as a")) == [ImportStatement("a")]
    assert list(parse_imports("import a as b")) == [ImportStatement("a", "b")]
    assert list(parse_imports("import a\\\nas b")) == [
        ImportStatement("a", "b")
    ]
    assert list(parse_imports("import a, b")) == [
        ImportStatement("a"),
        ImportStatement("b"),
    ]
    assert list(parse_imports("import a,\\\nb")) == [
        ImportStatement("a"),
        ImportStatement("b"),
    ]
    assert list(parse_imports("import a, b as c")) == [
        ImportStatement("a"),
        ImportStatement("b", "c"),
    ]

    assert list(parse_imports("import a #noqa")) == [
        ImportStatement("a", inline_comments=["noqa"])
    ]
    assert list(parse_imports("#noqa\nimport a")) == [
        ImportStatement("a", pre_comments=["noqa"])
    ]
    assert list(parse_imports("'''docstring'''\n#noqa\nimport a")) == [
        ImportStatement("a", pre_comments=["noqa"])
    ]
    assert list(parse_imports("#comment\n#noqa\nimport a")) == [
        ImportStatement("a", pre_comments=["comment", "noqa"])
    ]
    assert list(parse_imports("#hello\nimport a # noqa")) == [
        ImportStatement("a", pre_comments=["hello"], inline_comments=["noqa"])
    ]
    assert list(parse_imports("#hello\nimport a # comment")) == [
        ImportStatement(
            "a", pre_comments=["hello"], inline_comments=["comment"]
        )
    ]


def test_parse_imports_from_import():
    assert list(parse_imports("from .a import b")) == [
        ImportStatement(".a", leafs=[ImportLeaf("b")])
    ]
    assert list(parse_imports("from a import b")) == [
        ImportStatement("a", leafs=[ImportLeaf("b")])
    ]
    assert list(parse_imports("from a.b import c")) == [
        ImportStatement("a.b", leafs=[ImportLeaf("c")])
    ]
    assert list(parse_imports("from a.b import c as d")) == [
        ImportStatement("a.b", leafs=[ImportLeaf("c", "d")])
    ]
    assert list(parse_imports("from a.b import c,\\\nd")) == [
        ImportStatement("a.b", leafs=[ImportLeaf("c"), ImportLeaf("d")])
    ]
    assert list(parse_imports("from a.b\\\nimport c")) == [
        ImportStatement("a.b", leafs=[ImportLeaf("c")])
    ]
    assert list(parse_imports("from a.b import (c)")) == [
        ImportStatement("a.b", leafs=[ImportLeaf("c")])
    ]
    assert list(parse_imports("from a.b import (c, d)")) == [
        ImportStatement("a.b", leafs=[ImportLeaf("c"), ImportLeaf("d")])
    ]
    assert list(parse_imports("from a.b import (c, d,)")) == [
        ImportStatement("a.b", leafs=[ImportLeaf("c"), ImportLeaf("d")])
    ]
    assert list(parse_imports("from a.b import (c, d as d)")) == [
        ImportStatement("a.b", leafs=[ImportLeaf("c"), ImportLeaf("d")])
    ]
    assert list(parse_imports("from a.b import (c, d as e)")) == [
        ImportStatement("a.b", leafs=[ImportLeaf("c"), ImportLeaf("d", "e")])
    ]
    assert list(parse_imports("from a.b import \\\n(c, d,)")) == [
        ImportStatement("a.b", leafs=[ImportLeaf("c"), ImportLeaf("d")])
    ]
    assert list(parse_imports("from a.b import (\nc,\nd,\n)")) == [
        ImportStatement("a.b", leafs=[ImportLeaf("c"), ImportLeaf("d")])
    ]

    assert list(parse_imports("#comment\nfrom a.b import c")) == [
        ImportStatement(
            "a.b", leafs=[ImportLeaf("c")], pre_comments=["comment"]
        )
    ]
    assert list(parse_imports("from a.b import c # noqa")) == [
        ImportStatement(
            "a.b", leafs=[ImportLeaf("c")], inline_comments=["noqa"]
        )
    ]
    assert list(parse_imports("#comment\nfrom a.b import c # noqa")) == [
        ImportStatement(
            "a.b",
            leafs=[ImportLeaf("c")],
            pre_comments=["comment"],
            inline_comments=["noqa"],
        )
    ]
    assert list(
        parse_imports("#comment\nfrom a.b import c # noqa comment")
    ) == [
        ImportStatement(
            "a.b",
            leafs=[ImportLeaf("c")],
            pre_comments=["comment"],
            inline_comments=["noqa comment"],
        )
    ]
    assert list(parse_imports("from a.b import c # comment")) == [
        ImportStatement(
            "a.b", leafs=[ImportLeaf("c", inline_comments=["comment"])]
        )
    ]
    assert list(
        parse_imports("from a.b import (\n#comment\nc,#inline\nd,#noqa\n)")
    ) == [
        ImportStatement(
            "a.b",
            leafs=[
                ImportLeaf(
                    "c", pre_comments=["comment"], inline_comments=["inline"]
                ),
                ImportLeaf("d"),
            ],
            inline_comments=["noqa"],
        )
    ]
    assert list(
        parse_imports("from a.b import (\n#comment\nc,#inline\nd#noqa\n)")
    ) == [
        ImportStatement(
            "a.b",
            leafs=[
                ImportLeaf(
                    "c", pre_comments=["comment"], inline_comments=["inline"]
                ),
                ImportLeaf("d"),
            ],
            inline_comments=["noqa"],
        )
    ]
    assert list(
        parse_imports("from a.b import (\n#comment\nc,#inline\nd,#noqa\n)#end")
    ) == [
        ImportStatement(
            "a.b",
            leafs=[
                ImportLeaf(
                    "c", pre_comments=["comment"], inline_comments=["inline"]
                ),
                ImportLeaf("d"),
            ],
            inline_comments=["noqa", "end"],
        )
    ]
