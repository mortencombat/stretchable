from __future__ import annotations

from typing import Any, Generic, TypeVar, get_args

from .length import (
    MAX_CONTENT,
    Length,
    LengthAvailableSpace,
    LengthPoints,
    LengthPointsPercent,
    LengthPointsPercentAuto,
)

T = TypeVar("T")


class SizeBase(Generic[T]):
    _type_T: Any
    __slots__ = ("width", "height")

    def __init_subclass__(cls) -> None:
        cls._type_T = get_args(cls.__orig_bases__[0])[0]

    def __init__(self, *values: T, width: T = None, height: T = None) -> None:
        n = len(values)
        if width or height:
            if n > 0:
                raise Exception("Use either positional or named values, not both")
        elif n > 2:
            raise ValueError("More than 2 values is not supported")
        elif n == 0:
            width = height = None
        elif n == 1:
            width = height = values[0]
        else:
            width, height = values
        self.width: T = self._type_T.from_any(width)
        self.height: T = self._type_T.from_any(height)

    def to_dict(self) -> dict[str, dict[str, float]]:
        return dict(
            width=self.width.to_dict(),
            height=self.height.to_dict(),
        )

    @classmethod
    def from_any(cls, value: Any = None) -> SizeBase:
        if value is None:
            return cls()
        elif isinstance(value, cls):
            return value
        elif issubclass(type(value), SizeBase):
            # Return a new instance of cls, to cast to correct cls and ensure that
            # values uses supported scales
            return cls(value.width, value.height)
        elif isinstance(value, (list, tuple)):
            return cls(*value)
        else:
            return cls(value)

    @classmethod
    def default(cls) -> SizeBase:
        raise NotImplementedError

    def _str(
        self, width: str = "width", height: str = "height", include_class: bool = True
    ) -> str:
        v = "; ".join(
            f"{label}: {value}"
            for label, value in ((width, self.width), (height, self.height))
        )
        if include_class:
            v = f"Size({v})"
        return v

    def __str__(self) -> str:
        return self._str()

    def __eq__(self, __value: object) -> bool:
        if not isinstance(__value, SizeBase):
            return False
        return self.width == __value.width and self.height == __value.height


class Size(SizeBase[Length]):
    pass


class SizePoints(SizeBase[LengthPoints]):
    pass


class SizePointsPercent(SizeBase[LengthPointsPercent]):
    pass


class SizePointsPercentAuto(SizeBase[LengthPointsPercentAuto]):
    pass


class SizeAvailableSpace(SizeBase[LengthAvailableSpace]):
    @classmethod
    def default(cls) -> SizeAvailableSpace:
        return SizeAvailableSpace(MAX_CONTENT)
