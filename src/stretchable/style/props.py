from enum import IntEnum
from typing import Self

from attrs import define, field, validators

# region Layout strategy/misc


class Display(IntEnum):
    NONE = 0
    FLEX = 1
    GRID = 2


class Overflow(IntEnum):
    VISIBLE = 0
    HIDDEN = 1
    SCROLL = 2


class Position(IntEnum):
    """
    The positioning strategy for this item.

    This controls both how the origin is determined for the `inset` property,
    and whether or not the item will be controlled by flexbox's layout
    algorithm.

    WARNING: this enum follows the behavior of [CSS's `position`
    property](https://developer.mozilla.org/en-US/docs/Web/CSS/position), which
    can be unintuitive.

    [MDN](https://developer.mozilla.org/en-US/docs/Web/CSS/position)
    """

    RELATIVE = 0
    ABSOLUTE = 1


# endregion

# region Alignment


class AlignItems(IntEnum):
    """
    Used to control how child nodes are aligned.
    For Flexbox it controls alignment in the cross axis.
    For Grid it controls alignment in the block axis.

    [MDN](https://developer.mozilla.org/en-US/docs/Web/CSS/align-items)
    """

    START = 0
    END = 1
    FLEX_START = 2
    FLEX_END = 3
    CENTER = 4
    BASELINE = 5
    STRETCH = 6


class JustifyItems(IntEnum):
    """
    Used to control how child nodes are aligned.
    Does not apply to Flexbox, and will be ignored if specified on a flex container.
    For Grid it controls alignment in the inline axis.

    [MDN](https://developer.mozilla.org/en-US/docs/Web/CSS/justify-items)
    """

    START = 0
    END = 1
    FLEX_START = 2
    FLEX_END = 3
    CENTER = 4
    BASELINE = 5
    STRETCH = 6


class AlignSelf(IntEnum):
    """
    Used to control how the specified nodes is aligned.
    Overrides the parent Node's `AlignItems` property.
    For Flexbox it controls alignment in the cross axis
    For Grid it controls alignment in the block axis

    [MDN](https://developer.mozilla.org/en-US/docs/Web/CSS/align-self)
    """

    START = 0
    END = 1
    FLEX_START = 2
    FLEX_END = 3
    CENTER = 4
    BASELINE = 5
    STRETCH = 6


class JustifySelf(IntEnum):
    """
    Used to control how the specified nodes is aligned.
    Overrides the parent Node's `JustifyItems` property.
    Does not apply to Flexbox, and will be ignored if specified on a flex child
    For Grid it controls alignment in the inline axis

    [MDN](https://developer.mozilla.org/en-US/docs/Web/CSS/justify-self)
    """

    START = 0
    END = 1
    FLEX_START = 2
    FLEX_END = 3
    CENTER = 4
    BASELINE = 5
    STRETCH = 6


class AlignContent(IntEnum):
    """
    Sets the distribution of space between and around content items
    For Flexbox it controls alignment in the cross axis
    For Grid it controls alignment in the block axis

    [MDN](https://developer.mozilla.org/en-US/docs/Web/CSS/align-content)
    """

    START = 0
    END = 1
    FLEX_START = 2
    FLEX_END = 3
    CENTER = 4
    STRETCH = 5
    SPACE_BETWEEN = 6
    SPACE_EVENLY = 7
    SPACE_AROUND = 8


class JustifyContent(IntEnum):
    """
    Sets the distribution of space between and around content items
    For Flexbox it controls alignment in the main axis
    For Grid it controls alignment in the inline axis

    [MDN](https://developer.mozilla.org/en-US/docs/Web/CSS/justify-content)
    """

    START = 0
    END = 1
    FLEX_START = 2
    FLEX_END = 3
    CENTER = 4
    STRETCH = 5
    SPACE_BETWEEN = 6
    SPACE_EVENLY = 7
    SPACE_AROUND = 8


# endregion

# region Flex


class FlexWrap(IntEnum):
    """
    Controls whether flex items are forced onto one line or can wrap onto
    multiple lines.

    [MDN](https://developer.mozilla.org/en-US/docs/Web/CSS/flex-wrap)
    """

    NO_WRAP = 0
    WRAP = 1
    WRAP_REVERSE = 2


class FlexDirection(IntEnum):
    """
    The direction of the flexbox layout main axis. There are always two
    perpendicular layout axes: main (or primary) and cross (or secondary).
    Adding items will cause them to be positioned adjacent to each other along
    the main axis. By varying this value throughout your tree, you can create
    complex axis-aligned layouts.

    Items are always aligned relative to the cross axis, and justified relative
    to the main axis.

    [MDN](https://developer.mozilla.org/en-US/docs/Web/CSS/flex-direction)
    """

    ROW = 0
    COLUMN = 1
    ROW_REVERSE = 2
    COLUMN_REVERSE = 3


# endregion

# region Grid


class GridAutoFlow(IntEnum):
    """
    Controls whether grid items are placed row-wise or column-wise, and whether
    the sparse or dense packing algorithm is used. The "dense" packing algorithm
    attempts to fill in holes earlier in the grid, if smaller items come up
    later. This may cause items to appear out-of-order, when doing so would fill
    in holes left by larger items.

    [MDN](https://developer.mozilla.org/en-US/docs/Web/CSS/grid-auto-flow)
    """

    ROW = 0
    COLUMN = 1
    ROW_DENSE = 2
    COLUMN_DENSE = 3


class GridIndexType(IntEnum):
    AUTO = 0
    INDEX = 1
    SPAN = 2


@define(frozen=True)
class GridIndex:
    value: int = None
    span: bool = False

    # TODO: add validator

    @staticmethod
    def auto() -> Self:
        return GridIndex()

    @staticmethod
    def from_index(index: int) -> Self:
        return GridIndex(index)

    @staticmethod
    def from_span(span: int) -> Self:
        return GridIndex(span, True)

    @staticmethod
    def from_any(value: object) -> Self:
        if value is None:
            return GridIndex()
        elif isinstance(value, GridIndex):
            return value
        elif isinstance(value, int):
            return GridIndex(value)
        else:
            raise TypeError("Unsupported value type")

    @property
    def type(self) -> int:
        if self.value is None:
            return GridIndexType.AUTO
        elif self.span:
            return GridIndexType.SPAN
        else:
            return GridIndexType.INDEX

    def to_dict(self) -> dict[str, int]:
        return dict(
            kind=self.type.value,
            value=self.value if self.value is not None else 0,
        )


@define(frozen=True)
class GridPlacement:
    start: GridIndex = field(
        default=None,
        converter=GridIndex.from_any,
        validator=[validators.optional(validators.instance_of(GridIndex))],
    )
    end: GridIndex = field(
        default=None,
        converter=GridIndex.from_any,
        validator=[validators.optional(validators.instance_of(GridIndex))],
    )

    @staticmethod
    def from_any(value: object) -> Self:
        # TODO: support more types of values?
        if value is None:
            return GridPlacement()
        elif isinstance(value, GridPlacement):
            return value
        else:
            raise TypeError("Unsupported value type")

    def to_dict(self) -> dict[str, int]:
        return dict(
            start=self.start.to_dict(),
            end=self.end.to_dict(),
        )


# endregion
