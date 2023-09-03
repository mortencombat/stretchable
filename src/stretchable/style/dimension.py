from enum import IntEnum
from math import isnan
from typing import Self

from attrs import define, field

# SCALING_FACTOR: int = 1


class Dimension(IntEnum):
    AUTO = 0
    POINTS = 1
    PERCENT = 2
    MIN_CONTENT = 3
    MAX_CONTENT = 4


class ValueConversionError(Exception):
    pass


# TODO: Move Length to generic, with these:
#   LengthPercentageAuto    Points, Percent, Auto
#   LengthPercentage        Points, Percent
#   ?                       Points
#   AvailableSpace          Points, MinContent, MaxContent
# NOTE: Consider also that measure functions use MAX_CONTENT and MIN_CONTENT in some way


@define(frozen=True)
class Length:
    unit: Dimension = Dimension.AUTO
    value: float = float("nan")

    def to_taffy(self) -> dict:
        return dict(dim=self.unit.value, value=self.value)
        # (self.value * SCALING_FACTOR)
        #     if self.unit == Dimension.POINTS
        #     else self.value,
        # )

    def __mul__(self, other):
        if self.unit == Dimension.AUTO:
            raise ValueError("Cannot apply a value to AUTO")
        if not isinstance(other, (int, float)):
            raise ValueError("Cannot apply a non-numeric value to Length")
        return Length(self.unit, self.value * other)

    __rmul__ = __mul__

    def __str__(self):
        if self.unit == Dimension.AUTO:
            return "<auto>"
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
        if value is None:
            return AUTO
        if isinstance(value, (int, float)):
            return Length(Dimension.POINTS, value)
        elif isinstance(value, Length):
            return value
        elif isnan(value):
            return AUTO

        raise ValueError(f"{value} not recognized as a supported value")


pct = Length(Dimension.PERCENT, 0.01)
AUTO = Length(Dimension.AUTO)
ZERO = Length(Dimension.POINTS, 0.0)
NAN = float("nan")
Dim = Length | float | None
MAX_CONTENT = Length(Dimension.MAX_CONTENT)
MIN_CONTENT = Length(Dimension.MIN_CONTENT)


@define(frozen=True)
class Size:
    width: Length = field(default=AUTO, converter=Length.from_value)
    height: Length = field(default=AUTO, converter=Length.from_value)

    def to_taffy(self) -> dict[str, float]:
        return dict(
            width=self.width.to_taffy(),
            height=self.height.to_taffy(),
        )

    def __str__(self) -> str:
        return f"Size(width={str(self.width)}, height={str(self.height)})"

    @staticmethod
    def from_value(value: object = None) -> Self:
        if value is None:
            return Size()
        elif isinstance(value, Size):
            return value
        elif isinstance(value, (int, float, Length)):
            return Size(value, value)
        else:
            raise TypeError("Unsupported value type")


@define(frozen=True)
class Rect:
    top: Length = field(default=AUTO, converter=Length.from_value)
    right: Length = field(default=AUTO, converter=Length.from_value)
    bottom: Length = field(default=AUTO, converter=Length.from_value)
    left: Length = field(default=AUTO, converter=Length.from_value)

    def __init__(
        self,
        *values: Dim,
        top: Dim = None,
        right: Dim = None,
        bottom: Dim = None,
        left: Dim = None,
    ) -> None:
        n = len(values)
        if top or right or bottom or left:
            if n > 0:
                raise Exception("Use either positional or named values, not both")
            self.__attrs_init__(top, right, bottom, left)
        else:
            if n == 0:
                self.__attrs_init__()
            elif n == 1:
                self.__attrs_init__(values[0], values[0], values[0], values[0])
            elif n == 2:
                self.__attrs_init__(values[0], values[1], values[0], values[1])
            elif n == 3:
                self.__attrs_init__(values[0], values[1], values[2], values[1])
            elif n == 4:
                self.__attrs_init__(*values)
            else:
                raise Exception(f"Unsupported number of arguments ({n})")

    @staticmethod
    def from_value(value: object = None) -> Self:
        if value is None:
            return Rect()
        elif isinstance(value, Rect):
            return value
        elif isinstance(value, (int, float, Length)):
            return Rect(value)
        else:
            raise TypeError("Unsupported value type")

    @staticmethod
    def from_css_attrs(
        attributes: dict[str, Dim],
        *,
        prefix: str = None,
        common: str = None,
        left: str = "left",
        right: str = "right",
        top: str = "top",
        bottom: str = "bottom",
        default: Length = AUTO,
    ) -> Self:
        def _get_attr_name(prefix: str, name: str) -> str:
            return f"{prefix}-{name}" if prefix else name

        if common:
            name = _get_attr_name(prefix, common)
            if name in attributes:
                return Rect(attributes[name])
        if prefix and prefix in attributes:
            return Rect(attributes[prefix])

        values = [default] * 4
        no_attrs = True
        for i, key in enumerate((top, right, bottom, left)):
            name = _get_attr_name(prefix, key)
            if name in attributes:
                values[i] = attributes[name]
                no_attrs = False
        if no_attrs:
            return None
        return Rect(*values)

    def to_taffy(self) -> dict[str, float]:
        return dict(
            left=self.left.to_taffy(),
            right=self.right.to_taffy(),
            top=self.top.to_taffy(),
            bottom=self.bottom.to_taffy(),
        )

    def __str__(self) -> str:
        return f"Rect(left={self.left}, right={self.right}, top={self.top}, bottom={self.bottom})"
