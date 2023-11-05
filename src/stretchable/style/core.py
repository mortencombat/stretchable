import logging
from enum import IntEnum
from typing import Iterable, Self

from attrs import define, field, validators

from .. import taffylib
from .geometry.length import AUTO, NAN, PCT, PT, Length, LengthPointsPercentAuto
from .geometry.rect import Rect, RectPointsPercent, RectPointsPercentAuto
from .geometry.size import Size, SizePointsPercent, SizePointsPercentAuto
from .props import (
    AlignContent,
    AlignItems,
    AlignSelf,
    Display,
    FlexDirection,
    FlexWrap,
    GridAutoFlow,
    GridPlacement,
    JustifyContent,
    JustifyItems,
    JustifySelf,
    Overflow,
    Position,
)

logging.basicConfig(format="%(levelname)s:%(name)s:%(message)s")
logger = logging.getLogger(__name__)


def to_css_prop_name(enum: IntEnum) -> str:
    raise NotImplementedError


def to_css_prop_value(enum: IntEnum) -> str:
    raise NotImplementedError


@define(frozen=True)
class Style:
    # Layout mode/strategy
    display: Display = field(
        default=Display.FLEX,
        validator=[validators.instance_of(Display)],
    )

    # Position
    position: Position = field(
        default=Position.RELATIVE,
        validator=[validators.instance_of(Position)],
    )
    inset: RectPointsPercentAuto = field(
        default=AUTO, converter=RectPointsPercentAuto.from_any
    )

    # Alignment
    align_items: AlignItems = field(
        default=None,
        validator=[validators.optional(validators.instance_of(AlignItems))],
    )
    justify_items: JustifyItems = field(
        default=None,
        validator=[validators.optional(validators.instance_of(JustifyItems))],
    )
    align_self: AlignSelf = field(
        default=None,
        validator=[validators.optional(validators.instance_of(AlignSelf))],
    )
    justify_self: JustifySelf = field(
        default=None,
        validator=[validators.optional(validators.instance_of(JustifySelf))],
    )
    align_content: AlignContent = field(
        default=None,
        validator=[validators.optional(validators.instance_of(AlignContent))],
    )
    justify_content: JustifyContent = field(
        default=None,
        validator=[validators.optional(validators.instance_of(JustifyContent))],
    )
    gap: SizePointsPercent = field(default=0.0, converter=SizePointsPercent.from_any)

    # Spacing
    margin: RectPointsPercentAuto = field(
        default=0.0, converter=RectPointsPercentAuto.from_any
    )
    padding: RectPointsPercent = field(
        default=0.0, converter=RectPointsPercent.from_any
    )
    border: RectPointsPercent = field(default=0.0, converter=RectPointsPercent.from_any)

    # Size
    size: SizePointsPercentAuto = field(
        default=AUTO, converter=SizePointsPercentAuto.from_any
    )
    min_size: SizePointsPercentAuto = field(
        default=AUTO, converter=SizePointsPercentAuto.from_any
    )
    max_size: SizePointsPercentAuto = field(
        default=AUTO, converter=SizePointsPercentAuto.from_any
    )
    aspect_ratio: float = field(default=None)

    # Flex
    flex_wrap: FlexWrap = field(
        default=FlexWrap.NO_WRAP,
        validator=[validators.instance_of(FlexWrap)],
    )
    flex_direction: FlexDirection = field(
        default=FlexDirection.ROW,
        validator=[validators.instance_of(FlexDirection)],
    )
    flex_grow: float = 0.0
    flex_shrink: float = 1.0
    flex_basis: LengthPointsPercentAuto = field(
        default=AUTO, converter=LengthPointsPercentAuto.from_any
    )

    # TODO: Grid container
    grid_auto_flow: GridAutoFlow = field(
        default=GridAutoFlow.ROW,
        validator=[validators.instance_of(GridAutoFlow)],
    )
    # grid_template_rows (defines the width of the grid rows)
    #   GridTrackVec<TrackSizingFunction>
    # grid_template_columns (defines the heights of the grid columns)
    #   GridTrackVec<TrackSizingFunction>
    # grid_auto_rows (defines the size of implicitly created rows)
    #   GridTrackVec<NonRepeatedTrackSizingFunction>
    # grid_auto_columns (defines the size of implicitly created columns)
    #   GridTrackVec<NonRepeatedTrackSizingFunction>
    # GridTrackVec: A vector of grid tracks (defined in taffy::util::sys)

    # Grid child
    grid_row: GridPlacement = field(
        factory=GridPlacement, converter=GridPlacement.from_any
    )
    grid_column: GridPlacement = field(
        factory=GridPlacement, converter=GridPlacement.from_any
    )

    __ptr: int = field(init=False, default=None)

    def to_args(self) -> tuple:
        return (
            # Layout mode
            self.display,
            # Position
            self.position,
            self.inset.to_dict(),
            # Alignment
            self.gap.to_dict(),
            # Spacing
            self.margin.to_dict(),
            self.border.to_dict(),
            self.padding.to_dict(),
            # Size
            self.size.to_dict(),
            self.min_size.to_dict(),
            self.max_size.to_dict(),
            # Flex
            self.flex_wrap,
            self.flex_direction,
            self.flex_grow,
            self.flex_shrink,
            self.flex_basis.to_dict(),
            # Grid container
            self.grid_auto_flow,
            # grid_template_rows
            # grid_template_columns
            # grid_auto_rows
            # grid_auto_columns
            # Grid child
            self.grid_row.to_dict(),
            self.grid_column.to_dict(),
            # Size, optional
            self.aspect_ratio,
            # Alignment, optional
            self.align_items,
            self.justify_items,
            self.align_self,
            self.justify_self,
            self.align_content,
            self.justify_content,
        )

    def __attrs_post_init__(self) -> None:
        object.__setattr__(self, "_Style__ptr", taffylib.style_create(*self.to_args()))
        logger.debug("style_create() -> %s" % self.__ptr)

    def __del__(self) -> None:
        if self.__ptr is None:
            return
        taffylib.style_drop(self.__ptr)
        logger.debug("style_drop(ptr: %s)", self.__ptr)

    @property
    def _ptr(self) -> int:
        return self.__ptr

    @staticmethod
    def from_inline(style: str) -> Self:
        def parse_value(value: str) -> Length | float | str | tuple[Length]:
            def parse_single(val: str) -> Length | float | str:
                val = val.strip()
                if val.endswith("px"):
                    val = float(val.rstrip("px")) * PT
                elif val.endswith("%"):
                    val = float(val.rstrip("%")) * PCT
                elif val.lower() == "auto":
                    val = AUTO
                else:
                    try:
                        val = float(val)
                    except ValueError:
                        pass
                return val

            value = value.strip()
            if " " in value:
                return tuple(parse_single(v) for v in value.split(" "))
            else:
                return parse_single(value)

        def parse_style(style: str) -> dict[str, Length | str]:
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
            default: Length = NAN,
            suffix: Iterable[str] = None,
            start: Iterable[str] = ("left", "start"),
            end: Iterable[str] = ("right", "end"),
            top: Iterable[str] = ("top",),
            bottom: Iterable[str] = ("bottom",),
        ) -> Rect:
            if prefix:
                for s in (None, suffix) if suffix else (None,):
                    prop = get_prop_name(prefix, None, s)
                    if prop in keys:
                        keys.remove(prop)
                        values = props[prop]
                        try:
                            return Rect(*values)
                        except TypeError:
                            return Rect(values)

            values = [default] * 4
            not_present = True
            for i, _keys in enumerate((top, end, bottom, start)):
                for key in _keys:
                    for s in (None, suffix) if suffix else (None,):
                        prop = get_prop_name(prefix, key, s)
                        if prop in keys:
                            values[i] = props[prop]
                            keys.remove(prop)
                            not_present = False
            if not_present:
                return None
            return Rect(*values)

        def to_size(prefix: str = None, *, default: Length = AUTO) -> Size:
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

        def to_gap() -> Size:
            gap = SizePointsPercent.from_any(0)
            for prefix in (None, "row", "column"):
                prop = prefix + "-gap" if prefix else "gap"
                if prop in keys:
                    value = props[prop]
                    keys.remove(prop)
                    if prefix is None or prefix == "row":
                        gap.height = value
                    if prefix is None or prefix == "column":
                        gap.width = value
            return gap

        def prop_to_enum(prop: str) -> IntEnum:
            match prop:
                case "display":
                    return Display
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
                    return Position
                case "flex-wrap":
                    return FlexWrap
            raise ValueError(f"Unrecognized property '{prop}'")

        def to_enum(prop: str) -> IntEnum:
            if prop in keys:
                keys.remove(prop)
                enum = prop_to_enum(prop)
                return enum[props[prop].upper().replace("-", "_")]

        def to_float(prop: str) -> float:
            if prop in keys:
                keys.remove(prop)
                return props[prop]

        def to_flex() -> dict[str, Length | float]:
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
            gap, row-gap, column-gap            -> gap = Size

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
            v = to_size(prefix)
            if v:
                args[f"{prefix}_size" if prefix else "size"] = v

        # Row/column gap
        args["gap"] = to_gap()

        # Rect entries: inset, margin, border, padding
        for prop in ("inset", "margin", "border", "padding"):
            prefix, suffix = (None, None) if prop == "inset" else (prop, "width")
            v = to_rect(prefix, suffix=suffix, default=AUTO if prop == "inset" else 0)
            if v:
                args[prop] = v

        # Enum entries:
        #   display, flex-direction, flex-wrap, overflow,
        #   align-items, align-self, align-content, justify-content
        #   position (->position_type)
        for prop in (
            "display",
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
            if v is not None:
                args[prop.replace("-", "_")] = v

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
                logger.warning(f"Style property {key} is not recognized/supported")

        logger.debug(
            "from_inline('%s') => " + "; ".join([name + "=%s" for name in args.keys()]),
            style,
            *args.values(),
        )
        return Style(**args)
