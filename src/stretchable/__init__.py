# Module is inspired by/based on stretched (archived) by nmichlo:
# https://github.com/nmichlo/stretched

# Stretch is an implementation of CSS Flexbox written in Rust:
# https://github.com/vislyhq/stretch

# import bindings etc.
from .layout import Layout
from .node import Node, reset
from .stretch import _bindings
from .style import (
    AlignContent,
    AlignItems,
    AlignSelf,
    Dimension,
    DimensionValue,
    Direction,
    Display,
    FlexDirection,
    FlexWrap,
    JustifyContent,
    Overflow,
    PositionType,
    Rect,
    Size,
    Style,
    auto,
    pct,
    pt,
    undef,
)


class Stretch:
    _PRIVATE_PTR: int = None

    def __init__(self):
        raise Exception(
            "You should not be accessing or attempting to create an instance of this class."
        )

    @staticmethod
    def get_ptr():
        if Stretch._PRIVATE_PTR is None:
            Stretch._PRIVATE_PTR = _bindings.stretch_init()
        return Stretch._PRIVATE_PTR

    @staticmethod
    def reset():
        if not Stretch._PRIVATE_PTR is None:
            _bindings.stretch_free(Stretch._PRIVATE_PTR)
            Stretch._PRIVATE_PTR = None
