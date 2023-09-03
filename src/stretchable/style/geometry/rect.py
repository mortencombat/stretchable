from typing import Any, Generic, Self, TypeVar, get_args

from .length import Length

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
        # See current handling of this in dimension.py

        n = len(values)
        if n == 0:
            return cls()
        if n > 4:
            raise ValueError("A list or tuple with more than 4 values is not supported")

        # Parse values into T (this will raise an exception if any of the values are not supported)
        _values = [cls._type_T.from_any(v) for v in values]
        # TODO: consider if this interpretation of n-values should be moved to __init__ (including above scenarios n==0 and n>4)
        if n == 1:
            return cls(*(_values[0] * 4))
        elif n == 2:
            return cls(_values[0], _values[1], _values[0], _values[1])
        elif n == 3:
            return cls(_values[0], _values[1], _values[2], _values[1])
        else:
            return cls(*_values)

        self.top = self._type_T.from_any(top)
        self.right = self._type_T.from_any(right)
        self.bottom = self._type_T.from_any(bottom)
        self.left = self._type_T.from_any(left)

    def to_dict(self) -> dict[str, dict[str, float]]:
        return dict(
            top=self.top.to_dict(),
            right=self.right.to_dict(),
            bottom=self.bottom.to_dict(),
            left=self.left.to_dict(),
        )

    @classmethod
    def from_any(cls, value: Any = None) -> Self:
        if value is None:
            return cls()
        elif isinstance(value, cls):
            return value
        elif issubclass(type(value), RectBase):
            # Return a new instance of cls, to cast to correct cls and ensure that
            # values uses supported scales
            return cls(value.top, value.right, value.bottom, value.left)

        # Check if value can be taken as 1-4 values defining the Rect attributes
        values = (value,) if not isinstance(value, (list, tuple)) else value
        return cls(*values)

    def __str__(self) -> str:
        return f"Rect(left={self.left}, right={self.right}, top={self.top}, bottom={self.bottom})"


class Rect(RectBase[Length]):
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
