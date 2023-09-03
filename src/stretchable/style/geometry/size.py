from typing import Any, Generic, Self, TypeVar, get_args

from .length import (
    Length,
    LengthAvailableSpace,
    LengthPointsPercent,
    LengthPointsPercentAuto,
)

T = TypeVar("T")


class SizeBase(Generic[T]):
    _type_T: Any
    __slots__ = ("width", "height")

    def __init_subclass__(cls) -> None:
        cls._type_T = get_args(cls.__orig_bases__[0])[0]

    def __init__(self, width: T = None, height: T = None) -> None:
        self.width = self._type_T.from_any(width)
        self.height = self._type_T.from_any(height)

    def to_dict(self) -> dict[str, dict[str, float]]:
        return dict(
            width=self.width.to_dict(),
            height=self.height.to_dict(),
        )

    @classmethod
    def from_any(cls, value: Any = None) -> Self:
        if value is None:
            return cls()
        elif isinstance(value, cls):
            return value
        elif issubclass(type(value), SizeBase):
            # Return a new instance of cls, to cast to correct cls and ensure that
            # values uses supported scales
            return cls(value.width, value.height)

        # Check if value can be taken as 1-2 values defining the Size attributes
        values = (value,) if not isinstance(value, (list, tuple)) else value
        n = len(values)
        if n == 0:
            return cls()
        if n > 2:
            raise ValueError("A list or tuple with more than 2 values is not supported")

        # Parse values into T (this will raise an exception if any of the values are not supported)
        _values = [cls._type_T.from_any(v) for v in values]
        return cls(*_values) if n == 2 else cls(_values[0], _values[0])

    def __str__(self) -> str:
        return f"Size(width={str(self.width)}, height={str(self.height)})"


class Size(SizeBase[Length]):
    pass


class SizePointsPercent(SizeBase[LengthPointsPercent]):
    pass


class SizePointsPercentAuto(SizeBase[LengthPointsPercentAuto]):
    pass


class SizeAvailableSpace(SizeBase[LengthAvailableSpace]):
    pass
