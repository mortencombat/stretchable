from typing import Any, Generic, Self, TypeVar, get_args

from attrs import define, field

T = TypeVar("T")


@define(frozen=True)
class Size(Generic[T]):
    width: T = field(default=AUTO, converter=T.from_value)
    height: T = field(default=AUTO, converter=T.from_value)

    def to_dict(self) -> dict[str, dict[str, float]]:
        return dict(
            width=self.width.to_dict(),
            height=self.height.to_dict(),
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
