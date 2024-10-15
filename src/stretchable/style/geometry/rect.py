from __future__ import annotations

from typing import Any, Generic, TypeVar, get_args

from .length import Length, LengthPointsPercent, LengthPointsPercentAuto

T = TypeVar("T")


class RectBase(Generic[T]):
    _type_T: Any
    __slots__ = ("top", "right", "bottom", "left")

    def __init_subclass__(cls) -> None:
        cls._type_T = get_args(cls.__orig_bases__[0])[0]

    def __init__(
        self,
        *values: T,
        top: T = None,
        right: T = None,
        bottom: T = None,
        left: T = None,
    ) -> None:
        n = len(values)
        if top or right or bottom or left:
            if n > 0:
                raise Exception("Use either positional or named values, not both")
        elif n > 4:
            raise ValueError("More than 4 values is not supported")
        elif n == 0:
            top = right = bottom = left = None
        elif n == 1:
            top = right = bottom = left = values[0]
        elif n == 2:
            top = bottom = values[0]
            left = right = values[1]
        elif n == 3:
            top = values[0]
            left = right = values[1]
            bottom = values[2]
        else:
            top, right, bottom, left = values
        self.top: T = self._type_T.from_any(top)
        self.right: T = self._type_T.from_any(right)
        self.bottom: T = self._type_T.from_any(bottom)
        self.left: T = self._type_T.from_any(left)

    def to_dict(self) -> dict[str, dict[str, float]]:
        return dict(
            top=self.top.to_dict(),
            right=self.right.to_dict(),
            bottom=self.bottom.to_dict(),
            left=self.left.to_dict(),
        )

    @classmethod
    def from_any(cls, value: Any = None) -> RectBase:
        if value is None:
            return cls()
        elif isinstance(value, cls):
            return value
        elif issubclass(type(value), RectBase):
            # Return a new instance of cls, to cast to correct cls and ensure that
            # values uses supported scales
            return cls(value.top, value.right, value.bottom, value.left)
        elif isinstance(value, (list, tuple)):
            return cls(*value)
        else:
            return cls(value)

    def _str(
        self,
        top: str = "top",
        right: str = "right",
        bottom: str = "bottom",
        left: str = "left",
        include_class: bool = True,
    ) -> str:
        v = "; ".join(
            f"{label}: {value}"
            for label, value in (
                (top, self.top),
                (right, self.right),
                (bottom, self.bottom),
                (left, self.left),
            )
        )
        if include_class:
            v = f"Rect({v})"
        return v

    def __str__(self) -> str:
        return self._str()


class Rect(RectBase[Length]):
    pass


class RectPointsPercent(RectBase[LengthPointsPercent]):
    pass


class RectPointsPercentAuto(RectBase[LengthPointsPercentAuto]):
    pass


# def from_css_attrs(
#     attributes: dict[str, Dim],
#     *,
#     prefix: str = None,
#     common: str = None,
#     left: str = "left",
#     right: str = "right",
#     top: str = "top",
#     bottom: str = "bottom",
#     default: Length = AUTO,
# ) -> Self:
#     def _get_attr_name(prefix: str, name: str) -> str:
#         return f"{prefix}-{name}" if prefix else name

#     if common:
#         name = _get_attr_name(prefix, common)
#         if name in attributes:
#             return Rect(attributes[name])
#     if prefix and prefix in attributes:
#         return Rect(attributes[prefix])

#     values = [default] * 4
#     no_attrs = True
#     for i, key in enumerate((top, right, bottom, left)):
#         name = _get_attr_name(prefix, key)
#         if name in attributes:
#             values[i] = attributes[name]
#             no_attrs = False
#     if no_attrs:
#         return None
#     return Rect(*values)
