# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import lib2to3
from importanize.parser import (
    get_text_artifacts,
    parse_imports,
    normalize_comment,
    Leaf,
    Artifacts,
)
from importanize.statements import ImportLeaf, ImportStatement


def test_artifacts() -> None:
    assert Artifacts.default().first_line == 0
    assert Artifacts.default().sep == "\n"


def test_comment() -> None:
    assert normalize_comment("# foo") == "foo"
    assert normalize_comment("#foo") == "foo"
    assert normalize_comment("foo") == "foo"


def test_leaf() -> None:
    leaf = Leaf(lib2to3.pytree.Leaf(lib2to3.pgen2.token.NEWLINE, "\n"))
    assert repr(leaf) == "Leaf(4, '\\n')"


def test_get_text_artifacts_sep() -> None:
    assert get_text_artifacts("Hello\nWorld\n").sep == "\n"
    assert get_text_artifacts("Hello\r\nWorld\n").sep == "\r\n"
    assert get_text_artifacts("Hello").sep == "\n"


def test_get_text_artifacts_first_line() -> None:
    assert get_text_artifacts("").first_line == 0
    assert get_text_artifacts("if").first_line == 0

    assert get_text_artifacts("foo = bar").first_line == 0
    assert get_text_artifacts("# -*- coding: utf-8 -*-").first_line == 1
    assert get_text_artifacts("#!/bin/python").first_line == 1
    assert get_text_artifacts("#comment").first_line == 0
    assert get_text_artifacts("'''docstring here'''").first_line == 1
    assert get_text_artifacts("'''\nmultiline docstring here\n'''").first_line == 3

    assert get_text_artifacts("\n\nfoo = bar").first_line == 0
    assert get_text_artifacts("\n  \nfoo = bar").first_line == 0
    assert get_text_artifacts("# -*- coding: utf-8 -*-\n\nfoo = bar").first_line == 1
    assert (
        get_text_artifacts(
            "#!/bin/python\n# -*- coding: utf-8 -*-\n\nfoo = bar"
        ).first_line
        == 2
    )
    assert get_text_artifacts("'''docstring here'''\n\nfoo = bar").first_line == 1
    assert (
        get_text_artifacts("'''\nmultiline docstring here\n'''\n\nfoo=bar").first_line
        == 3
    )

    assert (
        get_text_artifacts(
            "# -*- coding: utf-8 -*-\n'''docstring here'''\nfoo = bar"
        ).first_line
        == 2
    )
    assert (
        get_text_artifacts(
            "# -*- coding: utf-8 -*-\n'''docstring here'''\nfoo = bar"
        ).first_line
        == 2
    )
    assert (
        get_text_artifacts(
            "# -*- coding: utf-8 -*-\n'''\nmultiline docstring here\n'''\n\nfoo = bar"
        ).first_line
        == 4
    )
    assert (
        get_text_artifacts(
            "#!/bin/python\n# -*- coding: utf-8 -*-\n'''\nmultiline docstring here\n'''\n\nfoo = bar"
        ).first_line
        == 5
    )


def test_parse_imports_no_imports() -> None:
    assert list(parse_imports("''' docstring here '''", strict=True)) == []


def test_parse_imports_import_to_from_import() -> None:
    assert (
        list(parse_imports("import a.b as b", strict=True))[0].as_string()
        == "from a import b"
    )
    assert (
        list(parse_imports("import a.b as c", strict=True))[0].as_string()
        == "from a import b as c"
    )
    assert (
        list(parse_imports("import a.b.c.d as e", strict=True))[0].as_string()
        == "from a.b.c import d as e"
    )


def test_parse_imports_import() -> None:
    assert list(parse_imports("import a", strict=True)) == [
        ImportStatement("a", strict=True)
    ]
    assert list(parse_imports("import a.b", strict=True)) == [
        ImportStatement("a.b", strict=True)
    ]
    assert list(parse_imports("import a.\\\nb", strict=True)) == [
        ImportStatement("a.b", strict=True)
    ]
    assert list(parse_imports("import a as a", strict=True)) == [
        ImportStatement("a", strict=True)
    ]
    assert list(parse_imports("import a as b", strict=True)) == [
        ImportStatement("a", "b", strict=True)
    ]
    assert list(parse_imports("import a\\\nas b", strict=True)) == [
        ImportStatement("a", "b", strict=True)
    ]
    assert list(parse_imports("import a, b", strict=True)) == [
        ImportStatement("a", strict=True),
        ImportStatement("b", strict=True),
    ]
    assert list(parse_imports("import a,\\\nb", strict=True)) == [
        ImportStatement("a", strict=True),
        ImportStatement("b", strict=True),
    ]
    assert list(parse_imports("import a, b as c", strict=True)) == [
        ImportStatement("a", strict=True),
        ImportStatement("b", "c", strict=True),
    ]

    assert list(parse_imports("import a #noqa", strict=True)) == [
        ImportStatement("a", inline_comments=["noqa"], strict=True)
    ]
    assert list(parse_imports("#noqa\nimport a", strict=True)) == [
        ImportStatement("a", standalone_comments=["noqa"], strict=True)
    ]
    assert list(parse_imports("#irrelevant\n\n#comment\nimport a", strict=True)) == [
        ImportStatement("a", standalone_comments=["comment"], strict=True)
    ]
    assert list(
        parse_imports("# -*- coding: utf-8 -*-\n#noqa\nimport a", strict=True)
    ) == [ImportStatement("a", standalone_comments=["noqa"], strict=True)]
    assert list(parse_imports("#!/bin/python\n#noqa\nimport a", strict=True)) == [
        ImportStatement("a", standalone_comments=["noqa"], strict=True)
    ]
    assert list(parse_imports("'''docstring'''\n#noqa\nimport a", strict=True)) == [
        ImportStatement("a", standalone_comments=["noqa"], strict=True)
    ]
    assert list(parse_imports("#comment\n#noqa\nimport a", strict=True)) == [
        ImportStatement("a", standalone_comments=["comment", "noqa"], strict=True)
    ]
    assert list(parse_imports("#hello\nimport a # noqa", strict=True)) == [
        ImportStatement(
            "a", standalone_comments=["hello"], inline_comments=["noqa"], strict=True
        )
    ]
    assert list(parse_imports("#hello\nimport a # comment", strict=True)) == [
        ImportStatement(
            "a", standalone_comments=["hello"], inline_comments=["comment"], strict=True
        )
    ]


def test_parse_imports_from_import() -> None:
    assert list(parse_imports("from .a import b", strict=True)) == [
        ImportStatement(".a", leafs=[ImportLeaf("b", strict=True)], strict=True)
    ]
    assert list(parse_imports("from a import b", strict=True)) == [
        ImportStatement("a", leafs=[ImportLeaf("b", strict=True)], strict=True)
    ]
    assert list(parse_imports("from a.b import c", strict=True)) == [
        ImportStatement("a.b", leafs=[ImportLeaf("c", strict=True)], strict=True)
    ]
    assert list(parse_imports("from a.b import c as d", strict=True)) == [
        ImportStatement("a.b", leafs=[ImportLeaf("c", "d", strict=True)], strict=True)
    ]
    assert list(parse_imports("from a.b import c,\\\nd", strict=True)) == [
        ImportStatement(
            "a.b",
            leafs=[ImportLeaf("c", strict=True), ImportLeaf("d", strict=True)],
            strict=True,
        )
    ]
    assert list(parse_imports("from a.b\\\nimport c", strict=True)) == [
        ImportStatement("a.b", leafs=[ImportLeaf("c", strict=True)], strict=True)
    ]
    assert list(parse_imports("from a.b import (c)", strict=True)) == [
        ImportStatement("a.b", leafs=[ImportLeaf("c", strict=True)], strict=True)
    ]
    assert list(parse_imports("from a.b import (c, d)", strict=True)) == [
        ImportStatement(
            "a.b",
            leafs=[ImportLeaf("c", strict=True), ImportLeaf("d", strict=True)],
            strict=True,
        )
    ]
    assert list(parse_imports("from a.b import (c, d,)", strict=True)) == [
        ImportStatement(
            "a.b",
            leafs=[ImportLeaf("c", strict=True), ImportLeaf("d", strict=True)],
            strict=True,
        )
    ]
    assert list(parse_imports("from a.b import (c, d as d)", strict=True)) == [
        ImportStatement(
            "a.b",
            leafs=[ImportLeaf("c", strict=True), ImportLeaf("d", strict=True)],
            strict=True,
        )
    ]
    assert list(parse_imports("from a.b import (c, d as e)", strict=True)) == [
        ImportStatement(
            "a.b",
            leafs=[ImportLeaf("c", strict=True), ImportLeaf("d", "e", strict=True)],
            strict=True,
        )
    ]
    assert list(parse_imports("from a.b import \\\n(c, d,)", strict=True)) == [
        ImportStatement(
            "a.b",
            leafs=[ImportLeaf("c", strict=True), ImportLeaf("d", strict=True)],
            strict=True,
        )
    ]
    assert list(parse_imports("from a.b import (\nc,\nd,\n)", strict=True)) == [
        ImportStatement(
            "a.b",
            leafs=[ImportLeaf("c", strict=True), ImportLeaf("d", strict=True)],
            strict=True,
        )
    ]

    assert list(parse_imports("#comment\nfrom a.b import c", strict=True)) == [
        ImportStatement(
            "a.b",
            leafs=[ImportLeaf("c", strict=True)],
            standalone_comments=["comment"],
            strict=True,
        )
    ]
    assert list(parse_imports("from a.b import c # noqa", strict=True)) == [
        ImportStatement(
            "a.b",
            leafs=[ImportLeaf("c", strict=True)],
            inline_comments=["noqa"],
            strict=True,
        )
    ]
    assert list(parse_imports("#comment\nfrom a.b import c # noqa", strict=True)) == [
        ImportStatement(
            "a.b",
            leafs=[ImportLeaf("c", strict=True)],
            standalone_comments=["comment"],
            inline_comments=["noqa"],
            strict=True,
        )
    ]
    assert list(
        parse_imports("#comment\nfrom a.b import c # noqa comment", strict=True)
    ) == [
        ImportStatement(
            "a.b",
            leafs=[ImportLeaf("c", strict=True)],
            standalone_comments=["comment"],
            inline_comments=["noqa comment"],
            strict=True,
        )
    ]
    assert list(parse_imports("from a.b import c # comment", strict=True)) == [
        ImportStatement(
            "a.b",
            leafs=[ImportLeaf("c", inline_comments=["comment"], strict=True)],
            strict=True,
        )
    ]
    assert list(
        parse_imports("from a.b import (#comment\nc,#inline\nd#noqa\n)", strict=True)
    ) == [
        ImportStatement(
            "a.b",
            leafs=[
                ImportLeaf("c", inline_comments=["inline"], strict=True),
                ImportLeaf("d", strict=True),
            ],
            inline_comments=["comment", "noqa"],
            strict=True,
        )
    ]
    assert list(
        parse_imports("from a.b import (\n#comment\nc,#inline\nd#noqa\n)", strict=True)
    ) == [
        ImportStatement(
            "a.b",
            leafs=[
                ImportLeaf(
                    "c",
                    standalone_comments=["comment"],
                    inline_comments=["inline"],
                    strict=True,
                ),
                ImportLeaf("d", strict=True),
            ],
            inline_comments=["noqa"],
            strict=True,
        )
    ]
    assert list(
        parse_imports("from a.b import (\n#comment\nc,#inline\nd,#noqa\n)", strict=True)
    ) == [
        ImportStatement(
            "a.b",
            leafs=[
                ImportLeaf(
                    "c",
                    standalone_comments=["comment"],
                    inline_comments=["inline"],
                    strict=True,
                ),
                ImportLeaf("d", strict=True),
            ],
            inline_comments=["noqa"],
            strict=True,
        )
    ]
    assert list(
        parse_imports(
            "from a.b import (\n#comment\nc,#inline\n#another\nd#noqa\n)", strict=True
        )
    ) == [
        ImportStatement(
            "a.b",
            leafs=[
                ImportLeaf(
                    "c",
                    standalone_comments=["comment"],
                    inline_comments=["inline"],
                    strict=True,
                ),
                ImportLeaf("d", standalone_comments=["another"], strict=True),
            ],
            inline_comments=["noqa"],
            strict=True,
        )
    ]
    assert list(
        parse_imports(
            "from a.b import (\n#comment\nc,#inline\n  #another\n  d#noqa\n)",
            strict=True,
        )
    ) == [
        ImportStatement(
            "a.b",
            leafs=[
                ImportLeaf(
                    "c",
                    standalone_comments=["comment"],
                    inline_comments=["inline"],
                    strict=True,
                ),
                ImportLeaf("d", standalone_comments=["another"], strict=True),
            ],
            inline_comments=["noqa"],
            strict=True,
        )
    ]
    assert list(
        parse_imports(
            "from a.b import (\n#comment\nc,#inline\nd,#noqa\n)#end", strict=True
        )
    ) == [
        ImportStatement(
            "a.b",
            leafs=[
                ImportLeaf(
                    "c",
                    standalone_comments=["comment"],
                    inline_comments=["inline"],
                    strict=True,
                ),
                ImportLeaf("d", strict=True),
            ],
            inline_comments=["noqa", "end"],
            strict=True,
        )
    ]
    assert list(
        parse_imports(
            "from a.b import (\n#comment\nc,#inline\nd,\n#statement\n)#end", strict=True
        )
    ) == [
        ImportStatement(
            "a.b",
            leafs=[
                ImportLeaf(
                    "c",
                    standalone_comments=["comment"],
                    inline_comments=["inline"],
                    strict=True,
                ),
                ImportLeaf("d", strict=True),
            ],
            inline_comments=["statement", "end"],
            strict=True,
        )
    ]
    assert list(
        parse_imports(
            "from a.b import (\n#comment\nc,#inline\nd,#noqa\n#statement\n)#end",
            strict=True,
        )
    ) == [
        ImportStatement(
            "a.b",
            leafs=[
                ImportLeaf(
                    "c",
                    standalone_comments=["comment"],
                    inline_comments=["inline"],
                    strict=True,
                ),
                ImportLeaf("d", strict=True),
            ],
            inline_comments=["noqa", "statement", "end"],
            strict=True,
        )
    ]
    assert list(
        parse_imports(
            "from a.b import (\n#comment\nc,#inline\nd,#foo\n#statement\n)#end",
            strict=True,
        )
    ) == [
        ImportStatement(
            "a.b",
            leafs=[
                ImportLeaf(
                    "c",
                    standalone_comments=["comment"],
                    inline_comments=["inline"],
                    strict=True,
                ),
                ImportLeaf("d", inline_comments=["foo"], strict=True),
            ],
            inline_comments=["statement", "end"],
            strict=True,
        )
    ]
    assert list(
        parse_imports(
            "from a.b import (#generic\n#comment\nc,#inline\nd,#foo\n#statement\n)#end",
            strict=True,
        )
    ) == [
        ImportStatement(
            "a.b",
            leafs=[
                ImportLeaf(
                    "c",
                    standalone_comments=["comment"],
                    inline_comments=["inline"],
                    strict=True,
                ),
                ImportLeaf("d", inline_comments=["foo"], strict=True),
            ],
            inline_comments=["generic", "statement", "end"],
            strict=True,
        )
    ]
