import tinycss2

from stretchable.style.core import Length, Ratio, Style, to_css_prop_name
from stretchable.style.props import Overflow


def test_inits():
    """Test the various methods of initializing a Style instance."""

    args = [
        "margin: 10px; aspect-ratio: 1.5; overflow-x: scroll;",
        {
            "margin": "10px",
            "aspect_ratio": 1.5,
            "overflow-x": Overflow.SCROLL,
        },
    ]
    args.append(tinycss2.parse_declaration_list(args[0]))

    # From plain css
    for arg in args:
        style = Style(arg)
        assert style["margin-left"] == Length(10, "px")
        assert style["aspect-ratio"] == Ratio(1.5, 1)
        assert style["overflow-x"] == Overflow.SCROLL


def test_warn_unrecognized():
    """Test that warning is logged if an unrecognized property or a property
    with an invalid/unrecognized value is encountered."""

    # TODO: implementation
    ...


def test_prop_names():
    assert to_css_prop_name("aspect_ratio") == "aspect-ratio"
    assert to_css_prop_name("aspectRatio") == "aspect-ratio"
    assert to_css_prop_name("AspectRatio") == "aspect-ratio"
    assert to_css_prop_name("aspect-ratio") == "aspect-ratio"
    assert to_css_prop_name(" aspect-ratio ") == "aspect-ratio"


def test_margin():
    # Test assignment of properties from shorthand
    css = "margin: 10px 20px 30px 40px;"
    style = Style(css)
    assert style["margin-top"] == Length(10, "px")
    assert style["margin-right"] == Length(20, "px")
    assert style["margin-bottom"] == Length(30, "px")
    assert style["margin-left"] == Length(40, "px")

    # Test property order/override
    css = "margin: 10px; margin-left: 5px;"
    style = Style(css)
    assert style["margin-left"] == Length(5, "px")
    css = "margin-left: 5px; margin: 10px;"
    style = Style(css)
    assert style["margin-left"] == Length(10, "px")

    # Test initial value for unassigned property
    css = "margin-left: 5px;"
    style = Style(css)
    assert style["margin-left"] == Length(5, "px")
    assert style["margin-top"] == Length(0, "px")


def test_aspect_ratio():
    css = "aspect-ratio: 1 / 5;"
    style = Style(css)
    assert style["aspect-ratio"] == Ratio(1, 5)

    css = "aspect-ratio: 2.5;"
    style = Style(css)
    assert style["aspect-ratio"] == Ratio(5, 2)

    css = "aspect-ratio: 3 auto;"
    style = Style(css)
    assert style["aspect-ratio"] == Ratio(3, auto=True)

    css = "aspect-ratio: auto 3/2;"
    style = Style(css)
    assert style["aspect-ratio"] == Ratio(3, 2, True)


def test_overflow():
    from stretchable.style.props import Overflow

    css = "overflow: hidden;"
    style = Style(css)
    assert style["overflow-x"] == Overflow.HIDDEN
    assert style["overflow-y"] == Overflow.HIDDEN

    css = "overflow: hidden visible;"
    style = Style(css)
    assert style["overflow-x"] == Overflow.HIDDEN
    assert style["overflow-y"] == Overflow.VISIBLE

    css = "overflow-x: hidden;"
    style = Style(css)
    assert style["overflow-x"] == Overflow.HIDDEN
    assert style["overflow-y"] == Overflow.VISIBLE


def test_grid_row_column():
    # TODO: Test grid-row, grid-column
    pass


"""

TODO:

- Add tests
- Properties.get_value_str() method, support:
    Specific property including defaults (with shortest possible string, eg. use shorthand if available)
    Specific property with sparse value (only values that are not default)
    All effective properties with sparse values, eg. without duplicates
- Add more properties to properties.xml
- Parsing of ratio, keyword, functions, etc.
- To Taffy

"""
