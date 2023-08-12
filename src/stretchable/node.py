import math
from collections.abc import Iterable
from enum import StrEnum, auto
from typing import Callable, List, Self, SupportsIndex, Tuple

from attrs import define

from .stretch import _bindings
from .style import NAN, Dimension, Size, Style


class LayoutNotComputedError(Exception):
    pass


MeasureFunc = Callable[[Size], Size]


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
        if Stretch._PRIVATE_PTR is not None:
            _bindings.stretch_free(Stretch._PRIVATE_PTR)
            Stretch._PRIVATE_PTR = None


def reset():
    Stretch.reset()


@define
class Layout:
    x: float
    y: float
    width: float
    height: float
    children: list[Self]

    @staticmethod
    def from_float_list(floats: List[float], offset: int = 0) -> Tuple[Self, int]:
        next_offset = offset + 5
        x, y, width, height, child_count = floats[offset:next_offset]

        children: List[Box] = []
        for _ in range(int(child_count)):
            (layout, next_offset) = Layout.from_float_list(floats, next_offset)
            children.append(layout)

        return (
            Layout(x, y, width, height, children),
            next_offset,
        )


class BoxType(StrEnum):
    CONTENT = auto()
    PADDING = auto()
    MARGIN = auto()
    BORDER = auto()


@define
class Box:
    x: float
    y: float
    width: float
    height: float

    @staticmethod
    def from_layout(layout: Layout) -> Self:
        return Box(layout.x, layout.y, layout.width, layout.height)


class Children(list):
    def __init__(self, parent: "Node"):
        self._parent = parent

    def append(self, node: "Node"):
        _bindings.stretch_node_add_child(
            Stretch.get_ptr(), self._parent._ptr, node._ptr
        )
        super().append(node)

    def extend(self, __iterable: Iterable["Node"]) -> None:
        for child in __iterable:
            self.append(child)

    def __delitem__(self, __index: SupportsIndex | slice) -> None:
        for index in (
            range(*__index.indices(len(self)))
            if isinstance(__index, slice)
            else [__index]
        ):
            _bindings.stretch_node_remove_child(
                Stretch.get_ptr(), self._parent._ptr, self[index]._ptr
            )
            super().__delitem__(index)

    def __setitem__(self, __index: int, node: "Node") -> None:
        assert __index >= 0 and __index < len(self)
        _bindings.stretch_node_replace_child_at_index(
            Stretch.get_ptr(), self._ptr, __index, node._ptr
        )
        super().__setitem__(__index, node)


class Node:
    __slots__ = ("_style", "_children", "_measure", "_ptr", "_box")

    def __init__(
        self, *children, style: Style = None, measure: MeasureFunc = None, **kwargs
    ):
        if not style:
            style = Style(**kwargs)
        elif kwargs:
            raise ValueError("Provide only `style` or style attributes, not both")
        self._style = style
        self._ptr = _bindings.stretch_node_create(Stretch.get_ptr(), self.style._ptr)
        self._children = Children(self)
        self.add(*children)
        self._measure = measure
        self._box = None

    def add(self, *children) -> Self:
        self._children.extend(children)
        return self

    @property
    def children(self) -> Children:
        return self._children

    @property
    def style(self) -> Style:
        return self._style

    @style.setter
    def style(self, value: Style) -> None:
        self._style = value
        # TODO: set node style

    @property
    def measure(self) -> MeasureFunc:
        return self._measure

    @measure.setter
    def measure(self, value: MeasureFunc) -> None:
        assert callable(value)
        _bindings.stretch_node_set_measure(
            Stretch.get_ptr(),
            self._ptr,
            self,
            lambda node, w, h: dict(**zip(("width", "height"), node.measure(w, h))),
        )

    def __del__(self):
        _bindings.stretch_node_free(Stretch.get_ptr(), self._ptr)

    @property
    def dirty(self) -> bool:
        return _bindings.stretch_node_dirty(Stretch.get_ptr(), self._ptr)

    def mark_dirty(self):
        _bindings.stretch_node_mark_dirty(Stretch.get_ptr(), self._ptr)

    def get_box(
        self, box_type: BoxType = BoxType.PADDING, relative: bool = True
    ) -> Box:
        # https://developer.mozilla.org/en-US/docs/Learn/CSS/Building_blocks/The_box_model
        # TODO: consider also support left-bottom origo (as opposed to the default of left-top origo)
        if self.dirty:
            raise LayoutNotComputedError
        if box_type != BoxType.PADDING or not relative:
            raise NotImplementedError
        return self._box

    def _set_layout(self, layout: Layout):
        self._box = Box.from_layout(layout)
        for n, l in zip(self.children, layout.children):
            n._set_layout(l)

    def compute_layout(self, size: Size = None):
        """
        Computes the layout of the node and any child nodes.
        After invoking this, the position of nodes can be retrieved from the
        x, y, width and height properties on each node.
        NOTE:
            x and y are relative to the parent node
            x, y, width and height define the node frame box (includes margins but not padding)
            To get the outer box, expand the frame box by the set amount of margin.
            To get the inner/content box, contract the frame box by the set amount of padding.
        TODO:
            Consider including arg (relative_position: bool) and integrating functionality to get the
            outer and inner box
        """

        float_layout = _bindings.stretch_node_compute_layout(
            Stretch.get_ptr(),
            self._ptr,
            size.width.value if size and size.width.unit == Dimension.POINTS else NAN,
            size.height.value if size and size.height.unit == Dimension.POINTS else NAN,
        )
        layout, _ = Layout.from_float_list(float_layout)
        self._set_layout(layout)

    def __str__(self):
        return "(node: _ptr={}, measure={}, children={})".format(
            self._ptr, self._children, self._measure
        )
