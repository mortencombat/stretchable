from enum import IntEnum
from math import isnan
from typing import Any, Generic, Optional, Self, TypeVar, get_args

T = TypeVar("T")
NAN = float("nan")


class Scale(IntEnum):
    AUTO = 0
    POINTS = 1
    PERCENT = 2
    MIN_CONTENT = 3
    MAX_CONTENT = 4


class Points(IntEnum):
    POINTS = Scale.POINTS


class PointsPercent(IntEnum):
    POINTS = Scale.POINTS
    PERCENT = Scale.PERCENT


class PointsPercentAuto(IntEnum):
    AUTO = Scale.AUTO
    POINTS = Scale.POINTS
    PERCENT = Scale.PERCENT


class AvailableSpace(IntEnum):
    DEFINITE = Scale.POINTS
    MIN_CONTENT = Scale.MIN_CONTENT
    MAX_CONTENT = Scale.MAX_CONTENT


# @define(frozen=True)
class LengthBase(Generic[T]):
    _type_T: Any
    __slots__ = ("scale", "value")

    @staticmethod
    def _check_scale(T: type, scale: IntEnum) -> None:
        if scale is None:
            return
        for m in dir(T):
            if m.startswith("_") or not m[0].isupper():
                continue
            v = getattr(T, m)
            if v == scale:
                return

        try:
            _scale = scale._name_
        except AttributeError:
            _scale = scale
        raise TypeError(f"Scale {_scale} is not supported in this context")

    def __init_subclass__(cls) -> None:
        cls._type_T = get_args(cls.__orig_bases__[0])[0]

    def __init__(self, scale: T = None, value: float = NAN) -> None:
        # Check if scale value corresponds to an allowed scale as defined by T.
        if scale:
            LengthBase._check_scale(self._type_T, scale)
        self.scale = scale
        self.value = value

    def __str__(self) -> str:
        match self.scale:
            case Scale.AUTO:
                return "auto"
            case Scale.POINTS:
                return f"{self.value:.2f} pt" if not isnan(self.value) else "nan"
            case Scale.PERCENT:
                return f"{self.value*100:.2f} %" if not isnan(self.value) else "nan"
            case Scale.MIN_CONTENT:
                return "min-content"
            case Scale.MAX_CONTENT:
                return "max-content"
            case _:
                return "None"

    @staticmethod
    def default() -> Self:
        raise NotImplementedError

    @classmethod
    def from_any(cls, value: Any = None) -> Self:
        """
        Scenarios:
          - If value is None, get the default value for cls.
          - If value is int/float, it is assumed to be Scale.POINTS (unless cls
            does not support this scale, in which case an exception will be
            raised)
          - If value is already an instance of a subclass of LengthBase, check
            that scale is supported for cls.
        """

        if value is None:
            return cls.default()
        if isinstance(value, (int, float)):
            value *= PT
        if not issubclass(type(value), LengthBase):
            raise TypeError("Value is not supported/recognized: " + str(value))
        LengthBase._check_scale(cls._type_T, value.scale)

        return cls(value.scale, value.value)

    def to_dict(self) -> dict[str, int | float]:
        return dict(dim=self.scale.value, value=self.value)

    def to_pts(self, container: Optional[float] = None) -> float:
        match self.scale:
            case Scale.POINTS:
                return self.value
            case Scale.PERCENT:
                if container is None:
                    raise ValueError(
                        "Length scale is PERCENT, `container` dimension must be provided"
                    )
                return self.value * container
            case scale:
                raise ValueError(
                    "Length with scale %s cannot be represented in PTS" % scale
                )

    def __eq__(self, __value: object) -> bool:
        if not isinstance(__value, LengthBase):
            return False
        return self.scale == __value.scale and self.value == __value.value


class Length(LengthBase[Scale]):
    def __mul__(self, value):
        if self.scale not in (Scale.POINTS, Scale.PERCENT):
            raise TypeError("Cannot multiply Length of type: " + str(self))
        elif not isinstance(value, (int, float)):
            raise ValueError("Cannot multiply with non-numeric value: " + str(value))
        return Length(self.scale, self.value * value)

    __rmul__ = __mul__

    @staticmethod
    def default() -> Self:
        return Length(Scale.AUTO)


class LengthAvailableSpace(LengthBase[AvailableSpace]):
    @staticmethod
    def definite(value: float | Length) -> Self:
        if value is None:
            raise TypeError("None value is not supported in this context")
        if issubclass(type(value), LengthBase) and value.scale != Scale.POINTS:
            raise ValueError(f"Only POINTS is supported in this context, not {value}")
        return LengthAvailableSpace(AvailableSpace.DEFINITE, value)

    @staticmethod
    def min_content() -> Self:
        return LengthAvailableSpace(AvailableSpace.MIN_CONTENT)

    @staticmethod
    def max_content() -> Self:
        return LengthAvailableSpace(AvailableSpace.MAX_CONTENT)

    @staticmethod
    def default() -> Self:
        return LengthAvailableSpace(AvailableSpace.MAX_CONTENT)

    @staticmethod
    def from_dict(value: dict[int, float]) -> Self:
        match value["dim"]:
            case Scale.POINTS:
                return LengthAvailableSpace.definite(value["value"])
            case Scale.MIN_CONTENT:
                return LengthAvailableSpace.min_content()
            case Scale.MAX_CONTENT:
                return LengthAvailableSpace.max_content()
            case _:
                raise ValueError(
                    f"Scale {value['dim']} is not supported in this context"
                )


class LengthPoints(LengthBase[Points]):
    @staticmethod
    def points(value: float | Length = None) -> Self:
        if value is None:
            value = NAN
        elif issubclass(type(value), LengthBase) and value.scale != Scale.POINTS:
            raise ValueError(f"Only POINTS is supported in this context, not {value}")
        return LengthPointsPercent(PointsPercent.POINTS, value)

    @staticmethod
    def default() -> Self:
        return LengthPoints()


class LengthPointsPercent(LengthBase[PointsPercent]):
    @staticmethod
    def points(value: float | Length) -> Self:
        if value is None:
            value = NAN
        elif issubclass(type(value), LengthBase) and value.scale != Scale.POINTS:
            raise ValueError(f"Only POINTS is supported in this context, not {value}")
        return LengthPointsPercent(PointsPercent.POINTS, value)

    @staticmethod
    def percent(value: float | Length) -> Self:
        if value is None:
            value = NAN
        elif issubclass(type(value), LengthBase) and value.scale != Scale.PERCENT:
            raise ValueError(f"Only PERCENT is supported in this context, not {value}")
        return LengthPointsPercent(PointsPercent.PERCENT, value)

    @staticmethod
    def default() -> Self:
        return LengthPointsPercent(PointsPercent.POINTS)


class LengthPointsPercentAuto(LengthBase[PointsPercentAuto]):
    @staticmethod
    def points(value: float | Length) -> Self:
        if value is None:
            value = NAN
        elif issubclass(type(value), LengthBase) and value.scale != Scale.POINTS:
            raise ValueError(f"Only POINTS is supported in this context, not {value}")
        return LengthPointsPercentAuto(PointsPercent.POINTS, value)

    @staticmethod
    def percent(value: float | Length) -> Self:
        if value is None:
            value = NAN
        elif issubclass(type(value), LengthBase) and value.scale != Scale.PERCENT:
            raise ValueError(f"Only PERCENT is supported in this context, not {value}")
        return LengthPointsPercentAuto(PointsPercent.PERCENT, value)

    @staticmethod
    def auto() -> Self:
        return LengthPointsPercentAuto(PointsPercent.AUTO)

    @staticmethod
    def default() -> Self:
        return LengthPointsPercentAuto(PointsPercentAuto.AUTO, NAN)


AUTO = Length(Scale.AUTO)
PCT = Length(Scale.PERCENT, 0.01)
PT = Length(Scale.POINTS, 1)
MIN_CONTENT = Length(Scale.MIN_CONTENT)
MAX_CONTENT = Length(Scale.MAX_CONTENT)
