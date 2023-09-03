from enum import IntEnum
from typing import Any, Generic, Self, TypeVar, get_args

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


class Percent(IntEnum):
    PERCENT = Scale.PERCENT


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
    __slots__ = ("_scale", "_value")

    def __init_subclass__(cls) -> None:
        cls._type_T = get_args(cls.__orig_bases__[0])[0]

    def __init__(self, scale: T = None, value: float = None) -> None:
        # Check if scale value corresponds to an allowed scale as defined by T.
        if scale:
            scale_ok = False
            for m in dir(self._type_T):
                if m.startswith("_") or not m[0].isupper():
                    continue
                v = getattr(self._type_T, m)
                if v == scale:
                    scale_ok = True
            if not scale_ok:
                raise TypeError(f"Scale {scale} is not allowed in this context")

        self._scale = scale
        self._value = value

    def __str__(self) -> str:
        match self._scale:
            case Scale.AUTO:
                return "auto"
            case Scale.POINTS:
                return f"{self._value:.2f} pt"
            case Scale.PERCENT:
                return f"{self._value*100:.2f} %"
            case Scale.MIN_CONTENT:
                return "min-content"
            case Scale.MAX_CONTENT:
                return "max-content"

    def from_any(value: Any) -> Self:
        raise NotImplementedError

    def to_dict(self) -> dict[str, int | float]:
        return dict(dim=self.scale.value, value=self.value)


class Length(LengthBase[Scale]):
    # This class supports all scales, as well as mul and rmul operations. It is
    # used to define constants that can be used as shorthand (fx AUTO) or for
    # multiplication (fx 5 * PCT) Other subclasses of Length should support
    # receiving an instance of this class as a value, but verifying that it is
    # of a supported scale.
    pass


class LengthAvailableSpace(LengthBase[AvailableSpace]):
    @staticmethod
    def definite(value: float | Length) -> Self:
        # TODO: If value type is Length, verify that it is a supported scale (POINTS)
        return LengthAvailableSpace(AvailableSpace.DEFINITE, value)

    @staticmethod
    def min_content() -> Self:
        return LengthAvailableSpace(AvailableSpace.MIN_CONTENT)

    @staticmethod
    def max_content() -> Self:
        return LengthAvailableSpace(AvailableSpace.MAX_CONTENT)

    @staticmethod
    def from_any(value: Any) -> Self:
        raise NotImplementedError


class LengthPointsPercent(LengthBase[PointsPercent]):
    def points(value: float | Length) -> Self:
        # TODO: If value type is Length, verify that it is a supported scale (POINTS)
        return LengthPointsPercent(PointsPercent.POINTS, value)

    def percent(value: float | Length) -> Self:
        # TODO: If value type is Length, verify that it is a supported scale (POINTS)
        return LengthPointsPercent(PointsPercent.PERCENT, value)

    @staticmethod
    def from_any(value: Any) -> Self:
        raise NotImplementedError


t1 = LengthAvailableSpace.definite(100)
print(t1)

t2 = LengthAvailableSpace.max_content()
print(t2)
