import tinycss2

from stretchable.style.parser import lstrip, rstrip, strip


def test_strip():
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
                leading=leading,
                internal=internal,
                trailing=trailing,
            )
        )
        assert actual == expected


def test_lrstrip():
    source = "  left: 10px;  "
    nodes = tinycss2.parse_component_value_list(source, skip_comments=True)

    # lstrip()
    actual = tinycss2.serialize(lstrip(nodes))
    expected = source.lstrip()
    assert actual == expected

    # rstrip()
    actual = tinycss2.serialize(rstrip(nodes))
    expected = source.rstrip()
    assert actual == expected
