from enum import IntEnum
from math import isnan
from typing import Generic, Self, TypeVar

from attrs import define, field

from .stretch import _bindings

SCALING_FACTOR: int = 1000


class AlignItems(IntEnum):
    FLEX_START: int = 0
    FLEX_END: int = 1
    CENTER: int = 2
    BASELINE: int = 3
    STRETCH: int = 4


class AlignSelf(IntEnum):
    AUTO: int = 0
    FLEX_START: int = 1
    FLEX_END: int = 2
    CENTER: int = 3
    BASELINE: int = 4
    STRETCH: int = 5


class AlignContent(IntEnum):
    FLEX_START: int = 0
    FLEX_END: int = 1
    CENTER: int = 2
    STRETCH: int = 3
    SPACE_BETWEEN: int = 4
    SPACE_AROUND: int = 5


class Direction(IntEnum):
    INHERIT: int = 0
    LTR: int = 1
    RTL: int = 2


class Display(IntEnum):
    FLEX: int = 0
    NONE: int = 1


class FlexDirection(IntEnum):
    ROW: int = 0
    COLUMN: int = 1
    ROW_REVERSE: int = 2
    COLUMN_REVERSE: int = 3


class JustifyContent(IntEnum):
    FLEX_START: int = 0
    FLEX_END: int = 1
    CENTER: int = 2
    SPACE_BETWEEN: int = 3
    SPACE_AROUND: int = 4
    SPACE_EVENLY: int = 5


class Overflow(IntEnum):
    VISIBLE: int = 0
    HIDDEN: int = 1
    SCROLL: int = 2


class PositionType(IntEnum):
    RELATIVE: int = 0
    ABSOLUTE: int = 1


class FlexWrap(IntEnum):
    NO_WRAP: int = 0
    WRAP: int = 1
    WRAP_REVERSE: int = 2


class Dimension(IntEnum):
    UNDEFINED: int = 0
    AUTO: int = 1
    POINTS: int = 2
    PERCENT: int = 3


T = TypeVar("T")


class ValueConversionError(Exception):
    pass


@define(frozen=True)
class DimensionValue(Generic[T]):
    unit: Dimension = Dimension.UNDEFINED
    value: float = float("nan")

    def to_stretch(self) -> dict:
        return dict(
            dim=self.unit.value,
            value=(self.value * SCALING_FACTOR)
            if self.unit == Dimension.POINTS
            else self.value,
        )

    def __mul__(self, other):
        if self.unit in (Dimension.AUTO, Dimension.UNDEFINED):
            raise ValueError("Cannot apply a value to auto or undefined dimension")
        if not isinstance(other, (int, float)):
            raise ValueError("Cannot apply a non-numeric value to dimension")
        return DimensionValue(self.unit, self.value * other)

    __rmul__ = __mul__

    def __str__(self):
        if self.unit == Dimension.AUTO:
            return "<auto>"
        elif self.unit == Dimension.UNDEFINED:
            return "<undef>"
        elif self.unit == Dimension.POINTS:
            return f"{self.value:.2f} pts"
        elif self.unit == Dimension.PERCENT:
            return f"{self.value*100:.2f} %"

    def to_float(self, container: float = None) -> float:
        if self.unit == Dimension.POINTS:
            return self.value
        elif self.unit == Dimension.PERCENT:
            if not container:
                raise ValueConversionError(
                    "Container dimension is required to convert percentage to absolute value"
                )
            return self.value * container
        else:
            return 0

    @staticmethod
    def from_value(value: object = None) -> Self:
        if not value:
            return UNDEF
        if isinstance(value, (int, float)):
            return DimensionValue(Dimension.POINTS, value)
        elif isinstance(value, DimensionValue):
            return value
        elif isnan(value):
            return UNDEF

        raise ValueError(f"{value} not recognized as a supported value")


pct = DimensionValue(Dimension.PERCENT, 0.01)
AUTO = DimensionValue(Dimension.AUTO)
UNDEF = DimensionValue()
NAN = float("nan")


@define(frozen=True)
class Size:
    width: DimensionValue = field(default=AUTO, converter=DimensionValue.from_value)
    height: DimensionValue = field(default=AUTO, converter=DimensionValue.from_value)

    def to_stretch(self) -> dict[str, float]:
        return dict(
            width=self.width.to_stretch(),
            height=self.height.to_stretch(),
        )


@define(frozen=True)
class Rect:
    start: DimensionValue = field(default=UNDEF, converter=DimensionValue.from_value)
    end: DimensionValue = field(default=UNDEF, converter=DimensionValue.from_value)
    top: DimensionValue = field(default=UNDEF, converter=DimensionValue.from_value)
    bottom: DimensionValue = field(default=UNDEF, converter=DimensionValue.from_value)

    def to_stretch(self) -> dict[str, float]:
        return dict(
            start=self.start.to_stretch(),
            end=self.end.to_stretch(),
            top=self.top.to_stretch(),
            bottom=self.bottom.to_stretch(),
        )

    def __str__(self) -> str:
        return f"Rect(start={self.start}, end={self.end}, top={self.top}, bottom={self.bottom})"


@define(frozen=True)
class Style:
    display: Display = Display.FLEX
    position_type: PositionType = PositionType.RELATIVE
    direction: Direction = Direction.INHERIT
    flex_direction: FlexDirection = FlexDirection.ROW
    flex_wrap: FlexWrap = FlexWrap.NO_WRAP
    overflow: Overflow = Overflow.HIDDEN
    align_items: AlignItems = AlignItems.STRETCH
    align_self: AlignSelf = AlignSelf.AUTO
    align_content: AlignContent = AlignContent.FLEX_START
    justify_content: JustifyContent = JustifyContent.FLEX_START
    position: Rect = field(factory=Rect)
    margin: Rect = field(factory=Rect)
    padding: Rect = field(factory=Rect)
    border: Rect = field(factory=Rect)
    flex_grow: float = 0.0
    flex_shrink: float = 1.0
    flex_basis: DimensionValue = AUTO
    size: Size = field(factory=Size)
    min_size: Size = field(factory=Size)
    max_size: Size = field(factory=Size)
    aspect_ratio: float = None

    __ptr: int = field(init=False, default=None)

    def __attrs_post_init__(self):
        object.__setattr__(self, "_Style__ptr", None)

    @property
    def _ptr(self) -> int:
        if not self.__ptr:
            object.__setattr__(
                self,
                "_Style__ptr",
                _bindings.stretch_style_create(
                    display=self.display.value,
                    position_type=self.position_type.value,
                    direction=self.direction.value,
                    flex_direction=self.flex_direction.value,
                    flex_wrap=self.flex_wrap.value,
                    overflow=self.overflow.value,
                    align_items=self.align_items.value,
                    align_self=self.align_self.value,
                    align_content=self.align_content.value,
                    justify_content=self.justify_content.value,
                    position=self.position.to_stretch(),
                    margin=self.margin.to_stretch(),
                    padding=self.padding.to_stretch(),
                    border=self.border.to_stretch(),
                    flex_grow=self.flex_grow,
                    flex_shrink=self.flex_shrink,
                    flex_basis=self.flex_basis.to_stretch(),
                    size=self.size.to_stretch(),
                    min_size=self.min_size.to_stretch(),
                    max_size=self.max_size.to_stretch(),
                    aspect_ratio=self.aspect_ratio or NAN,
                ),
            )
        return self.__ptr

    def __del__(self):
        if self.__ptr:
            _bindings.stretch_style_free(self.__ptr)
            object.__setattr__(self, "_Style__ptr", None)
