import logging
from enum import IntEnum

from attrs import define, field, validators

from stretchable.taffy import _bindings

from .dimension import AUTO, Length, Rect, Size
from .enum import (
    AlignContent,
    AlignItems,
    AlignSelf,
    Display,
    FlexDirection,
    FlexWrap,
    GridAutoFlow,
    JustifyContent,
    JustifyItems,
    JustifySelf,
    Position,
)
from .grid import GridPlacement

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

    # TODO: validators here should enforce fields supporting only Length/Percentage or Length/Percentage/Auto

    # Position
    position: Position = field(
        default=Position.RELATIVE,
        validator=[validators.instance_of(Position)],
    )
    inset: Rect = field(factory=Rect, converter=Rect.from_value)

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
    gap: Size = field(default=0.0, converter=Size.from_value)

    # Spacing
    margin: Rect = field(default=0.0, converter=Rect.from_value)
    padding: Rect = field(default=0.0, converter=Rect.from_value)
    border: Rect = field(default=0.0, converter=Rect.from_value)

    # Size
    size: Size = field(factory=Size, converter=Size.from_value)
    min_size: Size = field(factory=Size, converter=Size.from_value)
    max_size: Size = field(factory=Size, converter=Size.from_value)
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
    flex_basis: Length = field(default=AUTO, converter=Length.from_value)

    # TODO: Grid container
    grid_auto_flow: GridAutoFlow = field(
        default=GridAutoFlow.ROW,
        validator=[validators.instance_of(GridAutoFlow)],
    )
    # grid_template_rows (defines the width of the grid rows)
    #   GridTrackVec<TrackSizingFunction>
    #
    #
    # grid_template_columns (defines the heights of the grid columns)
    #   GridTrackVec<TrackSizingFunction>
    #
    # grid_auto_rows (defines the size of implicitly created rows)
    #   GridTrackVec<NonRepeatedTrackSizingFunction>
    #
    # grid_auto_columns (defines the size of implicitly created columns)
    #   GridTrackVec<NonRepeatedTrackSizingFunction>
    #
    # GridTrackVec: A vector of grid tracks (defined in taffy::util::sys)

    # Grid child
    grid_row: GridPlacement = field(
        factory=GridPlacement, converter=GridPlacement.from_value
    )
    grid_column: GridPlacement = field(
        factory=GridPlacement, converter=GridPlacement.from_value
    )

    _ptr: int = field(init=False, default=None)

    def __attrs_post_init__(self):
        object.__setattr__(
            self,
            "_ptr",
            _bindings.taffy_style_create(
                # Layout mode
                self.display,
                # Position
                self.position,
                self.inset.to_taffy(),
                # Alignment
                self.align_items,
                self.justify_items,
                self.align_self,
                self.justify_self,
                self.align_content,
                self.justify_content,
                self.gap.to_taffy(),
                # Spacing
                self.margin.to_taffy(),
                self.border.to_taffy(),
                self.padding.to_taffy(),
                # Size
                self.size.to_taffy(),
                self.min_size.to_taffy(),
                self.max_size.to_taffy(),
                self.aspect_ratio,
                # Flex
                self.flex_wrap,
                self.flex_direction,
                self.flex_grow,
                self.flex_shrink,
                self.flex_basis.to_taffy(),
                # Grid container
                self.grid_auto_flow,
                # grid_template_rows
                # grid_template_columns
                # grid_auto_rows
                # grid_auto_columns
                # Grid child
                self.grid_row.to_taffy(),
                self.grid_column.to_taffy(),
            ),
        )
        logger.debug("taffy_style_create -> %s", self._ptr)

    def __del__(self):
        if self._ptr:
            _bindings.taffy_style_drop(self._ptr)
            logger.debug("taffy_style_drop(%s)", self._ptr)
