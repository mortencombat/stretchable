import tinycss2

from stretchable.style.parser import strip


def test_strip():
    def is_stripped(node: tinycss2.ast.Node) -> bool:
        return node and isinstance(node, tinycss2.ast.WhitespaceToken)

    css: str = " grid-column: 3 / 2 "
    fixtures = [
        (True, False, False, css, css.lstrip()),
        (False, False, True, css, css.rstrip()),
        (False, True, False, css, " grid-column:3/2 "),
        (True, False, True, "   ", ""),
    ]

    for leading, internal, trailing, source, expected in fixtures:
        nodes = tinycss2.parse_component_value_list(source, skip_comments=True)
        actual = tinycss2.serialize(
            strip(
                nodes,
                predicate=is_stripped,
                leading=leading,
                internal=internal,
                trailing=trailing,
            )
        )
        assert actual == expected
