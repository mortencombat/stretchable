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
