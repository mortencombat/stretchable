from pathlib import Path

import tinycss2
from lxml import etree

from .parser import to_css_prop_name

"""
Write out CSS shorthand/property tree for border and flexbox properties.

NOTE: we should require length values to have units, eg. they should become DimensionToken.
    ALTHOUGH, consider that lengths can be 0, which should be allowed without a unit.

NOTE: there should be a translator function that:
    converts DimensionToken to a float value, using a dictionary of unit scales.
    converts IdentToken

CSS token types:
    WhitespaceToken
    IdentToken                  used for keywords, fx:
                                    border-width: thin, medium, thick
                                    border-style: none, hidden, dotted, dashed, solid, double, groove, ridge, inset, outset
    StringToken
    LiteralToken                what is LiteralToken used for? flex grid 1 / 5?
    NumberToken                 number (int/float)
    NOTE: for some properties such as aspect-ratio, we need to be able to parse a fraction, eg. 16 / 9 (NumberToken, WhitespaceToken, LiteralToken, WhitespaceToken, NumberToken).
        This is called a <ratio> in CSS terminology.
    DimensionToken              length
    PercentageToken             percentage

border: <border-width> <border-style> <border-color>
        border-width: IdentToken | DimensionToken | NumberToken
        border-style: IdentToken
        border-color: IdentToken | FunctionToken

    border-width: <length> | thin | medium | thick

        border-top-width: <length> | thin | medium | thick

NOTE: the order of the properties in the border shorthand is not important, to be able to recognize border-style from border-color, we need to know the possible values for each property

gap: <row-gap> [<column-gap>]
    row-gap: <length/percentage>
    column-gap: <length/percentage>
    - If only one value is provided, it is used for both row and column gap


Style class:
- CSS props accessed using style['prop']
- Store input CSS props as a raw prop
    - Should be available as both str, dict[str, str] and list[Declaration]
- Consider lazy parsing

Property class:
- Represents a single CSS property
- Type of value is determined by the property, and will be checked/enforced by the property class
- Can be converted to a string

Shorthand class:
- Represents a shorthand property
- Consider using regex style parsing to split into individual properties

Separate Property and Shorthand class instances from actual values
"""


class Value:
    # TODO: Value should store the raw value as well? Could be useful for debugging and for converting back to CSS
    pass


class Length(Value):
    def __init__(self, value: float, unit: str = None):
        self.value = value
        self.unit = unit


class Percentage(Value):
    def __init__(self, value: float):
        self.value = value


class Number(Value):
    def __init__(self, value: float):
        self.value = value


class Keyword(Value):
    def __init__(self, value: str):
        self.value = value


class Function(Value):
    def __init__(self, value: str):
        self.value = value


class ValueType:
    """This represents a description of a single value of a CSS property."""

    def __init__(
        self,
        initial: object,
        *,
        keywords: list[str] = None,
        length: bool = False,
        percentage: bool = False,
        number: bool = False,
        ratio: bool = False,
        function: bool = False,
    ):
        self.initial = initial
        self.keywords = keywords
        self.length = length
        self.percentage = percentage
        self.number = number
        self.ratio = ratio
        self.function = function


class Property:
    """This represents a specific CSS property (not a shorthand)."""

    def __init__(
        self,
        name: str,
        value: ValueType,
        multiple: bool = False,
    ):
        self.name = name
        self.value = value

    def parse_value(self, value: list[tinycss2.ast.Node]) -> Value:
        # Attempts to parse the value and return a Value instance
        raise NotImplementedError


def optional(name: str, default: str | Value) -> tuple[str, str | Value]:
    return name, default


class ShorthandProperty:
    """This represents a shorthand CSS property."""

    def __init__(self, name: str, properties: list[str], *, ordered: bool = False):
        """
        It should be possible that properties are optional, and to define
        their default value if they are not provided. Note that default value
        could be a specific value, or a reference to another of the
        properties.
        NOTE: instead of list[Property], could be list[str] and then a dict[str, Property] to look up the Property instance
        One way of achieving this could be to have a method called optional, which could then be used like this:
            properties = [
                "row-gap",
                optional("column-gap", default="row-gap"),
            ]
        default could also be an instance of any of the Value classes, eg. Length(0, "px"), Percentage(0) or Keyword("auto").
        if default is a str, it will be taken as a reference to another property (should be one of the properties in the list)
        NOTE: this should be able to handle margin, border and padding shorthands with 1-4 values
            This could be by way of introducing a value type called Inset or Rect, which could be a list of 1-4 <length> or <length-percentage> values
        """

        self.name = name
        self.properties = properties
        self.ordered = ordered  # True if the order of properties is important

    def parse_values(self, value: list[tinycss2.ast.Node]) -> dict[Property, Value]:
        """
        Based on properties and strict, check if value is valid/parseable
        If so, return a dict of properties and their values

        This could perhaps be based on a regex-style matching of the value. How would it be handled if the order is not important?
        Note that WhitespaceToken can not be considered as a value separator, as it is used in the <ratio> value type.
        """

        raise NotImplementedError


# margin


class Properties:
    def __init__(self, properties: list[Property | ShorthandProperty]):
        self.properties = properties

    @staticmethod
    def from_file(filepath: str | Path):
        """Parse XML from `filepath` and return a Properties instance."""
        return Properties.from_xml(etree.parse(filepath))

    @staticmethod
    def from_string(xml: str):
        """Parse XML from `xml` string and return a Properties instance."""
        return Properties.from_xml(etree.fromstring(xml))

    @staticmethod
    def from_xml(root: etree.Element):
        """Parse CSS properties from an XML element and return a Properties instance."""

        def iter_children(node: etree.Element, shorthand: str = None):
            is_prop = True
            for child in node.iterchildren():
                iter_children(child, shorthand=node.tag)
                is_prop = False
            if is_prop:
                props[node.tag] = node.tag
            else:
                shorthands[node.tag] = node.tag
            to_parent[node.tag] = shorthand

        # Iterate over all elements in the XML tree to find properties (leaf nodes) and shorthands (non-leaf nodes)
        props: dict[str, Property] = {}
        shorthands: dict[str, ShorthandProperty] = {}
        to_parent: dict[str, str] = {}  # prop -> shorthand
        iter_children(root.getroot())

        raise NotImplementedError

    def parse(self, decl: list[tinycss2.ast.Declaration]) -> dict[Property, Value]:
        """Parses a list of declarations and returns a dict of properties and their values."""
        raise NotImplementedError


# TODO: there should be a class handling all these props and shorthands?

PROPS = [
    *[
        Property(
            f"margin-{side}",
            ValueType(
                initial=Length(0), keywords=["auto"], length=True, percentage=True
            ),
        )
        for side in ["top", "right", "bottom", "left"]
    ],
    ShorthandProperty(
        "margin", ["margin-top", "margin-right", "margin-bottom", "margin-left"]
    ),
]


class Style:
    def __init__(self, style: str | dict[str, str] | list[tinycss2.ast.Declaration]):
        if isinstance(style, str):
            self._decl = tinycss2.parse_blocks_contents(style, skip_comments=True)
        elif isinstance(style, dict):
            self._decl = [
                tinycss2.parse_one_declaration(
                    f"{to_css_prop_name(name)}: {value}", skip_comments=True
                )
                for name, value in style.items()
            ]
        elif isinstance(style, list):
            self._decl = style
        else:
            raise ValueError("Invalid style input")

        self._input = style
        self._values: dict[str, Value] = {}

    def __str__(self):
        """Returns the style as a CSS string.

        Only properties which are not the initial value should be included.
        """
        raise NotImplementedError

    def __getitem__(self, prop: str) -> Value:
        """
        This should look through self._decl to see if the property is set.
        If the property is not set, return the initial value.
        Cache the result (in self._values) and any other properties that may be parsed during this process (fx if prop is a shorthand).
        """

        if prop not in self._values:
            # Check if prop is recognized as a property or a shorthand, if not raise KeyError

            # Get value, caching this value and any other properties that may be parsed during this process
            raise NotImplementedError

        return self._values[prop]
