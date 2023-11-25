from __future__ import annotations

import logging
import re
from enum import Enum, IntEnum
from typing import Any, Iterable, Optional

from attrs import define, field, validators

from .. import taffylib
from .geometry import length, rect
from .geometry import size as _size
from .props import (
    AlignContent,
    AlignItems,
    AlignSelf,
    Display,
    FlexDirection,
    FlexWrap,
    GridAutoFlow,
    GridIndexType,
    GridPlacement,
    GridTrackSize,
    GridTrackSizing,
    JustifyContent,
    JustifyItems,
    JustifySelf,
    Overflow,
    Position,
    parse_value,
)

logging.basicConfig(format="%(levelname)s:%(name)s:%(message)s")
logger = logging.getLogger(__name__)

_ATTR_NAMES: dict[str, tuple[str]] = {
    "gap": ("column-gap", "row-gap"),
    "size": (),
    "max_size": ("max-width", "max-height"),
    "min_size": ("min-width", "min-height"),
    "inset": (),
}


def grid_template_from_any(value: Any) -> list[GridTrackSizing]:
    if not isinstance(value, (list, tuple)):
        value = [value]
    return [GridTrackSizing.from_any(v) for v in value]


def grid_auto_from_any(value: Any) -> list[GridTrackSize]:
    if not isinstance(value, (list, tuple)):
        value = [value]
    return [GridTrackSize.from_any(v) for v in value]


@define(frozen=True, kw_only=True)
class Style:
    """Style configuration for a node.

    Parameters
    ----------
    display
        Visibility and layout strategy
    position
        Positioning mode
    inset
        Position/inset of node edges
    align_items
        Used to control how child nodes are aligned, optional
    justify_items
        Used to control how child nodes are aligned
    align_self
    justify_self
    align_content
    justify_content
        ...
    gap
        ...

    """

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
    inset: rect.RectPointsPercentAuto = field(
        default=length.AUTO, converter=rect.RectPointsPercentAuto.from_any
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
    gap: _size.SizePointsPercent = field(
        default=0.0, converter=_size.SizePointsPercent.from_any
    )

    # Spacing
    padding: rect.RectPointsPercent = field(
        default=0.0, converter=rect.RectPointsPercent.from_any
    )
    border: rect.RectPointsPercent = field(
        default=0.0, converter=rect.RectPointsPercent.from_any
    )
    margin: rect.RectPointsPercentAuto = field(
        default=0.0, converter=rect.RectPointsPercentAuto.from_any
    )

    # Size
    size: _size.SizePointsPercentAuto = field(
        default=length.AUTO, converter=_size.SizePointsPercentAuto.from_any
    )
    min_size: _size.SizePointsPercentAuto = field(
        default=length.AUTO, converter=_size.SizePointsPercentAuto.from_any
    )
    max_size: _size.SizePointsPercentAuto = field(
        default=length.AUTO, converter=_size.SizePointsPercentAuto.from_any
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
    flex_basis: length.LengthPointsPercentAuto = field(
        default=length.AUTO, converter=length.LengthPointsPercentAuto.from_any
    )

    # Grid container
    grid_auto_flow: GridAutoFlow = field(
        default=GridAutoFlow.ROW,
        validator=[validators.instance_of(GridAutoFlow)],
    )
    grid_template_rows: list[GridTrackSizing] = field(
        default=None, converter=grid_template_from_any
    )
    grid_template_columns: list[GridTrackSizing] = field(
        default=None, converter=grid_template_from_any
    )
    grid_auto_rows: list[GridTrackSize] = field(
        default=None, converter=grid_auto_from_any
    )
    grid_auto_columns: list[GridTrackSize] = field(
        default=None, converter=grid_auto_from_any
    )

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
            [e.to_dict() for e in self.grid_template_rows],
            [e.to_dict() for e in self.grid_template_columns],
            [e.to_dict() for e in self.grid_auto_rows],
            [e.to_dict() for e in self.grid_auto_columns],
            self.grid_auto_flow,
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

    def _str(self, args: Optional[tuple[str]] = None) -> str:
        entries = []
        for arg in dir(self):
            if arg.startswith("_"):
                continue
            if args and arg not in args:
                continue
            value = getattr(self, arg)
            if arg in _ATTR_NAMES:
                entries.append(value._str(*_ATTR_NAMES[arg], include_class=False))
                continue
            if isinstance(value, Enum):
                value = value._name_.lower()
            elif isinstance(value, (tuple, list)):
                value = " ".join(str(v) for v in value)
            else:
                value = str(value)
            entries.append(f"{arg.replace('_', '-')}: {value}")
        return "Style(" + "; ".join(entries) + ")"

    def __str__(self) -> str:
        return self._str()

    @staticmethod
    def from_inline(style: str) -> Style:
        def parse_style(style: str) -> dict[str, length.Length | str]:
            props = dict()
            for entry in style.split(";"):
                entry = entry.strip()
                if not entry:
                    continue
                name, _, value = entry.partition(":")
                if not name.startswith("grid-"):
                    value = parse_value(value)
                props[name.strip()] = value
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
            default: length.Length = length.NAN,
            suffix: Iterable[str] = None,
            start: Iterable[str] = ("left", "start"),
            end: Iterable[str] = ("right", "end"),
            top: Iterable[str] = ("top",),
            bottom: Iterable[str] = ("bottom",),
        ) -> rect.Rect:
            if prefix:
                for s in (None, suffix) if suffix else (None,):
                    prop = get_prop_name(prefix, None, s)
                    if prop in keys:
                        keys.remove(prop)
                        values = props[prop]
                        try:
                            return rect.Rect(*values)
                        except TypeError:
                            return rect.Rect(values)

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
            return rect.Rect(*values)

        def to_size(
            prefix: str = None, *, default: length.Length = length.AUTO
        ) -> _size.Size:
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
            return _size.Size(*values)

        def to_gap() -> _size.Size:
            width, height = None, None
            for prefix in (None, "row", "column"):
                prop = prefix + "-gap" if prefix else "gap"
                if prop not in keys:
                    continue
                value = props[prop]
                keys.remove(prop)
                if isinstance(value, tuple) and len(value) == 2:
                    width, height = value
                else:
                    if prefix is None or prefix == "row":
                        height = value
                    if prefix is None or prefix == "column":
                        width = value
            if width is None and height is None:
                return None
            return _size.Size(
                width=width if width is not None else 0,
                height=height if height is not None else 0,
            )

        def prop_to_enum(prop: str) -> IntEnum:
            match prop:
                case "display":
                    return Display
                case "justify-content":
                    return JustifyContent
                case "justify-items":
                    return JustifyItems
                case "justify-self":
                    return JustifySelf
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
                case "grid-auto-flow":
                    return GridAutoFlow
            raise ValueError(f"Unrecognized property '{prop}'")

        def to_enum(prop: str) -> IntEnum:
            if prop in keys:
                keys.remove(prop)
                enum = prop_to_enum(prop)
                return enum[props[prop].strip().upper().replace("-", "_")]

        def to_float(prop: str) -> float:
            if prop in keys:
                keys.remove(prop)
                return props[prop]

        def to_flex() -> dict[str, length.Length | float]:
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

        def to_grid() -> dict[str, Any]:
            def split_parts(value: str) -> list[str]:
                # Remove any spaces trailing the separator
                value = value.strip().replace(", ", ",")
                # Split into parts
                return re.split(" (?![^(,]*\\))", value)

            parsed = dict()
            for suffix in ("row", "column"):
                # grid_template_rows/columns
                prop = f"grid-template-{suffix}s"
                if prop in keys:
                    try:
                        value = props[prop]
                        parsed[prop.replace("-", "_")] = [
                            GridTrackSizing.from_inline(v) for v in split_parts(value)
                        ]
                        keys.remove(prop)
                    except ValueError:
                        logger.warning(
                            f"Style property {prop}: {value} could not be parsed"
                        )

                # grid-auto-rows/columns
                prop = f"grid-auto-{suffix}s"
                if prop in keys:
                    try:
                        value = props[prop]
                        parsed[prop.replace("-", "_")] = [
                            GridTrackSize.from_inline(v) for v in split_parts(value)
                        ]
                        keys.remove(prop)
                    except ValueError:
                        logger.warning(
                            f"Style property {prop}: {value} could not be parsed"
                        )

                # grid-row/column
                prop = f"grid-{suffix}"
                if prop in keys:
                    value = props[prop]
                    try:
                        parsed[prop.replace("-", "_")] = GridPlacement.from_inline(
                            props[prop]
                        )
                        keys.remove(prop)
                    except ValueError:
                        logger.warning(
                            f"Style property {prop}: {value} could not be parsed"
                        )

            return parsed

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

        grid entries:
            ...

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
        v = to_gap()
        if v:
            args["gap"] = v

        # Rect entries: inset, margin, border, padding
        for prop in ("inset", "margin", "border", "padding"):
            prefix, suffix = (None, None) if prop == "inset" else (prop, "width")
            v = to_rect(
                prefix, suffix=suffix, default=length.AUTO if prop == "inset" else 0
            )
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
            "justify-items",
            "justify-self",
            "justify-content",
            "position",
            "grid-auto-flow",
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

        # Special handling for grid properties
        v = to_grid()
        if v:
            args.update(**v)

        # If there are any keys left, these are unrecognized/unsupported
        if len(keys) > 0:
            for key in keys:
                logger.warning(f"Style property {key} is not recognized/supported")

        # values = []
        # for value in args.values():
        #     if isinstance(value, (tuple, list)):
        #         value = " ".join(str(e) for e in value)
        #     elif isinstance(value, Enum):
        #         value = value._name_.lower().replace("_", "-")
        #     else:
        #         value = str(value)
        #     values.append(value)

        # logger.debug(
        #     "from_inline('%s') => "
        #     + "; ".join([name.replace("_", "-") + ": %s" for name in args.keys()]),
        #     style,
        #     *values,
        # )

        s = Style(**args)
        logger.debug("from_inline('%s') => %s", style, s._str(args.keys()))
        return s
