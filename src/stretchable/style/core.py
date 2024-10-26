from __future__ import annotations

import logging
import re
from enum import Enum, IntEnum
from typing import Any, Iterable, Optional

from attrs import define, field, validators

from .geometry import length, rect
from .geometry import size as _size
from .props import (
    AlignContent,
    AlignItems,
    AlignSelf,
    BoxSizing,
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
    boxsizing
        Sizing style application
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

    # Sizing styles application
    box_sizing: BoxSizing = field(
        default=BoxSizing.BORDER,
        validator=[validators.instance_of(BoxSizing)],
    )

    # Overflow
    overflow_x: Overflow = field(
        default=Overflow.VISIBLE,
        validator=[validators.instance_of(Overflow)],
    )
    overflow_y: Overflow = field(
        default=Overflow.VISIBLE,
        validator=[validators.instance_of(Overflow)],
    )
    scrollbar_width: float = 0.0

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

    # __ptr: int = field(init=False, default=None)

    def to_dict(self) -> dict[str, Any]:
        return dict(
            # Layout/sizing mode
            display=self.display,
            box_sizing=self.box_sizing,
            # Overflow
            overflow_x=self.overflow_x,
            overflow_y=self.overflow_y,
            scrollbar_width=self.scrollbar_width,
            # Position
            position=self.position,
            inset=self.inset.to_dict(),
            # Alignment
            gap=self.gap.to_dict(),
            # Spacing
            margin=self.margin.to_dict(),
            border=self.border.to_dict(),
            padding=self.padding.to_dict(),
            # Size
            size=self.size.to_dict(),
            min_size=self.min_size.to_dict(),
            max_size=self.max_size.to_dict(),
            # Flex
            flex_wrap=self.flex_wrap,
            flex_direction=self.flex_direction,
            flex_grow=self.flex_grow,
            flex_shrink=self.flex_shrink,
            flex_basis=self.flex_basis.to_dict(),
            # Grid container
            grid_template_rows=[e.to_dict() for e in self.grid_template_rows],
            grid_template_columns=[e.to_dict() for e in self.grid_template_columns],
            grid_auto_rows=[e.to_dict() for e in self.grid_auto_rows],
            grid_auto_columns=[e.to_dict() for e in self.grid_auto_columns],
            grid_auto_flow=self.grid_auto_flow,
            # Grid child
            grid_row=self.grid_row.to_dict(),
            grid_column=self.grid_column.to_dict(),
            # Size, optional
            aspect_ratio=self.aspect_ratio,
            # Alignment, optional
            align_items=self.align_items,
            justify_items=self.justify_items,
            align_self=self.align_self,
            justify_self=self.justify_self,
            align_content=self.align_content,
            justify_content=self.justify_content,
        )

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
            if prop == "display":
                return Display
            elif prop == "box-sizing":
                return BoxSizing
            elif prop == "overflow":
                return Overflow
            elif prop == "justify-content":
                return JustifyContent
            elif prop == "justify-items":
                return JustifyItems
            elif prop == "justify-self":
                return JustifySelf
            elif prop == "align-items":
                return AlignItems
            elif prop == "align-self":
                return AlignSelf
            elif prop == "align-content":
                return AlignContent
            elif prop == "flex-direction":
                return FlexDirection
            elif prop == "position":
                return Position
            elif prop == "flex-wrap":
                return FlexWrap
            elif prop == "grid-auto-flow":
                return GridAutoFlow
            raise ValueError(f"Unrecognized property '{prop}'")

        def to_enum(prop: str) -> IntEnum:
            if prop in keys:
                keys.remove(prop)
                enum = prop_to_enum(prop)
                return enum[
                    props[prop].strip().upper().replace("-", "_").replace(" ", "_")
                ]

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

        def to_overflow() -> dict[str, Any]:
            values = [None, None]

            # First look for 'overflow' which can be a single value (overflow-x == overflow_y) or two values
            if "overflow" in keys:
                value = props["overflow"].strip()
                values = value.split(" ")
                n = len(values)
                if n == 1:
                    values = values * 2
                elif n > 2:
                    logger.warning(
                        f"Style property overflow: {value} could not be parsed"
                    )
                keys.remove("overflow")

            # Then look for 'overflow-x' and 'overflow-y' (eg. these will override if overflow is also present)
            for i, prop in enumerate(("overflow-x", "overflow-y")):
                if prop not in keys:
                    continue
                values[i] = props[prop]
                keys.remove(prop)

            # Translate str values into corresponding enums and insert into dictionary
            r = dict()
            for prop, value in zip(("overflow_x", "overflow_y"), values):
                if not value:
                    continue
                r[prop] = Overflow[value.strip().upper()]
            return r

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
            "box-sizing",
            "flex-direction",
            "flex-wrap",
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
        for prop in (
            "flex-basis",
            "flex-grow",
            "flex-shrink",
            "aspect-ratio",
            "scrollbar-width",
        ):
            v = to_float(prop)
            if v is not None:
                args[prop.replace("-", "_")] = v

        # Special handling for flex property
        v = to_flex()
        if v:
            args.update(**v)

        # Special handling for overflow/overflow-x/overflow-y properties
        v = to_overflow()
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
