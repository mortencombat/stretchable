from __future__ import annotations

from enum import IntEnum
from math import isnan
from typing import Any, Generic, Optional, TypeVar, get_args

T = TypeVar("T")
NAN = float("nan")


class Scale(IntEnum):
    """All available length scales/settings (support is context-dependent)."""

    AUTO = 0
    POINTS = 1
    PERCENT = 2
    MIN_CONTENT = 3
    MAX_CONTENT = 4
    # For track size, see:
    # <https://developer.mozilla.org/en-US/docs/Web/CSS/grid-template-columns>
    FIT_CONTENT_POINTS = 5
    FIT_CONTENT_PERCENT = 6
    FLEX = 7


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


class MinTrackSize(IntEnum):
    POINTS = Scale.POINTS
    PERCENT = Scale.PERCENT
    MIN_CONTENT = Scale.MIN_CONTENT
    MAX_CONTENT = Scale.MAX_CONTENT
    AUTO = Scale.AUTO


class MaxTrackSize(IntEnum):
    POINTS = Scale.POINTS
    PERCENT = Scale.PERCENT
    MIN_CONTENT = Scale.MIN_CONTENT
    MAX_CONTENT = Scale.MAX_CONTENT
    FIT_CONTENT_POINTS = Scale.FIT_CONTENT_POINTS
    FIT_CONTENT_PERCENT = Scale.FIT_CONTENT_PERCENT
    AUTO = Scale.AUTO
    FLEX = Scale.FLEX


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
        if self.scale == Scale.AUTO:
            return "auto"
        elif self.scale == Scale.POINTS:
            return f"{self.value:.2f} pt" if not isnan(self.value) else "nan"
        elif self.scale == Scale.PERCENT:
            return f"{self.value*100:.2f} %" if not isnan(self.value) else "nan"
        elif self.scale == Scale.MIN_CONTENT:
            return "min-content"
        elif self.scale == Scale.MAX_CONTENT:
            return "max-content"
        elif self.scale == Scale.FIT_CONTENT_POINTS:
            value = f"{self.value:.2f} pt" if not isnan(self.value) else "nan"
            return f"fit-content({value})"
        elif self.scale == Scale.FIT_CONTENT_PERCENT:
            value = f"{self.value*100:.2f} %" if not isnan(self.value) else "nan"
            return f"fit-content({value})"
        elif self.scale == Scale.FLEX:
            return f"{self.value:.2f} fr" if not isnan(self.value) else "nan"
        else:
            return "None"

    @staticmethod
    def default() -> LengthBase:
        raise NotImplementedError

    @classmethod
    def from_any(cls, value: Any = None) -> LengthBase:
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
        if self.scale == Scale.POINTS:
            return self.value
        elif self.scale == Scale.PERCENT:
            if container is None:
                raise ValueError(
                    "Length scale is PERCENT, `container` dimension must be provided"
                )
            return self.value * container
        else:
            raise ValueError(
                "Length with scale %s cannot be represented in PTS" % self.scale
            )

    def __eq__(self, __value: object) -> bool:
        if not isinstance(__value, LengthBase):
            return False
        return self.scale == __value.scale and (
            self.value == __value.value or (isnan(self.value) and isnan(__value.value))
        )


class Length(LengthBase[Scale]):
    def __mul__(self, value):
        if self.scale not in (Scale.POINTS, Scale.PERCENT, Scale.FLEX):
            raise TypeError("Cannot multiply Length of type: " + str(self))
        elif not isinstance(value, (int, float)):
            raise ValueError("Cannot multiply with non-numeric value: " + str(value))
        return Length(self.scale, self.value * value)

    __rmul__ = __mul__

    @staticmethod
    def default() -> Length:
        return Length(Scale.AUTO)


class LengthAvailableSpace(LengthBase[AvailableSpace]):
    @staticmethod
    def definite(value: float | Length) -> LengthAvailableSpace:
        if value is None:
            raise TypeError("None value is not supported in this context")
        if issubclass(type(value), LengthBase) and value.scale != Scale.POINTS:
            raise ValueError(f"Only POINTS is supported in this context, not {value}")
        return LengthAvailableSpace(AvailableSpace.DEFINITE, value)

    @staticmethod
    def min_content() -> LengthAvailableSpace:
        return LengthAvailableSpace(AvailableSpace.MIN_CONTENT)

    @staticmethod
    def max_content() -> LengthAvailableSpace:
        return LengthAvailableSpace(AvailableSpace.MAX_CONTENT)

    @staticmethod
    def default() -> LengthAvailableSpace:
        return LengthAvailableSpace(AvailableSpace.MAX_CONTENT)

    @staticmethod
    def from_dict(value: dict[int, float]) -> LengthAvailableSpace:
        v = value["dim"]
        if v == Scale.POINTS:
            return LengthAvailableSpace.definite(value["value"])
        elif v == Scale.MIN_CONTENT:
            return LengthAvailableSpace.min_content()
        elif v == Scale.MAX_CONTENT:
            return LengthAvailableSpace.max_content()
        else:
            raise ValueError(f"Scale {v} is not supported in this context")


class LengthPoints(LengthBase[Points]):
    """
    A length in :py:obj:`Scale.POINTS <Scale>`.

    Parameters
    ----------
    scale : Points
    value : float

    """

    @staticmethod
    def points(value: float | Length = None) -> LengthPoints:
        """Returns length using :py:obj:`Scale.POINTS <Scale>`."""

        if value is None:
            value = NAN
        elif issubclass(type(value), LengthBase) and value.scale != Scale.POINTS:
            raise ValueError(f"Only POINTS is supported in this context, not {value}")
        return LengthPointsPercent(PointsPercent.POINTS, value)

    @staticmethod
    def default() -> LengthPoints:
        return LengthPoints()


class LengthPointsPercent(LengthBase[PointsPercent]):
    @staticmethod
    def points(value: float | Length) -> LengthPointsPercent:
        if value is None:
            value = NAN
        elif issubclass(type(value), LengthBase) and value.scale != Scale.POINTS:
            raise ValueError(f"Only POINTS is supported in this context, not {value}")
        return LengthPointsPercent(PointsPercent.POINTS, value)

    @staticmethod
    def percent(value: float | Length) -> LengthPointsPercent:
        if value is None:
            value = NAN
        elif issubclass(type(value), LengthBase) and value.scale != Scale.PERCENT:
            raise ValueError(f"Only PERCENT is supported in this context, not {value}")
        return LengthPointsPercent(PointsPercent.PERCENT, value)

    @staticmethod
    def default() -> LengthPointsPercent:
        return LengthPointsPercent(PointsPercent.POINTS)


class LengthPointsPercentAuto(LengthBase[PointsPercentAuto]):
    @staticmethod
    def points(value: float | Length) -> LengthPointsPercentAuto:
        if value is None:
            value = NAN
        elif issubclass(type(value), LengthBase) and value.scale != Scale.POINTS:
            raise ValueError(f"Only POINTS is supported in this context, not {value}")
        return LengthPointsPercentAuto(PointsPercent.POINTS, value)

    @staticmethod
    def percent(value: float | Length) -> LengthPointsPercentAuto:
        if value is None:
            value = NAN
        elif issubclass(type(value), LengthBase) and value.scale != Scale.PERCENT:
            raise ValueError(f"Only PERCENT is supported in this context, not {value}")
        return LengthPointsPercentAuto(PointsPercent.PERCENT, value)

    @staticmethod
    def auto() -> LengthPointsPercentAuto:
        return LengthPointsPercentAuto(PointsPercentAuto.AUTO)

    @staticmethod
    def default() -> LengthPointsPercentAuto:
        return LengthPointsPercentAuto(PointsPercentAuto.AUTO, NAN)


class LengthMinTrackSize(LengthBase[MinTrackSize]): ...


class LengthMaxTrackSize(LengthBase[MaxTrackSize]):
    @staticmethod
    def flex(value: float | Length) -> LengthMaxTrackSize:
        if value is None:
            value = NAN
        elif issubclass(type(value), LengthBase) and value.scale != Scale.FLEX:
            raise ValueError(f"Only FLEX is supported in this context, not {value}")
        return LengthMaxTrackSize(MaxTrackSize.FLEX, value)

    @staticmethod
    def fit_content(value: float | Length) -> LengthMaxTrackSize:
        if not isinstance(value, Length):
            value = LengthMaxTrackSize(MaxTrackSize.FIT_CONTENT_POINTS, value)
        elif value.scale == Scale.POINTS:
            value = LengthMaxTrackSize(MaxTrackSize.FIT_CONTENT_POINTS, value.value)
        elif value.scale == Scale.PERCENT:
            value = LengthMaxTrackSize(MaxTrackSize.FIT_CONTENT_PERCENT, value.value)
        elif (
            value.scale != Scale.FIT_CONTENT_PERCENT
            and value.scale != Scale.FIT_CONTENT_POINTS
        ):
            raise TypeError(f"{value} is not a valid value in this context")
        return value


AUTO = Length(Scale.AUTO)
PCT = Length(Scale.PERCENT, 0.01)
PT = Length(Scale.POINTS, 1)
FR = Length(Scale.FLEX, 1)
MIN_CONTENT = Length(Scale.MIN_CONTENT)
MAX_CONTENT = Length(Scale.MAX_CONTENT)
ZERO = Length(Scale.POINTS, 0)
