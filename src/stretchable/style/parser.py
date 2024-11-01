import logging
import re
from enum import Enum
from typing import Callable, Union

from tinycss2.ast import (
    Declaration,
    DimensionToken,
    IdentToken,
    LiteralToken,
    Node,
    PercentageToken,
    WhitespaceToken,
)

from .geometry.length import LengthPointsPercent, LengthPointsPercentAuto
from .geometry.rect import Rect, RectPointsPercent, RectPointsPercentAuto
from .props import (
    AlignContent,
    AlignItems,
    AlignSelf,
    BoxSizing,
    Display,
    Edge,
    FlexDirection,
    FlexWrap,
    GridAutoFlow,
    JustifyContent,
    JustifyItems,
    JustifySelf,
    Overflow,
    Position,
)

logging.basicConfig(format="%(levelname)s:%(name)s:%(message)s")
logger = logging.getLogger(__name__)

"""

Use the concept of a property adapter, which takes:
  a range of declarations (can include CSS shorthands)
and returns:
  a dictionary of properties with parsed values (may be one property or multiple)

For example:
  margin: 10px; margin-left: 5px; margin-right: 5px
returns:
  margin: RectPointsPercentAuto(10, 5, 10, 5)

The adapter should define:
    which CSS property names it can handle
    

The caller will consume the recognized CSS properties and pass it to the adapter.

The adapter will return a dictionary of properties with parsed values.

Use an instanced class because it enables using the same adapter for different
properties, fx margin, border and padding

TODO: Consider if prefix should be supported by the base class and base class contain a default implementation of parse_single

"""

Token = Union[DimensionToken, PercentageToken]

__PROP_NAME_PATTERN = re.compile(r"(?<!^)(?=[A-Z])")


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

    return __PROP_NAME_PATTERN.sub("-", name.strip()).lower().replace("_", "-")


def strip(
    tokens: list[Node],
    *,
    predicate: Callable[[Node], bool] = lambda node: node
    and isinstance(node, WhitespaceToken),
    leading: bool = True,
    internal: bool = False,
    trailing: bool = True,
) -> list[Node]:
    """
    Strip leading, internal and/or trailing tokens matching a given predicate
    (default: WhitespaceTokens) from the given list of tokens.
    """

    if not leading and not internal and not trailing:
        return tokens.copy()

    s = [predicate(node) for node in tokens]
    j, k = None, None
    for i, v in enumerate(s):
        if v:
            continue
        if j is None:
            j = i
        k = i

    def include(i: int) -> bool:
        if i < j:
            if leading:
                return False
        elif i > k:
            if trailing:
                return False
        else:
            if internal and s[i]:
                return False
        return True

    if j is None:
        return []
    return [node for i, node in enumerate(tokens) if include(i)]


def lstrip(tokens: list[Node]) -> list[Node]:
    """Strips whitespace from the beginning of a list of tokens."""
    return strip(tokens, trailing=False)


def rstrip(tokens: list[Node]) -> list[Node]:
    """Strips whitespace from the end of a list of nodes."""
    return strip(tokens, leading=False)


def split(
    tokens: list[Node],
    *,
    sep: str = None,
    predicate: Callable[[Node], bool] = lambda node: node
    and isinstance(node, WhitespaceToken),
    maxsplit: int = -1,
) -> list[list[Node]]:
    """
    Splits a list of tokens by a specified separator given as a string literal
    or determined by a predicate method (default: WhitespaceTokens).

    TODO: Multiple consecutive separators should be treated as a single separator.
    """

    if maxsplit == 0:
        raise ValueError("`maxsplit` cannot be 0")

    if sep is not None:
        if predicate is not None:
            raise ValueError("Provide either `sep` or `predicate`, not both")
        predicate = (
            lambda node: node and isinstance(node, LiteralToken) and node.value == sep
        )

    if predicate is None:
        raise ValueError("Separator is required, either via `sep` or `predicate`")

    sets, cur = [], []
    for node in tokens:
        if (maxsplit < 0 or len(sets) < maxsplit) and predicate(node):
            sets.append(cur)
            cur = []
        else:
            cur.append(node)
    sets.append(cur)

    return sets


class Adapter:
    def __init__(self, resolvers: list[str, callable]):
        self._resolvers = resolvers
        self._recognized_props = [name for name, _ in resolvers]

    @property
    def recognized_props(self) -> list[str]:
        return self._recognized_props

    def _parse(self, decl: list[Declaration]) -> dict[str, object]:
        # First use resolvers to parse the values
        values: dict[str, list[Token]] = {}
        remaining: set[str] = set({d.lower_name for d in decl})
        for name, resolver in self._resolvers:
            for d in decl:
                if d.lower_name != name:
                    continue
                _values = resolver(name, d.value)
                values.update(_values)
                remaining.remove(name)

        # Check that all properties have been resolved
        if remaining:
            raise ValueError(f"Unrecognized properties: {remaining}")

        # Then use parse_value to convert the parsed values to the correct type
        for prop, value in values.items():
            values[prop] = self.parse_value(prop, value)

        return values

    def parse_value(self, name: str, value: list[Token]) -> object | None:
        raise NotImplementedError("parse_value must be implemented in subclass")

    def parse(self, decl: list[Declaration]) -> dict[str, object]:
        raise NotImplementedError("parse must be implemented in subclass")


class EnumAdapter(Adapter):
    def __init__(self, enum: type[Enum], name: str = None):
        self._enum = enum
        self._name = name or to_css_prop_name(enum.__name__)
        if self._name == "overflow":
            resolvers = [
                (
                    self._name,
                    lambda name, value: {"overflow-x": value, "overflow-y": value},
                ),
                (f"{self._name}-x", lambda name, value: {name: value}),
                (f"{self._name}-y", lambda name, value: {name: value}),
            ]
            pass
        else:
            resolvers = [(self._name, lambda name, value: {name: value})]
        super().__init__(resolvers)

    def parse_value(self, name: str, value: list[Token]) -> Enum:
        if not value:
            raise ValueError(f"Missing value for {name}")
        value = strip(value)
        if len(value) != 1:
            raise ValueError(f"Invalid value for {name}")
        value = value[0]
        if not isinstance(value, IdentToken):
            raise ValueError(f"Unsupported token {value}")
        try:
            return self._enum[value.value.upper().replace("-", "_").replace(" ", "_")]
        except KeyError:
            raise ValueError(f"Invalid value {value.value} for {name}")

    def parse(self, decl: list[Declaration]) -> dict[str, object]:
        values = super()._parse(decl)
        return {name.replace("-", "_"): values[name] for name in values}


class RectAdapter(Adapter):
    def __init__(self, prop: str, *, prefix: str = None, labels: list[str] = None):
        # Check if prop is supported
        if prop not in self._prop_map:
            raise ValueError(f"RectAdapter cannot be used for {prop}")

        self._prop = prop
        self._prefix = prefix
        self._labels = labels or ["top", "right", "bottom", "left"]

        # Define resolvers
        resolvers = []
        if self._prefix:
            resolvers.append((self._prefix, self.parse_shorthand))
        for label in self._labels:
            resolvers.append(
                (
                    f"{self._prefix}-{label}" if self._prefix else label,
                    self.parse_single,
                )
            )

        super().__init__(resolvers)

    _prop_map: dict[str, Rect] = {
        "inset": RectPointsPercentAuto,
        "margin": RectPointsPercentAuto,
        "padding": RectPointsPercent,
        "border": RectPointsPercent,
    }

    def parse_shorthand(
        self,
        name,
        value: list[Token],
    ) -> dict[str, Union[LengthPointsPercent, LengthPointsPercentAuto]]:
        values = split(strip(value))
        n = len(values)
        if n == 1:
            return {label: values[0] for label in self._labels}
        elif n == 2:
            return {
                self._labels[0]: values[0],
                self._labels[1]: values[1],
                self._labels[2]: values[0],
                self._labels[3]: values[1],
            }
        elif n == 3:
            return {
                self._labels[0]: values[0],
                self._labels[1]: values[1],
                self._labels[2]: values[2],
                self._labels[3]: values[1],
            }
        elif n == 4:
            return {label: value for label, value in zip(self._labels, values)}
        else:
            raise ValueError(f"Invalid number of values for {name}")

    def parse_single(
        self,
        name: str,
        value: list[Token],
    ) -> dict[str, Union[LengthPointsPercent, LengthPointsPercentAuto]]:
        return {name.removeprefix(f"{self._prefix}-"): value}

    def parse_value(
        self,
        name: str,
        value: list[Token],
    ) -> Union[LengthPointsPercent, LengthPointsPercentAuto, None]:
        #   how to support relative/alternative units (fx em, rem, etc.), via a hook?
        #   how to provide context for the hook method?
        if not value:
            return None
        value = strip(value)
        if len(value) != 1:
            raise ValueError(f"Invalid value for {name}")
        value = value[0]
        if isinstance(value, PercentageToken):
            return LengthPointsPercent.percent(value.value / 100)
        if not isinstance(value, DimensionToken):
            raise ValueError(f"Unsupported token {value}")
        if value.unit == "auto":
            if self._edge != Edge.MARGIN:
                raise ValueError(f"Unsupported unit {value.unit} for {self._prefix}")
            return LengthPointsPercentAuto.auto()
        if value.unit in ("px", "pt", "", None):
            return LengthPointsPercent.points(value.value)
        raise ValueError(f"Unsupported unit {value.unit}")

    def parse(self, decl: list[Declaration]) -> dict[str, object]:
        values = super()._parse(decl)
        return {self._prop: self._prop_map[self._prop](**values)}


class Adapters:
    def __init__(self, *adapters: Adapter):
        # Check for duplicate properties
        props: set[str] = set()
        for adapter in adapters:
            for prop in adapter.recognized_props:
                if prop in props:
                    raise ValueError(f"Duplicate property {prop}")
                props.add(prop)

        # Store the adapters
        self._adapters = adapters

    def get_props(self, decl: list[Declaration]) -> dict[str, object]:
        """
        Parse a list of declarations and return a dictionary of properties with parsed values.

        :param decl: Declarations
        :type decl: list[Declaration]
        :return: Properties with parsed values
        :rtype: dict[str, object]
        """

        props: dict[str, object] = {}
        decls: dict[str, Declaration] = {d.lower_name: d for d in decl}
        for adapter in self._adapters:
            _decls = []
            for prop in adapter.recognized_props:
                if prop in decls:
                    _decls.append(decls.pop(prop))
            if _decls:
                props.update(adapter.parse(_decls))

        for d in decls:
            logger.warning(f"Property {d} not recognized")

        return props


adapters = Adapters(
    *[
        RectAdapter(prop, prefix=prop if prop != "inset" else None)
        for prop in ("inset", "margin", "border", "padding")
    ],
    *[
        EnumAdapter(enum)
        for enum in (
            Display,
            BoxSizing,
            Overflow,
            JustifyContent,
            JustifyItems,
            JustifySelf,
            AlignItems,
            AlignSelf,
            AlignContent,
            FlexDirection,
            Position,
            FlexWrap,
            GridAutoFlow,
        )
    ],
)
