from __future__ import annotations

import importlib
import os
import re
from dataclasses import dataclass, field
from enum import Enum, Flag, IntEnum, auto
from pathlib import Path
from typing import Any, Callable, Iterable, Protocol

import tinycss2
from lxml import etree

"""
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

_MODULE_OBJ_PATTERN = re.compile(
    r"((?:[a-zA-Z_][a-zA-Z0-9_]+\.?)+)\.([a-zA-Z_][a-zA-Z0-9_]+)"
)
_PROP_RECT_NAME_PATTERN = re.compile(r"([a-z]+-)?(top|right|bottom|left)(-[a-z]+)?")
_PROP_RECT_EDGES = ("top", "right", "bottom", "left")
_PROP_NAME_PATTERN = re.compile(r"(?<!^)(?=[A-Z])")

"""
NOTE: 

We need to be able to determine in what form properties should be passed into Taffy.

For example, scrollbar-width is keyword|length, but Taffy takes this as a float (eg. length).
Some properties may be possible to infer automatically, based on the type(s) supported.
"""

# Properties that should be passed to Taffy
# TODO: this should be defined in properties.xml, use export="true" to include
_PROPS_TAFFY = {
    # Layout/sizing mode
    "display",
    "box-sizing",
    # Overflow
    "overflow-x",
    "overflow-y",
    # "scrollbar-width",
    # # Position
    # "position",
    # "inset",
    # # Alignment
    # "gap",
    "align-items",
    "justify-items",
    "align-self",
    "justify-self",
    "align-content",
    "justify-content",
    # # Spacing
    # "padding",
    # "border-width",
    # "margin",
    # # Size
    # "size",
    # "min-size",
    # "max-size",
    # "aspect-ratio",
    # # Flex
    "flex-wrap",
    "flex-direction",
    "flex-grow",
    "flex-shrink",
    # "flex-basis",
    # # Grid, container
    # "grid-template-rows",
    # "grid-template-columns",
    # "grid-auto-rows",
    # "grid-auto-columns",
    # "grid-auto-flow",
    # # Grid, child
    # "grid-row",
    # "grid-column",
}

# Property adapters for properties passed to Taffy
# These adapters, when present, will be used before applying the default adapter.
# The default adapter will take care of unit scaling, etc.
# NOTE: many cases could be handled by get_length_value, but this is a more general solution
_PROPS_TAFFY_ADAPTERS: dict[str, Callable[[Value], Any]] = {
    # "scrollbar-width": lambda v: v.value if isinstance(v, Length) else v.value,
}


def to_css_prop_name(name: str) -> str:
    """
    Returns `name` converted to CSS naming convention, for example:
    `aspectRatio` -> `aspect-ratio`
    `aspect_ratio` -> `aspect-ratio`
    `AspectRatio` -> `aspect-ratio`
    `ASPECT_RATIO` -> `aspect-ratio`

    :param name: CSS property name
    :type name: str
    :return: property name converted to CSS naming convention
    :rtype: str
    """

    return _PROP_NAME_PATTERN.sub("-", name.strip()).lower().replace("_", "-")


class PercentageUnit:
    """Represents a CSS unit for <percentage> values."""

    def __mul__(self, value: int | float) -> Percentage:
        if isinstance(value, (int, float)):
            return Percentage(value)
        else:
            raise TypeError("Invalid value type for <percentage>")

    def __rmul__(self, value: int | float) -> Percentage:
        return self.__mul__(value)

    def __str__(self):
        return "%"


class LengthUnit:
    """Represents a CSS unit for <length> values.

    Multiplying an int/float value with a unit returns a Length instance.
    Multiplying any other types raises a TypeError.
    """

    def __init__(self, unit: str):
        self.unit = unit

    def __mul__(self, value: int | float) -> Length:
        if isinstance(value, (int, float)):
            return Length(value, self.unit)
        else:
            raise TypeError("Invalid value type for <length>")

    def __rmul__(self, value: int | float) -> Length:
        return self.__mul__(value)

    def __str__(self):
        return self.unit


class PropertyBindingError(Exception):
    pass


@dataclass(frozen=True, slots=True)
class Value:
    """This is a base class for all value types. It represents a single value of a CSS property."""

    class Type(Flag):
        KEYWORD = auto()
        LENGTH = auto()
        PERCENTAGE = auto()
        NUMBER = auto()
        COLOR = auto()
        RATIO = auto()
        FUNCTION = auto()

    type: Value.Type
    nodes: list[tinycss2.ast.Node] = field(default=None, kw_only=True)

    def __str__(self):
        if self.nodes:
            return tinycss2.serialize(self.nodes)

    def _to_taffy(
        self, prop: str, context: object
    ) -> int | float | dict[str, int | float]:
        raise NotImplementedError


@dataclass(frozen=True, slots=True)
class GridLine(Value):
    """Represents a <grid-line> value in CSS."""

    type: Value.Type = field(init=False, default=Value.Type.NUMBER)
    is_span: bool = field(default=False, kw_only=True)
    value: int = field(default=None, kw_only=True)

    @staticmethod
    def auto() -> GridLine:
        return GridLine()

    @staticmethod
    def index(index: int) -> GridLine:
        return GridLine(value=index)

    @staticmethod
    def span(span: int) -> GridLine:
        return GridLine(is_span=True, value=span)

    @property
    def is_auto(self) -> bool:
        return self.value is None

    def __str__(self):
        if self.nodes:
            return super(GridLine, self).__str__()
        raise NotImplementedError

    def __eq__(self, value):
        raise NotImplementedError

    def _to_taffy(
        self, prop: str, context: object
    ) -> int | float | dict[str, int | float]:
        raise NotImplementedError


@dataclass(frozen=True, slots=True)
class Length(Value):
    """Represents a <length> value in CSS."""

    type: Value.Type = field(init=False, default=Value.Type.LENGTH)
    value: float
    unit: str = None

    def __eq__(self, value) -> bool:
        if value is None:
            return False
        if isinstance(value, Length):
            return self.value == value.value and (
                self.unit == value.unit or value.value == 0
            )
        if isinstance(value, Number):
            return self.value == value.value and (self.unit is None or value.value == 0)
        return False

    def __str__(self):
        if self.nodes:
            return super(Length, self).__str__()
        if self.unit:
            return f"{self.value}{self.unit}"
        return str(self.value)

    def _to_taffy(
        self, prop: str, context: object
    ) -> int | float | dict[str, int | float]:
        return dict(dim=1, value=properties.get_length(prop, self, context))


@dataclass(frozen=True, slots=True)
class Number(Value):
    """Represents a <number> value in CSS."""

    type: Value.Type = field(init=False, default=Value.Type.NUMBER)
    value: float | int

    def __eq__(self, value) -> bool:
        if value is None:
            return False
        if isinstance(value, Number):
            return self.value == value.value
        if isinstance(value, Length):
            return self.value == value.value and (
                value.unit is None or value.value == 0
            )
        return False

    def __str__(self):
        if self.nodes:
            return super(Number, self).__str__()
        return str(self.value)

    def _to_taffy(
        self, prop: str, context: object
    ) -> int | float | dict[str, int | float]:
        return properties.get_length(prop, self, context)


@dataclass(frozen=True, slots=True)
class Percentage(Value):
    """Represents a <percentage> value in CSS."""

    type: Value.Type = field(init=False, default=Value.Type.PERCENTAGE)
    value: float

    def __str__(self):
        if self.nodes:
            return super(Percentage, self).__str__()
        return f"{self.value}%"


@dataclass(frozen=True, slots=True)
class Ratio(Value):
    """Represents a <ratio> value in CSS."""

    type: Value.Type = field(init=False, default=Value.Type.RATIO)
    width: float = None
    height: float = 1
    auto: bool = False

    def __eq__(self, value) -> bool:
        if value is None or not isinstance(value, Ratio):
            return False
        return (
            self.auto == value.auto
            and round(self.width / self.height - value.width / value.height, 3) == 0
        )

    def __str__(self):
        if self.nodes:
            return super(Ratio, self).__str__()
        s = "auto" if self.auto else ""
        if self.width:
            if s:
                s += " "
            s += f"{self.width} / {self.height}"
        return s


@dataclass(frozen=True, slots=True)
class Color(Value):
    """Represents a <percentage> value in CSS."""

    type: Value.Type = field(init=False, default=Value.Type.COLOR)
    value: tuple[float]


@dataclass(frozen=True, slots=True)
class Keyword(Value):
    """Represents a <keyword> value in CSS."""

    type: Value.Type = field(init=False, default=Value.Type.KEYWORD)
    value: str | Enum

    def __eq__(self, value) -> bool:
        if value is None:
            return False
        if isinstance(value, Keyword):
            return self.value == value.value
        return self.value == value

    def _to_taffy(
        self, prop: str, context: object
    ) -> int | float | dict[str, int | float]:
        if isinstance(self.value, IntEnum):
            return self.value.value
        raise PropertyBindingError(
            f"Keyword value cannot automatically be bound to Taffy: {self.value}"
        )


@dataclass(frozen=True, slots=True)
class Function(Value):
    """Represents a <function> value in CSS."""

    type: Value.Type = field(init=False, default=Value.Type.FUNCTION)


class Parser(Protocol):
    def parse(self, value: list[tinycss2.ast.Node]) -> Value:
        """Parses a list of nodes (tokens) and returns a Value instance. Consumed
        nodes are removed from the input `value`.

        Any leading whitespace tokens in value should be removed before calling
        this method.

        Raises ValueError if the value is not valid.
        """

        ...


@dataclass(frozen=True, slots=True)
class LengthParser:
    """This is a parser for <length> values in CSS."""

    def parse(self, value: list[tinycss2.ast.Node]) -> Length:
        if not value:
            raise ValueError("No value provided")
        elif value[0].type == "number":
            v = value.pop(0)
            return Length(v.value, nodes=[v])
        elif value[0].type == "dimension":
            v = value.pop(0)
            return Length(v.value, v.unit, nodes=[v])
        else:
            raise ValueError(
                f"Length value must be a number or a dimension: {value[0]}"
            )


@dataclass(frozen=True, slots=True)
class PercentageParser:
    """This is a parser for <percentage> values in CSS."""

    def parse(self, value: list[tinycss2.ast.Node]) -> Percentage:
        if not value:
            raise ValueError("No value provided")
        elif value[0].type == "percentage":
            v = value.pop(0)
            return Percentage(v.value, nodes=[v])
        else:
            raise ValueError(f"Percentage value must be a percentage: {value[0]}")


@dataclass(frozen=True, slots=True)
class NumberParser(Parser):
    """This is a parser for <number> values in CSS."""

    def parse(self, value: list[tinycss2.ast.Node]) -> Number:
        if not value:
            raise ValueError("No value provided")
        elif value[0].type == "number":
            v = value.pop(0)
            return Number(v.value, nodes=[v])
        else:
            raise ValueError(f"Number value must be a number: {value[0]}")


@dataclass(frozen=True, slots=True)
class KeywordParser:
    """This is a parser for keyword values in CSS."""

    keywords: Iterable[str] | Enum = None

    def parse(self, value: list[tinycss2.ast.Node]) -> Keyword:
        if not value:
            raise ValueError("No value provided")
        elif value[0].type == "ident":
            val = value[0].value
            if self.keywords:
                if issubclass(self.keywords, Enum):
                    val_name = val.replace("-", "_").upper()
                    if val_name in self.keywords.__members__:
                        val = self.keywords[val_name]
                    elif val in self.keywords._value2member_map_:
                        val = self.keywords._value2member_map_[val]
                    else:
                        raise ValueError(f"Invalid keyword: {val}")
                elif val not in self.keywords:
                    raise ValueError(f"Invalid keyword: {val}")
            v = value.pop(0)
            return Keyword(val, nodes=[v])
        else:
            raise ValueError(f"Keyword value must be an ident: {value[0]}")


@dataclass(frozen=True, slots=True)
class FunctionParser:
    """This is a parser for function values in CSS."""

    functions: Iterable[str] | Enum = None


@dataclass(frozen=True, slots=True)
class RatioParser:
    """This is a parser for <ratio> values in CSS."""

    def parse(self, value: list[tinycss2.ast.Node]) -> Ratio:
        """Parses a ratio value in the form of <width> / <height> [auto]."""

        # Default attributes
        auto, width, height = False, None, 1

        # NOTE: we cannot pop values until we are sure that we have a valid match

        # Recognized tokens/patterns:
        #   <IdentToken "auto">
        #   <NumberToken>[<WhitespaceToken>][<LiteralToken "/">[<WhitespaceToken>]<NumberToken>]
        section = 0
        for i, token in enumerate(value):
            # Ignore leading whitespace tokens
            if token.type == "whitespace":
                continue

            if (
                (section == 0 or section == 1)
                and not auto
                and token.type == "ident"
                and token.value == "auto"
            ):
                auto = True
                if section == 1:
                    break
            elif section == 0 and not width and token.type == "number":
                width = token.value
                section = 1
            elif section == 1 and token.type == "literal" and token.value == "/":
                section = 2
            elif section == 2 and token.type == "number":
                height = token.value
                section = 0
            else:
                break

        if not auto and not width:
            raise ValueError("Value not recognized as a ratio")

        # Remove consumed tokens
        for c in range(i + 1):
            value.pop(0)

        v = Ratio(width=width, height=height, auto=auto)

        return v


@dataclass(frozen=True, slots=True)
class ColorParser:
    """This is a parser for <color> values in CSS."""

    def parse(self, value: list[tinycss2.ast.Node]) -> Color:
        raise NotImplementedError


@dataclass(frozen=True, slots=True)
class Property:
    """This represents a specific CSS property (not a shorthand)."""

    name: str
    parsers: tuple[Parser]
    initial: object = None
    array: bool = None
    default: str = None
    export: bool = True
    inactive: bool = field(default=False, init=False)

    def parse(
        self, value: list[tinycss2.ast.Node], *, raise_remaining: bool = True
    ) -> Value | list[Value]:
        """Parses a list of nodes (tokens) and returns a Value instance or list
        of Value instances in case of array properties.

        Consumed nodes are removed from the input `value`.

        If the property cannot consume the full input value and raise_remaining
        is True, a ValueError is raised.
        """

        if not isinstance(value, list):
            value = [value]
        values: list[Value] = []
        while value:
            # Ignore leading whitespace tokens
            while value and value[0].type == "whitespace":
                value.pop(0)
            if not value:
                break

            if values and not self.array:
                if not raise_remaining:
                    return values[0]
                raise ValueError("Multiple values not allowed")

            # Parse the value
            for p in self.parsers:
                try:
                    v = p.parse(value)
                    values.append(v)
                    break
                except ValueError:
                    v = None
                    continue
            if not v:
                raise ValueError(f"Invalid value: {value[0]}")

        if not values:
            raise ValueError("No value provided")

        return values if self.array else values[0]

    @staticmethod
    def from_xml_node(node: etree.Element):
        """Parse a property from an XML node and return a Property instance."""

        def get_attrib(
            node: etree.Element, name: str, *, inherit: bool = True
        ) -> str | None:
            """
            Get an attribute from an XML node.

            If not present on node and inherit == True, traverse up the element
            tree and get attribute from nearest parent element. Return None if
            it does not exist on node or parents.
            """

            while node is not None:
                if name in node.attrib:
                    return node.attrib[name]
                if not inherit:
                    return None
                node = node.getparent()

        name = node.tag

        # Add type parsers
        types = get_attrib(node, "type")
        if not types:
            raise ValueError(f"Property {name}: Missing type attribute")
        parsers = []
        keywords: list[str] | Enum = None
        functions: list[str] = None
        for t in types.split("|"):
            t = t.strip()
            parser = None

            if t == "length":
                parser = LengthParser()
            elif t == "percentage":
                parser = PercentageParser()
            elif t == "number":
                parser = NumberParser()
            elif t == "color":
                parser = ColorParser()
            elif t == "ratio":
                parser = RatioParser()
            elif t == "auto":
                if keywords is None:
                    keywords = []
                elif not isinstance(keywords, list):
                    raise ValueError(
                        f"Property {name}: auto type cannot be combined with an Enum-based keywords-list"
                    )
                keywords.append("auto")
            elif t == "keyword":
                if keywords is None:
                    keywords = []
                kws = get_attrib(node, "keywords")
                if kws:
                    m = _MODULE_OBJ_PATTERN.match(kws)
                    if m:
                        if keywords:
                            raise ValueError(
                                f"Property {name}: cannot combine Enum-based keywords with a list of keywords"
                            )

                        # module = importlib.import_module(m.group(1))
                        importlib.invalidate_caches()

                        module = importlib.import_module(m.group(1))
                        if m.group(2) not in module.__dict__:
                            try:
                                module = importlib.import_module(
                                    f"{m.group(1)}.__init__"
                                )
                            except ModuleNotFoundError:
                                module = None
                            if not module or m.group(2) not in module.__dict__:
                                raise ValueError(
                                    f"Property {name}: Enum {m.group(2)} not found in module {m.group(1)}"
                                )
                        keywords = module.__dict__[m.group(2)]
                    else:
                        keywords.extend([kw.strip() for kw in kws.split(",")])
            elif t == "function":
                if functions is None:
                    functions = []
                funcs = get_attrib(node, "functions")
                if funcs:
                    keywords.extend([func.strip() for func in funcs.split(",")])
            else:
                raise ValueError(f"Property {name}: Invalid type {t}")

            if parser:
                if parser in parsers:
                    raise ValueError(f"Property {name}: Duplicate type {t}")
                parsers.append(parser)

        if keywords:
            parsers.append(KeywordParser(keywords))

        if functions:
            parsers.append(FunctionParser(functions))

        initial = get_attrib(node, "initial")
        default = get_attrib(node, "default")
        export = get_attrib(node, "export", inherit=False)
        export = export is None or not export.strip().lower() == "false"

        return Property(
            name,
            parsers=tuple(parsers),
            initial=initial,
            default=default,
            export=export,
        )


@dataclass(frozen=True, slots=True)
class ShorthandProperty:
    """This represents a shorthand CSS property."""

    name: str
    properties: list[ShorthandProperty | Property]
    ordered: bool = False
    optional: bool = False
    inactive: bool = False
    rect: bool = field(init=False, default=False)

    def __post_init__(self):
        object.__setattr__(self, "rect", self._is_rect())

    def _is_rect(self) -> bool:
        """Determines if the shorthand property is a rect (shorthand for properties corresponding to 4 edges)."""

        if len(self.properties) != 4:
            return False

        p = self.properties[0]

        # Ensure prop name matches pattern and determine prop name prefix and suffix, if any
        # Prefix and suffix are optional and can be any lowercase string, but
        # they must be identical for all 4 properties
        m = _PROP_RECT_NAME_PATTERN.match(p.name)
        if not m:
            return False
        prefix, suffix = m.group(1), m.group(3)
        if m.group(2) != _PROP_RECT_EDGES[0]:
            return False

        for i, prop in enumerate(self.properties):
            if not isinstance(prop, Property):
                return False

            if prop.array:
                return False

            if i > 0:
                m = _PROP_RECT_NAME_PATTERN.match(prop.name)
                if m.group(1) != prefix or m.group(3) != suffix:
                    return False
                if m.group(2) != _PROP_RECT_EDGES[i]:
                    return False
                if prop.parsers != p.parsers:
                    return False
                if prop.initial != p.initial:
                    return False

        return True

    def __hash__(self):
        return hash(self.name)

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

    def parse(self, value: list[tinycss2.ast.Node]) -> dict[str, Value | list[Value]]:
        """Parses a list of nodes (tokens) and returns a dict of properties and their values.

        Consumed nodes are removed from the input `value`.
        """

        """
        Based on properties, optional and ordered, check if value is valid/parseable
        If so, return a dict of "direct" properties and their values

        Procedure, if ordered is True:
            1. Walk through the properties in order, parsing values
            2. If a property cannot be parsed:
                a. If the property is optional, use the default value and continue
                b. If the property is not optional, raise an error

        Procedure, if ordered is False:
            1. Walk through the properties in order, parsing values
            2. If a property cannot be parsed, continue to the next property
            3. At the end, check if all required properties have been parsed

        If all properties are optional, check that at least one value is provided, otherwise raise an error
        """

        remaining = list(self.properties)
        values: dict[str, Value | list[Value]] = {}
        rect_values = []

        while value:
            while value and value[0].type == "whitespace":
                value.pop(0)
            if not value:
                break

            if self.rect:
                # Special handling for rect shorthands
                rect_values.append(
                    self.properties[0].parse(value, raise_remaining=False)
                )
            else:
                matched = False
                for prop in self.properties:
                    if prop not in remaining:
                        continue
                    try:
                        if isinstance(prop, Property):
                            v: Value | list[Value] = prop.parse(
                                value, raise_remaining=False
                            )
                            values[prop.name] = v
                        else:
                            vs: dict[str, Value | list[Value]] = prop.parse(value)
                            values.update(vs)
                        matched = True
                        remaining.remove(prop)
                    except ValueError:
                        if self.ordered and not prop.optional:
                            raise ValueError(f"Property {prop.name} not provided")
                if not matched:
                    break

        # Check that there are no remaining tokens
        while value and value[0].type == "whitespace":
            value.pop(0)
        if value:
            raise ValueError(f"Invalid value: {value[0]}")

        if self.rect:
            n = len(rect_values)
            if n == 1:
                values = {p.name: rect_values[0] for p in self.properties}
            elif n == 2:
                values = {
                    self.properties[0].name: rect_values[0],
                    self.properties[1].name: rect_values[1],
                    self.properties[2].name: rect_values[0],
                    self.properties[3].name: rect_values[1],
                }
            elif n == 3:
                values = {
                    self.properties[0].name: rect_values[0],
                    self.properties[1].name: rect_values[1],
                    self.properties[2].name: rect_values[2],
                    self.properties[3].name: rect_values[1],
                }
            elif n == 4:
                values = {self.properties[i].name: v for i, v in enumerate(rect_values)}
            elif n > 4:
                raise ValueError("Too many values provided")
            else:
                raise ValueError("No value provided")

        else:
            # If any properties have not been specified, check if a default is specified
            for prop in remaining:
                if prop.default:
                    if prop.default not in values:
                        raise ValueError(f"Property {prop.name} not provided")
                    values[prop.name] = values[prop.default]

            # Check that any remaining properties have initial values specified
            if any(prop.initial is None for prop in remaining):
                raise ValueError(
                    f"Not all properties provided, missing {', '.join(p.name for p in remaining if p.initial is None)}"
                )

        # Check that at least one value was provided
        if not values:
            raise ValueError("No value provided")

        return values

    @staticmethod
    def from_xml_node(node: etree.Element):
        """Parse a shorthand property from an XML node and return a ShorthandProperty instance."""

        name = node.tag
        props = []
        for element in node.iterchildren(tag=etree.Element):
            props.append(
                (
                    ShorthandProperty.from_xml_node(element)
                    if len(element) > 0
                    else Property.from_xml_node(element)
                )
            )

        inactive = "inactive" in node.attrib and node.attrib["inactive"] == "true"

        return ShorthandProperty(name, properties=props, inactive=inactive)


# margin


def value_to_length(
    prop: str,
    value: Value,
    context: object,
    unit_scales: dict[str, float] = None,
    keywords: dict[str | Enum, float] = None,
) -> float:
    """Converts a Value instance to a length value.

    If the Value cannot be converted to a length, a ValueError is raised.
    """

    if isinstance(value, Length):
        if value.unit is not None:
            if not unit_scales or value.unit not in unit_scales:
                raise ValueError(f"Length unit not recognized: {value}")
            return value.value * unit_scales[value.unit]
        return value.value
    elif isinstance(value, Number):
        return value.value
    elif isinstance(value, Keyword):
        if not keywords or value.value not in keywords:
            raise ValueError(f"Keyword value not recognized: {value}")
        return keywords[value.value]
    raise ValueError(f"Value cannot be converted to length: {value}")


class Properties:
    """This represents a collection of CSS properties."""

    __slots__ = ("_property_map", "_shorthands_map", "_get_length")

    def __init__(
        self,
        properties: list[Property | ShorthandProperty],
        get_length_delegate: Callable[[str, Value, object], float] = value_to_length,
    ):
        def make_maps(
            properties: list[Property | ShorthandProperty],
            shorthands: tuple[str] = None,
        ) -> None:
            for prop in properties:
                if not prop.inactive:
                    self._property_map[prop.name] = prop
                    if shorthands:
                        self._shorthands_map[prop.name] = shorthands
                if isinstance(prop, ShorthandProperty):
                    if prop.inactive:
                        sh = shorthands
                    elif shorthands:
                        sh = shorthands + (prop.name,)
                    else:
                        sh = (prop.name,)
                    make_maps(prop.properties, sh)

        # Generate maps to lookup properties by property name
        self._property_map = {}
        self._shorthands_map = {}
        make_maps(properties)

        self._get_length = get_length_delegate

    @property
    def properties(self) -> list[Property | ShorthandProperty]:
        return self._properties

    def __contains__(self, prop: str) -> bool:
        return prop in self._property_map

    def __getitem__(self, prop: str) -> Property | ShorthandProperty:
        if prop not in self._property_map:
            raise KeyError(f"Property not recognized: {prop}")
        return self._property_map[prop]

    def get_shorthands(self, prop: str) -> list[str]:
        if prop not in self._property_map:
            raise KeyError(f"Property not recognized: {prop}")
        return self._shorthands_map[prop] if prop in self._shorthands_map else []

    def get_related(self, prop: str) -> set[str]:
        """Get all related properties for a property.

        This includes all shorthands which can define this property, as well as
        all derived properties from those shorthands.
        """

        props: set[str] = {prop}

        for shorthand in self.get_shorthands(prop):
            props.add(shorthand)
            for p, sh in self._shorthands_map.items():
                if p in props:
                    continue
                if shorthand in sh:
                    props.add(p)

        return props

    def get_value(
        self, prop: str, decl: list[tinycss2.ast.Declaration], cache: dict[str, Value]
    ) -> Value:
        """Get the value of a property from a list of declarations, using
        applicable shorthands and storing all parsed values in cache."""

        if prop not in self._property_map:
            raise KeyError(f"Property not recognized: {prop}")
        if prop in cache:
            return cache[prop]

        # Get all related properties for the property, including self
        props = self.get_related(prop)

        # Order of declarations determines final value, so walk through all declarations in order, setting property values in cache
        for d in decl:
            if d.type != "declaration":
                continue
            if d.lower_name not in props:
                continue
            val = self[d.lower_name].parse(list(d.value))
            if isinstance(val, dict):
                cache.update(val)
            else:
                cache[d.lower_name] = val

        if prop not in cache and self[prop].initial is not None:
            # If property is not in cache, use initial value
            value = tinycss2.parse_component_value_list(self[prop].initial)
            cache[prop] = self[prop].parse(value)

        if prop not in cache:
            return None
        return cache[prop]

    @property
    def get_length_delegate(self) -> Callable[[str, Value, object], float]:
        return self._get_length

    @get_length_delegate.setter
    def get_length_delegate(self, delegate: Callable[[str, Value, object], float]):
        self._get_length = delegate

    def get_length(self, prop: str, value: Value, context: object) -> float:
        return self._get_length(prop, value, context)

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

        props = []
        for element in root.getroot().iterchildren(tag=etree.Element):
            props.append(
                ShorthandProperty.from_xml_node(element)
                if len(element) > 0
                else Property.from_xml_node(element)
            )

        return Properties(props)


class Style:
    __slots__ = ("_decl", "_input", "_values")

    def __init__(
        self, style: str | dict[str, str] | list[tinycss2.ast.Declaration] = None
    ):
        if style is None:
            self._decl = []
        elif isinstance(style, str):
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

    def __contains__(self, prop: str) -> bool:
        return prop in properties

    def __getitem__(self, prop: str) -> Value:
        return properties.get_value(prop, self._decl, self._values)

    def _to_taffy(self, context: object = None) -> dict[str, Any]:
        """Converts the style to a dict used for Taffy binding."""

        args: dict[str, Any] = {}

        """
        Does properties iterate over all properties including children?
        Should it be properties.properties?
        
        """

        for prop in properties:
            if not prop.export:
                continue
            value = self[prop.name]

            if prop.name in _PROPS_TAFFY_ADAPTERS:
                value = _PROPS_TAFFY_ADAPTERS[prop.name](value)

            """
            How to handle shorthand properties? size + rect should be mapped, other shorthands are not supported natively


            Determine processing based on prop.parsers:
                type(s)     action
                keyword     if value is an Enum, and Enum has an integer value, use that
                            otherwise raise PropertyBindingError
                ratio       if value is a Ratio, use value
                            raise PropertyBindingError if value.auto, since it is not supported by Taffy

            First determine ...


            """

            if value is not None:
                value = value._to_taffy(prop.name, context)

            args[prop.name.replace("-", "_")] = value

        return args


properties = Properties.from_file(
    Path(os.path.dirname(__file__)).joinpath("properties.xml")
)

pt = LengthUnit("pt")
pct = PercentageUnit()
