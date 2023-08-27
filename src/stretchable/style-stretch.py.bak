import warnings
from enum import IntEnum
from math import isnan
from typing import Generic, Iterable, Self, TypeVar

from attrs import define, field, validators

from .stretch import _bindings

SCALING_FACTOR: int = 1000


class AlignItems(IntEnum):
    FLEX_START: int = 0
    FLEX_END: int = 1
    CENTER: int = 2
    BASELINE: int = 3
    STRETCH: int = 4


class AlignSelf(IntEnum):
    AUTO: int = 0
    FLEX_START: int = 1
    FLEX_END: int = 2
    CENTER: int = 3
    BASELINE: int = 4
    STRETCH: int = 5


class AlignContent(IntEnum):
    FLEX_START: int = 0
    FLEX_END: int = 1
    CENTER: int = 2
    STRETCH: int = 3
    SPACE_BETWEEN: int = 4
    SPACE_AROUND: int = 5


class Direction(IntEnum):
    INHERIT: int = 0
    LTR: int = 1
    RTL: int = 2


class Display(IntEnum):
    FLEX: int = 0
    NONE: int = 1


class FlexDirection(IntEnum):
    ROW: int = 0
    COLUMN: int = 1
    ROW_REVERSE: int = 2
    COLUMN_REVERSE: int = 3


class JustifyContent(IntEnum):
    FLEX_START: int = 0
    FLEX_END: int = 1
    CENTER: int = 2
    SPACE_BETWEEN: int = 3
    SPACE_AROUND: int = 4
    SPACE_EVENLY: int = 5


class Overflow(IntEnum):
    VISIBLE: int = 0
    HIDDEN: int = 1
    SCROLL: int = 2


class PositionType(IntEnum):
    RELATIVE: int = 0
    ABSOLUTE: int = 1


class FlexWrap(IntEnum):
    NO_WRAP: int = 0
    WRAP: int = 1
    WRAP_REVERSE: int = 2


class Dimension(IntEnum):
    UNDEFINED: int = 0
    AUTO: int = 1
    POINTS: int = 2
    PERCENT: int = 3


T = TypeVar("T")


class ValueConversionError(Exception):
    pass


@define(frozen=True)
class DimensionValue(Generic[T]):
    unit: Dimension = Dimension.UNDEFINED
    value: float = float("nan")

    def to_stretch(self) -> dict:
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

    def to_stretch(self) -> dict[str, float]:
        return dict(
            width=self.width.to_stretch(),
            height=self.height.to_stretch(),
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

    def to_stretch(self) -> dict[str, float]:
        return dict(
            start=self.start.to_stretch(),
            end=self.end.to_stretch(),
            top=self.top.to_stretch(),
            bottom=self.bottom.to_stretch(),
        )

    def __str__(self) -> str:
        return f"Rect(start={self.start}, end={self.end}, top={self.top}, bottom={self.bottom})"


@define(frozen=True)
class Style:
    display: Display = Display.FLEX
    position_type: PositionType = PositionType.RELATIVE
    direction: Direction = Direction.INHERIT
    flex_direction: FlexDirection = FlexDirection.ROW
    flex_wrap: FlexWrap = FlexWrap.NO_WRAP
    overflow: Overflow = Overflow.HIDDEN
    align_items: AlignItems = AlignItems.STRETCH
    align_self: AlignSelf = AlignSelf.AUTO
    align_content: AlignContent = AlignContent.STRETCH
    justify_content: JustifyContent = field(
        default=JustifyContent.FLEX_START,
        validator=[validators.instance_of(JustifyContent)],
    )
    position: Rect = field(factory=Rect, converter=Rect.from_value)
    margin: Rect | Dim = field(factory=Rect, converter=Rect.from_value)
    padding: Rect | Dim = field(factory=Rect, converter=Rect.from_value)
    border: Rect | Dim = field(factory=Rect, converter=Rect.from_value)
    flex_grow: float = 0.0
    flex_shrink: float = 1.0
    flex_basis: Dim = field(default=AUTO, converter=DimensionValue.from_value)
    size: Size = field(factory=Size)
    min_size: Size = field(factory=Size)
    max_size: Size = field(factory=Size)
    aspect_ratio: float = field(default=None)

    @aspect_ratio.validator
    def check_aspect_ratio(self, attr, value):
        if not value:
            return
        elif not isinstance(value, (int, float)):
            raise TypeError(f"{attr.name} must be int or float")
        elif value <= 0:
            raise ValueError(f"{attr.name} must be > 0")

    # TODO:
    #   add validators for remaining attributes
    #   create methods to clone style with modified settings
    #   add tests to check that changing styles after node instancing has desired effect

    _ptr: int = field(init=False, default=None)

    def __attrs_post_init__(self):
        # object.__setattr__(self, "_Style__ptr", None)

        object.__setattr__(
            self,
            "_ptr",
            _bindings.stretch_style_create(
                display=self.display.value,
                position_type=self.position_type.value,
                direction=self.direction.value,
                flex_direction=self.flex_direction.value,
                flex_wrap=self.flex_wrap.value,
                overflow=self.overflow.value,
                align_items=self.align_items.value,
                align_self=self.align_self.value,
                align_content=self.align_content.value,
                justify_content=self.justify_content.value,
                position=self.position.to_stretch(),
                margin=self.margin.to_stretch(),
                padding=self.padding.to_stretch(),
                border=self.border.to_stretch(),
                flex_grow=self.flex_grow,
                flex_shrink=self.flex_shrink,
                flex_basis=self.flex_basis.to_stretch(),
                size=self.size.to_stretch(),
                min_size=self.min_size.to_stretch(),
                max_size=self.max_size.to_stretch(),
                aspect_ratio=self.aspect_ratio or NAN,
            ),
        )

    def __del__(self):
        if self._ptr:
            _bindings.stretch_style_free(self._ptr)

    @staticmethod
    def from_html_style(style: str) -> Self:
        def parse_value(value: str) -> Dim | float | str:
            value = value.strip()
            if value.endswith("px"):
                value = float(value.rstrip("px"))
            elif value.endswith("%"):
                value = float(value.rstrip("%")) * pct
            elif value.lower() == "auto":
                value = AUTO
            else:
                try:
                    value = float(value)
                except ValueError:
                    pass
            return value

        def parse_style(style: str) -> dict[str, Dim | str]:
            props = dict()
            for entry in style.split(";"):
                entry = entry.strip()
                if not entry:
                    continue
                name, _, value = entry.partition(":")
                props[name.strip()] = parse_value(value)
            return props

        def get_prop_name(prefix: str, key: str, suffix: str = None) -> str:
            if prefix:
                name = f"{prefix}-{key}" if key else prefix
            elif not key:
                raise ValueError("Either prefix or key must be specified")
            else:
                name = key
            if suffix:
                name += "-" + suffix
            return name

        def to_rect(
            prefix: str = None,
            *,
            default: Dim = UNDEF,
            suffix: Iterable[str] = None,
            start: Iterable[str] = ("left", "start"),
            end: Iterable[str] = ("right", "end"),
            top: Iterable[str] = ("top",),
            bottom: Iterable[str] = ("bottom",),
        ) -> Rect:
            if prefix:
                for s in (None, suffix):
                    prop = get_prop_name(prefix, None, s)
                    if prop in keys:
                        keys.remove(prop)
                        return Rect(props[prop])

            values = [default] * 4
            not_present = True
            for i, _keys in enumerate((top, end, bottom, start)):
                for key in _keys:
                    for s in (None, suffix):
                        prop = get_prop_name(prefix, key, s)
                        if prop in keys:
                            values[i] = props[prop]
                            keys.remove(prop)
                            not_present = False
            if not_present:
                return None
            return Rect(*values)

        def to_size(prefix: str = None, *, default: Dim = AUTO) -> Size:
            values = [default] * 2
            not_present = True
            for i, key in enumerate(("width", "height")):
                prop = get_prop_name(prefix, key)
                if prop in keys:
                    values[i] = props[prop]
                    keys.remove(prop)
                    not_present = False
            if not_present:
                return None
            return Size(*values)

        def prop_to_enum(prop: str) -> IntEnum:
            match prop:
                case "display":
                    return Display
                case "direction":
                    return Direction
                case "justify-content":
                    return JustifyContent
                case "align-items":
                    return AlignItems
                case "align-self":
                    return AlignSelf
                case "align-content":
                    return AlignContent
                case "flex-direction":
                    return FlexDirection
                case "overflow":
                    return Overflow
                case "position":
                    return PositionType
                case "flex-wrap":
                    return FlexWrap
            raise ValueError(f"Unrecognized enum property {prop}")

        def to_enum(prop: str) -> IntEnum:
            if prop in keys:
                keys.remove(prop)
                enum = prop_to_enum(prop)
                return enum[props[prop].upper().replace("-", "_")]

        def to_float(prop: str) -> float:
            if prop in keys:
                keys.remove(prop)
                return props[prop]

        def to_flex() -> dict[str, Dim | float]:
            if "flex" not in keys:
                return None

            v = props["flex"]
            if isinstance(v, str):
                values = [parse_value(value) for value in v.split(" ")]
            else:
                values = [v]
            n = len(values)
            keys.remove("flex")
            return dict(
                flex_grow=values[0],
                flex_shrink=values[1] if n >= 2 else 1,
                flex_basis=values[2] if n >= 3 else 0,
            )

        """
        Size entries:
            width, height                       -> size = Size
            max-width, max-height               -> max_size = Size
            min-width, min-height               -> min_size = Size

        Rect entries:
            top, right, bottom, left            -> position = Rect
            margin**, border**, padding**       -> margin = Rect, ...
                                                (margin, margin-width -> single value)
                                                (margin-left, etc. -> specific values)

        Enum entries:
            display, direction, flex-direction, flex-wrap, overflow,
            align-items, align-self, align-content, justify-content
                                                -> display = Display (etc.)
            position                            -> position_type = PositionType

        float entries:
            flex-grow, flex-shrink, aspect-ratio
                                                -> flex_grow (etc.)

        Dim entries:
            flex-basis                          -> flex_basis = Dim
        """

        args = dict()
        props = parse_style(style)
        keys = set(props.keys())

        # Size entries: size, max_size, min_size
        for prefix in (None, "min", "max"):
            v = to_size(prefix, default=AUTO if not prefix else UNDEF)
            if v:
                args[f"{prefix}_size" if prefix else "size"] = v

        # Rect entries: position, margin, border, padding
        for prop in ("position", "margin", "border", "padding"):
            prefix, suffix = (None, None) if prop == "position" else (prop, "width")
            v = to_rect(prefix, suffix=suffix)
            if v:
                args[prop] = v

        # Enum entries:
        #   display, direction, flex-direction, flex-wrap, overflow,
        #   align-items, align-self, align-content, justify-content
        #   position (->position_type)
        for prop in (
            "display",
            "direction",
            "flex-direction",
            "flex-wrap",
            "overflow",
            "align-items",
            "align-self",
            "align-content",
            "justify-content",
            "position",
        ):
            v = to_enum(prop)
            if v:
                args[
                    "position_type" if prop == "position" else prop.replace("-", "_")
                ] = v

        # float and Dim entries:
        #   flex-basis, flex-grow, flex-shrink, aspect-ratio
        for prop in ("flex-basis", "flex-grow", "flex-shrink", "aspect-ratio"):
            v = to_float(prop)
            if v is not None:
                args[prop.replace("-", "_")] = v

        # Special handling for flex property
        v = to_flex()
        if v:
            args.update(**v)

        # If there are any keys left, these are unrecognized/unsupported
        if len(keys) > 0:
            for key in keys:
                warnings.warn(f"Style property {key} is not recognized/supported")

        print(args)
        return Style(**args)
