from __future__ import annotations

import re
from enum import IntEnum
from typing import Any, Optional

from attrs import define, field, validators

from .geometry import length


def parse_value(
    value: str,
) -> length.Length | float | str | tuple[length.Length]:
    def parse_single(val: str) -> length.Length | float | str:
        val = val.strip().lower()
        if val.endswith("px"):
            return float(val.rstrip("px")) * length.PT
        if val.endswith("%"):
            return float(val.rstrip("%")) * length.PCT
        if val.endswith("fr"):
            return float(val.rstrip("fr")) * length.FR
        if val == "auto":
            return length.AUTO
        if val == "min-content":
            return length.MIN_CONTENT
        if val == "max-content":
            return length.MAX_CONTENT
        try:
            return float(val)
        except ValueError:
            return val

    value = value.strip()
    if " " in value:
        return tuple(parse_single(v) for v in value.split(" "))
    else:
        return parse_single(value)


# region Layout strategy/misc


class Display(IntEnum):
    """Used to control node visibility and layout strategy.

    See `display <https://developer.mozilla.org/en-US/docs/Web/CSS/display>`_ on MDN for more information.
    """

    NONE = 0
    FLEX = 1
    GRID = 2
    BLOCK = 3


class BoxSizing(IntEnum):
    """
    Specifies whether size styles for are applied to the "content box" or the "border box".

    See `box-sizing <https://developer.mozilla.org/en-US/docs/Web/CSS/box-sizing>`_ on MDN for more information.
    """

    BORDER = 0
    CONTENT = 1


class Overflow(IntEnum):
    """Controls the desired behavior when content does not fit inside the parent node.

    See `overflow <https://developer.mozilla.org/en-US/docs/Web/CSS/overflow>`_ on MDN for more information.
    """

    VISIBLE = 0
    HIDDEN = 1
    SCROLL = 2
    CLIP = 3


class Position(IntEnum):
    """The positioning strategy for this node.

    This controls both how the origin is determined for the `inset` property,
    and whether or not the item will be controlled by flexbox's layout
    algorithm.

    See `position <https://developer.mozilla.org/en-US/docs/Web/CSS/position>`_ on MDN for more information.

    Warning
    -------
    This enum follows the behavior of CSS's `position` property, which
    can be unintuitive.
    """

    RELATIVE = 0
    ABSOLUTE = 1


# endregion

# region Alignment


class AlignItems(IntEnum):
    """Used to control how child nodes are aligned.

    For Flexbox it controls alignment in the cross axis.
    For Grid it controls alignment in the block axis.

    See `align-items <https://developer.mozilla.org/en-US/docs/Web/CSS/align-items>`_ on MDN for more information.
    """

    START = 0
    END = 1
    FLEX_START = 2
    FLEX_END = 3
    CENTER = 4
    BASELINE = 5
    STRETCH = 6


class JustifyItems(IntEnum):
    """Used to control how child nodes are aligned.

    Does not apply to Flexbox, and will be ignored if specified on a flex container.
    For Grid it controls alignment in the inline axis.

    See `justify-items <https://developer.mozilla.org/en-US/docs/Web/CSS/justify-items>`_ on MDN for more information.
    """

    START = 0
    END = 1
    FLEX_START = 2
    FLEX_END = 3
    CENTER = 4
    BASELINE = 5
    STRETCH = 6


class AlignSelf(IntEnum):
    """Used to control how the node is aligned.

    Overrides the parent Node's `AlignItems` property.
    For Flexbox it controls alignment in the cross axis
    For Grid it controls alignment in the block axis

    See `align-self <https://developer.mozilla.org/en-US/docs/Web/CSS/align-self>`_ on MDN for more information.
    """

    START = 0
    END = 1
    FLEX_START = 2
    FLEX_END = 3
    CENTER = 4
    BASELINE = 5
    STRETCH = 6


class JustifySelf(IntEnum):
    """Used to control how the node is aligned.

    Overrides the parent node :py:attr:`Style` property.
    Does not apply to Flexbox, and will be ignored if specified on a flex child
    For Grid it controls alignment in the inline axis

    See `justify-self <https://developer.mozilla.org/en-US/docs/Web/CSS/justify-self>`_ on MDN for more information.
    """

    START = 0
    END = 1
    FLEX_START = 2
    FLEX_END = 3
    CENTER = 4
    BASELINE = 5
    STRETCH = 6


class AlignContent(IntEnum):
    """Sets the distribution of space between and around content items.

    For Flexbox it controls alignment in the cross axis. For Grid it controls
    alignment in the block axis.

    See `align-content <https://developer.mozilla.org/en-US/docs/Web/CSS/align-content>`_ on MDN for more information.
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
    """Sets the distribution of space between and around content items.

    For Flexbox it controls alignment in the main axis. For Grid it controls
    alignment in the inline axis.

    See `justify-content <https://developer.mozilla.org/en-US/docs/Web/CSS/justify-content>`_ on MDN for more information.
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
    """Controls whether flex items are forced onto one line or can wrap onto
    multiple lines.

    See `flex-wrap <https://developer.mozilla.org/en-US/docs/Web/CSS/flex-wrap>`_ on MDN for more information.
    """

    NO_WRAP = 0
    WRAP = 1
    WRAP_REVERSE = 2


class FlexDirection(IntEnum):
    """The direction of the flexbox layout main axis.

    There are always two perpendicular layout axes: main (or primary) and cross
    (or secondary). Adding items will cause them to be positioned adjacent to
    each other along the main axis. By varying this value throughout your tree,
    you can create complex axis-aligned layouts.

    Items are always aligned relative to the cross axis, and justified relative
    to the main axis.

    See `flex-direction <https://developer.mozilla.org/en-US/docs/Web/CSS/flex-direction>`_ on MDN for more information.
    """

    ROW = 0
    COLUMN = 1
    ROW_REVERSE = 2
    COLUMN_REVERSE = 3


# endregion

# region Grid


class GridAutoFlow(IntEnum):
    """Controls whether grid items are placed row-wise or column-wise, and whether
    the sparse or dense packing algorithm is used.

    The "dense" packing algorithm
    attempts to fill in holes earlier in the grid, if smaller items come up
    later. This may cause items to appear out-of-order, when doing so would fill
    in holes left by larger items.

    See `grid-auto-flow <https://developer.mozilla.org/en-US/docs/Web/CSS/grid-auto-flow>`_ on MDN for more information.
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
class GridTrackSize:
    min_size: length.LengthMinTrackSize = field(
        converter=length.LengthMinTrackSize.from_any
    )
    max_size: length.LengthMaxTrackSize = field(
        converter=length.LengthMaxTrackSize.from_any
    )

    @staticmethod
    def from_inline(value: str) -> GridTrackSize:
        """
        Parses the provided CSS property value and returns a GridTrackSize instance.
        Note that the parser is quite basic and may not understand all valid syntax.

        `value` may be on one of the following forms:
            40px
            20%
            1fr
            minmax(20px, 40px)
            min-content
            max-content
            fit-content(50%)
            fit-content(30px)
        """

        value = value.strip().lower()
        if value == "auto":
            return GridTrackSize.auto()
        if value == "min-content":
            return GridTrackSize.min_content()
        if value == "max-content":
            return GridTrackSize.max_content()
        if value.startswith("fit-content"):
            value = value.removeprefix("fit-content(").removesuffix(")")
            value = parse_value(value)
            return GridTrackSize.fit_content(value)
        if value.startswith("minmax"):
            value = value.removeprefix("minmax(").removesuffix(")")
            value = value.split(",")
            if len(value) != 2:
                raise ValueError(f"'{value}' not recognized as a valid grid track size")
            return GridTrackSize(parse_value(value[0]), parse_value(value[1]))

        # Appears to be a specific value (px, % or fr)
        value = parse_value(value)
        if isinstance(value, length.Length):
            if value.scale == length.Scale.FLEX:
                return GridTrackSize.flex(value)
            elif value.scale == length.Scale.POINTS:
                return GridTrackSize.points(value)
            elif value.scale == length.Scale.PERCENT:
                return GridTrackSize.percent(value)

        raise ValueError(f"'{value}' not recognized as a valid grid track size")

    @staticmethod
    def from_any(value: Any) -> GridTrackSize:
        if not value:
            return GridTrackSize.auto()
        if isinstance(value, GridTrackSize):
            return value
        if isinstance(value, str):
            return GridTrackSize.from_inline(value)
        if isinstance(value, (list, tuple)) and len(value) == 2:
            return GridTrackSize(*value)
        if isinstance(value, (int, float)):
            return GridTrackSize.points(value)
        if isinstance(value, length.Length):
            if value.scale == length.Scale.AUTO:
                return GridTrackSize.auto()
            elif value.scale == length.Scale.MIN_CONTENT:
                return GridTrackSize.min_content()
            elif value.scale == length.Scale.MAX_CONTENT:
                return GridTrackSize.max_content()
            elif (
                value.scale
                == length.Scale.FIT_CONTENT_PERCENT | length.Scale.FIT_CONTENT_POINTS
            ):
                return GridTrackSize.fit_content(value)
            elif value.scale == length.Scale.POINTS:
                return GridTrackSize.points(value)
            elif value.scale == length.Scale.PERCENT:
                return GridTrackSize.percent(value)
            elif value.scale == length.Scale.FLEX:
                return GridTrackSize.flex(value)
        raise ValueError(
            f"The value {value} could not be interpreted as a valid GridTrackSize"
        )

    @staticmethod
    def auto() -> GridTrackSize:
        return GridTrackSize(length.AUTO, length.AUTO)

    @staticmethod
    def min_content() -> GridTrackSize:
        return GridTrackSize(length.MIN_CONTENT, length.MIN_CONTENT)

    @staticmethod
    def max_content() -> GridTrackSize:
        return GridTrackSize(length.MAX_CONTENT, length.MAX_CONTENT)

    @staticmethod
    def fit_content(value: length.PointsPercent | int | float) -> GridTrackSize:
        return GridTrackSize(length.AUTO, length.LengthMaxTrackSize.fit_content(value))

    @staticmethod
    def zero() -> GridTrackSize:
        return GridTrackSize(length.ZERO, length.ZERO)

    @staticmethod
    def points(value: length.LengthPointsPercent | int | float) -> GridTrackSize:
        if not isinstance(value, length.Length):
            value = length.LengthPointsPercent.points(value)
        return GridTrackSize(value, value)

    @staticmethod
    def percent(value: length.LengthPointsPercent | int | float) -> GridTrackSize:
        if not isinstance(value, length.Length):
            value = length.LengthPointsPercent.percent(value)
        return GridTrackSize(value, value)

    @staticmethod
    def flex(value: length.LengthMaxTrackSize | float) -> GridTrackSize:
        if not isinstance(value, length.Length):
            value = length.LengthMaxTrackSize.flex(value)
        return GridTrackSize(length.AUTO, value)

    def to_dict(self) -> dict:
        return dict(
            min_size=self.min_size.to_dict(),
            max_size=self.max_size.to_dict(),
        )

    def __str__(self) -> str:
        if (
            self.min_size == self.max_size
            or (
                self.min_size == length.AUTO
                and self.max_size.scale == length.Scale.FLEX
            )
            or self.max_size.scale == length.Scale.FIT_CONTENT_POINTS
            or self.max_size.scale == length.Scale.FIT_CONTENT_PERCENT
        ):
            return str(self.max_size)
        return f"minmax({self.min_size}, {self.max_size})"


class GridTrackRepetition(IntEnum):
    SINGLE = -2
    AUTO_FIT = -1
    AUTO_FILL = 0
    COUNT = 1  # repeat_count


# class GridTrackSizing(ABC):
#     @abstractmethod
#     def to_dict(self) -> dict:
#         ...


@define(frozen=True)
class GridTrackSizing:
    tracks: list[GridTrackSize]
    repetition: GridTrackRepetition = field(default=GridTrackRepetition.AUTO_FILL)
    count: int = field(kw_only=True, default=None)

    @staticmethod
    def single(track: Any) -> GridTrackSizing:
        return GridTrackSizing(
            [GridTrackSize.from_any(track)], GridTrackRepetition.SINGLE
        )

    @staticmethod
    def repeat(
        tracks: list[Any],
        *,
        repetition: GridTrackRepetition = GridTrackRepetition.AUTO_FILL,
        count: Optional[int] = None,
    ) -> GridTrackSizing:
        if repetition == GridTrackRepetition.SINGLE:
            raise ValueError("GridTrackRepetition.SINGLE is not valid in this context")
        if repetition == GridTrackRepetition.COUNT and (count is None or count < 1):
            raise ValueError(
                "`count` argument is required and must be >0 for GridTrackRepetition.COUNT"
            )
        return GridTrackSizing(
            [GridTrackSize.from_any(track) for track in tracks], repetition, count=count
        )

    @staticmethod
    def from_inline(value: str) -> GridTrackSizing:
        """
        Parses the provided CSS property value and returns a GridTrackSize instance.
        Note that the parser is quite basic and may not understand all valid syntax.

        The value may be one of the following:
            <track>
            repeat(<repetition>, <track>[ <track>] ...)
        where <track> is a value that can be parsed as a track size (eg. using
        GridTrackSize.from_inline(...)), and <repetition> is either a positive
        integer, 'auto-fill' or 'auto-fit'.
        """

        value = value.strip().lower()
        if not value.startswith("repeat(") or not value.endswith(")"):
            return GridTrackSizing.single(value)

        value = value.removeprefix("repeat(").removesuffix(")")
        repetition, _, tracks = value.partition(",")

        # Parse repetition, split tracks
        count = None
        v = repetition.strip()
        if v == "auto-fill":
            repetition = GridTrackRepetition.AUTO_FILL
        elif v == "auto-fit":
            repetition = GridTrackRepetition.AUTO_FIT
        else:
            try:
                repetition = GridTrackRepetition.COUNT
                count = int(v)
            except TypeError:
                raise ValueError(
                    f"`repetition` value '{v}' should be either 'auto-fill', 'auto-fit' or a positive integer"
                )
        tracks = re.split(" (?![^(,]*\\))", tracks.replace(", ", ","))
        return GridTrackSizing.repeat(tracks, repetition=repetition, count=count)

    @staticmethod
    def from_any(value: Any) -> GridTrackSizing:
        if value is None:
            return GridTrackSizing.single(None)
        if isinstance(value, str):
            return GridTrackSizing.from_inline(value)
        if isinstance(value, GridTrackSizing):
            return value
        return GridTrackSizing.single(value)

    def to_dict(self) -> dict:
        if self.repetition == GridTrackRepetition.SINGLE:
            return dict(
                repetition=GridTrackRepetition.SINGLE,
                single=self.tracks[0].to_dict(),
                repeat=[],
            )

        return dict(
            repetition=(
                self.repetition
                if self.repetition != GridTrackRepetition.COUNT
                else self.count
            ),
            single=None,
            repeat=[t.to_dict() for t in self.tracks],
        )

    def __str__(self) -> str:
        if self.repetition == GridTrackRepetition.SINGLE:
            return str(self.tracks[0])
        return f"repeat({self.repetition._name_.lower().replace('_', '-')}, {' '.join(str(t) for t in self.tracks)})"


@define(frozen=True)
class GridIndex:
    value: int = None
    span: bool = False

    # TODO: add validator: index can be != 0, span > 0

    @staticmethod
    def auto() -> GridIndex:
        return GridIndex()

    @staticmethod
    def from_index(index: int) -> GridIndex:
        return GridIndex(index)

    @staticmethod
    def from_span(span: int) -> GridIndex:
        return GridIndex(span, True)

    @staticmethod
    def from_inline(value: str) -> GridIndex:
        value = value.strip()
        if value.startswith("span"):
            value = value.removeprefix("span").strip()
            try:
                return GridIndex.from_span(int(value))
            except TypeError:
                raise ValueError(
                    f"'{value}' is not a recognized as a valid grid-* value"
                )
        try:
            return GridIndex.from_index(int(value))
        except TypeError:
            raise ValueError(f"'{value}' is not a recognized as a valid grid-* value")

    @staticmethod
    def from_any(value: object) -> GridIndex:
        if value is None:
            return GridIndex.auto()
        if isinstance(value, str):
            return GridIndex.from_inline(value)
        if isinstance(value, GridIndex):
            return value
        if isinstance(value, int):
            return GridIndex(value)
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
    def from_inline(value: str) -> GridPlacement:
        if "/" in value:
            start, _, end = value.partition("/")
        else:
            start, end = value, None
        return GridPlacement(start, end)

    @staticmethod
    def from_any(value: object) -> GridPlacement:
        # TODO: support more types of values?
        if value is None:
            return GridPlacement()
        if isinstance(value, str):
            return GridPlacement.from_inline(value)
        if isinstance(value, GridPlacement):
            return value
        raise TypeError("Unsupported value type")

    def to_dict(self) -> dict[str, int]:
        return dict(
            start=self.start.to_dict(),
            end=self.end.to_dict(),
        )


# endregion
