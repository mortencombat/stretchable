from enum import IntEnum
from math import isnan
from typing import Self

from attrs import define, field

SCALING_FACTOR: int = 1000


class Dimension(IntEnum):
    UNDEFINED: int = 0
    AUTO: int = 1
    POINTS: int = 2
    PERCENT: int = 3


class ValueConversionError(Exception):
    pass


@define(frozen=True)
class DimensionValue:
    unit: Dimension = Dimension.UNDEFINED
    value: float = float("nan")

    def to_taffy(self) -> dict:
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
        if value is None:
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
Dim = DimensionValue | float | None


@define(frozen=True)
class Size:
    width: Dim = field(default=AUTO, converter=DimensionValue.from_value)
    height: Dim = field(default=AUTO, converter=DimensionValue.from_value)

    def to_taffy(self) -> dict[str, float]:
        return dict(
            width=self.width.to_taffy(),
            height=self.height.to_taffy(),
        )

    def __str__(self) -> str:
        return f"Size(width={str(self.width)}, height={str(self.height)})"


@define(frozen=True)
class Rect:
    top: DimensionValue = field(default=UNDEF, converter=DimensionValue.from_value)
    end: DimensionValue = field(default=UNDEF, converter=DimensionValue.from_value)
    bottom: DimensionValue = field(default=UNDEF, converter=DimensionValue.from_value)
    start: DimensionValue = field(default=UNDEF, converter=DimensionValue.from_value)

    def __init__(
        self,
        *values: Dim,
        top: Dim = None,
        end: Dim = None,
        bottom: Dim = None,
        start: Dim = None,
    ) -> None:
        n = len(values)
        if top or end or bottom or start:
            if n > 0:
                raise Exception("Use either positional or named values, not both")
            self.__attrs_init__(top, end, bottom, start)
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
        if not value:
            return Rect()
        elif isinstance(value, Rect):
            return value
        elif isinstance(value, (int, float, DimensionValue)):
            return Rect(value)
        else:
            raise TypeError("Unsupported value type")

    @staticmethod
    def from_css_attrs(
        attributes: dict[str, Dim],
        *,
        prefix: str = None,
        common: str = None,
        start: str = "left",
        end: str = "right",
        top: str = "top",
        bottom: str = "bottom",
        default: Dim = UNDEF,
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
        for i, key in enumerate((top, end, bottom, start)):
            name = _get_attr_name(prefix, key)
            if name in attributes:
                values[i] = attributes[name]
                no_attrs = False
        if no_attrs:
            return None
        return Rect(*values)

    def to_taffy(self) -> dict[str, float]:
        return dict(
            start=self.start.to_taffy(),
            end=self.end.to_taffy(),
            top=self.top.to_taffy(),
            bottom=self.bottom.to_taffy(),
        )

    def __str__(self) -> str:
        return f"Rect(start={self.start}, end={self.end}, top={self.top}, bottom={self.bottom})"
