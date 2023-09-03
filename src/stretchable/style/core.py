import logging
from enum import IntEnum

from attrs import define, field, validators

from stretchable.taffy import _bindings

from .geometry.length import AUTO, LengthPointsPercentAuto
from .geometry.rect import RectPointsPercent, RectPointsPercentAuto
from .geometry.size import SizePointsPercent, SizePointsPercentAuto
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
        default=None, converter=RectPointsPercentAuto.from_any
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

    def _create(self) -> int:
        ptr = _bindings.style_create(
            # Layout mode
            self.display,
            # Position
            self.position,
            self.inset.to_dict(),
            # Alignment
            self.align_items,
            self.justify_items,
            self.align_self,
            self.justify_self,
            self.align_content,
            self.justify_content,
            self.gap.to_dict(),
            # Spacing
            self.margin.to_dict(),
            self.border.to_dict(),
            self.padding.to_dict(),
            # Size
            self.size.to_dict(),
            self.min_size.to_dict(),
            self.max_size.to_dict(),
            self.aspect_ratio,
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
        )
        logger.debug("style_create() -> %s", ptr)
        return ptr

    @staticmethod
    def _drop(self, ptr: int):
        _bindings.style_drop(ptr)
        logger.debug("style_drop(style: %s)", ptr)
