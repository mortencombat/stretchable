import logging
from enum import IntEnum

from attrs import define, field, validators

from stretchable.taffy import _bindings

from .dimensions import AUTO, Dim, DimensionValue, Rect, Size
from .enums import (
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
    # display: Display = field(
    #     default=Display.FLEX,
    #     validator=[validators.instance_of(Display)],
    # )
    # position: Position = field(
    #     default=Position.RELATIVE,
    #     validator=[validators.instance_of(Position)],
    # )
    # inset: Rect | Dim = field(factory=Rect, converter=Rect.from_value)
    # margin: Rect | Dim = field(factory=Rect, converter=Rect.from_value)
    # padding: Rect | Dim = field(factory=Rect, converter=Rect.from_value)
    # border: Rect | Dim = field(factory=Rect, converter=Rect.from_value)
    # size: Size = field(factory=Size)
    # min_size: Size = field(factory=Size)
    # max_size: Size = field(factory=Size)
    aspect_ratio: float = field(default=None)

    # Alignment
    align_items: AlignItems = field(
        default=AlignItems.STRETCH,
        validator=[validators.optional(validators.instance_of(AlignItems))],
    )
    justify_items: JustifyItems = field(
        default=JustifyItems.STRETCH,
        validator=[validators.optional(validators.instance_of((JustifyItems, None)))],
    )
    align_self: AlignSelf = field(
        default=None,
        validator=[validators.optional(validators.instance_of((AlignSelf, None)))],
    )
    justify_self: JustifySelf = field(
        default=None,
        validator=[validators.optional(validators.instance_of((JustifySelf, None)))],
    )
    align_content: AlignContent = field(
        default=None,
        validator=[validators.optional(validators.instance_of((AlignContent, None)))],
    )
    justify_content: JustifyContent = field(
        default=None,
        validator=[validators.optional(validators.instance_of((JustifyContent, None)))],
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
    flex_basis: Dim = field(default=AUTO, converter=DimensionValue.from_value)

    # Grid

    _ptr: int = field(init=False, default=None)

    def __attrs_post_init__(self):
        object.__setattr__(
            self,
            "_ptr",
            _bindings.taffy_style_create(
                self.align_items,
                self.justify_items,
                self.align_self,
                self.justify_self,
                self.align_content,
                self.justify_content,
                self.aspect_ratio,
            ),
        )
        logger.debug("taffy_style_create -> %s", self._ptr)

    def __del__(self):
        if self._ptr:
            _bindings.taffy_style_drop(self._ptr)
            logger.debug("taffy_style_drop(%s)", self._ptr)
