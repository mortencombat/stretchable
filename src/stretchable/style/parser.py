import logging
from typing import Callable, Union

from tinycss2.ast import (
    Declaration,
    DimensionToken,
    LiteralToken,
    Node,
    PercentageToken,
    WhitespaceToken,
)

from .geometry.length import LengthPointsPercent, LengthPointsPercentAuto
from .geometry.rect import Rect, RectPointsPercent, RectPointsPercentAuto
from .props import Edge

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

"""

Token = Union[DimensionToken, PercentageToken]


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

    def parse(self, decl: list[Declaration]) -> dict[str, object]:
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


class EdgeAdapter(Adapter):
    def __init__(self, edge: Edge):
        # Check if edge is supported
        if edge not in self._prop_map:
            raise ValueError(f"EdgeAdapter cannot be used for {edge}")
        self._edge = edge
        self._prefix = edge.name.lower()

        # Define resolvers
        super().__init__(
            [
                (self._prefix, self.parse_shorthand),
                (f"{self._prefix}-top", self.parse_single),
                (f"{self._prefix}-right", self.parse_single),
                (f"{self._prefix}-bottom", self.parse_single),
                (f"{self._prefix}-left", self.parse_single),
            ],
        )

    _prop_map: dict[Edge, Rect] = {
        Edge.MARGIN: RectPointsPercentAuto,
        Edge.PADDING: RectPointsPercent,
        Edge.BORDER: RectPointsPercent,
    }

    def parse_shorthand(
        self,
        name,
        value: list[Token],
    ) -> dict[str, Union[LengthPointsPercent, LengthPointsPercentAuto]]:
        values = split(strip(value))
        n = len(values)
        if n == 1:
            return dict(
                top=values[0], right=values[0], bottom=values[0], left=values[0]
            )
        elif n == 2:
            return dict(
                top=values[0], right=values[1], bottom=values[0], left=values[1]
            )
        elif n == 3:
            return dict(
                top=values[0], right=values[1], bottom=values[2], left=values[1]
            )
        elif n == 4:
            return dict(
                top=values[0], right=values[1], bottom=values[2], left=values[3]
            )
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
        values = super().parse(decl)
        return {self._prefix: self._prop_map[self._edge](**values)}


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


adapters = Adapters(*[EdgeAdapter(edge) for edge in Edge if edge != Edge.CONTENT])
