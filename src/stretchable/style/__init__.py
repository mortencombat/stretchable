import logging
from enum import IntEnum

from attrs import define, field, validators

from stretchable.taffy import _bindings

from .dimension import AUTO, Dim, Length, Rect, Size
from .enum import (
    AlignContent,
    AlignItems,
    AlignSelf,
    Display,
    FlexDirection,
    FlexWrap,
    JustifyContent,
    JustifyItems,
    JustifySelf,
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

    # NOTE: validator here should enforce fields supporting Length / Percentage / Auto
    # Position
    position: Position = field(
        default=Position.RELATIVE,
        validator=[validators.instance_of(Position)],
    )
    # inset: Rect | Dim = field(factory=Rect, converter=Rect.from_value)

    # Size
    # size: Size = field(factory=Size)
    # min_size: Size = field(factory=Size)
    # max_size: Size = field(factory=Size)

    # Spacing
    # margin: Rect | Dim = field(factory=Rect, converter=Rect.from_value)
    # padding: Rect | Dim = field(factory=Rect, converter=Rect.from_value)
    # border: Rect | Dim = field(factory=Rect, converter=Rect.from_value)
    aspect_ratio: float = field(default=None)

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
    flex_basis: Length = field(default=AUTO, converter=Length.from_value)

    # Grid

    _ptr: int = field(init=False, default=None)

    def __attrs_post_init__(self):
        object.__setattr__(
            self,
            "_ptr",
            _bindings.taffy_style_create(
                self.display,
                self.position,
                self.align_items,
                self.justify_items,
                self.align_self,
                self.justify_self,
                self.align_content,
                self.justify_content,
                self.aspect_ratio,
                self.flex_wrap,
                self.flex_direction,
                self.flex_grow,
                self.flex_shrink,
                self.flex_basis.to_taffy(),
            ),
        )
        logger.debug("taffy_style_create -> %s", self._ptr)

    def __del__(self):
        if self._ptr:
            _bindings.taffy_style_drop(self._ptr)
            logger.debug("taffy_style_drop(%s)", self._ptr)
