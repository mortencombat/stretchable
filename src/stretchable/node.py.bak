import math
from collections.abc import Iterable
from enum import StrEnum, auto
from typing import Callable, List, Self, SupportsIndex
from xml.etree import ElementTree

from attrs import define

from .stretch import _bindings
from .style import NAN, SCALING_FACTOR, Dimension, Display, Rect, Size, Style


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


class Box(StrEnum):
    CONTENT = auto()  # Innermost box, corresponding to inside of padding
    PADDING = auto()  # Outside of padding / inside of border
    BORDER = auto()  # Outside of border
    MARGIN = auto()  # Outside of margin


@define
class Layout:
    x: float
    y: float
    width: float
    height: float


class Children(list):
    def __init__(self, parent: "Node"):
        self._parent = parent

    def append(self, node: "Node"):
        _bindings.stretch_node_add_child(
            Stretch.get_ptr(), self._parent._ptr, node._ptr
        )
        node._parent = self._parent
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
            Stretch.get_ptr(), self._parent._ptr, __index, node._ptr
        )
        super().__setitem__(__index, node)


class Node:
    __slots__ = ("_style", "_children", "_measure", "_ptr", "_layout", "_parent")

    def __init__(
        self, *children, style: Style = None, measure: MeasureFunc = None, **kwargs
    ):
        self._ptr = None
        if not style:
            style = Style(**kwargs)
        elif kwargs:
            raise ValueError("Provide only `style` or style attributes, not both")
        self._style = style
        self._ptr = _bindings.stretch_node_create(Stretch.get_ptr(), self.style._ptr)
        self._children = Children(self)
        self.add(*children)
        self.measure = measure
        self._layout = None
        self._parent = None

    @staticmethod
    def from_xml(xml: str) -> Self:
        root = ElementTree.fromstring(xml)
        return Node._from_xml(root)

    @staticmethod
    def _from_xml(element: ElementTree.Element) -> Self:
        node = (
            Node(style=Style.from_html_style(element.attrib["style"]))
            if "style" in element.attrib
            else Node()
        )
        for child in element:
            node.add(Node._from_xml(child))
        return node

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
        _bindings.stretch_node_set_style(Stretch.get_ptr(), self._ptr, value._ptr)
        self._style = value

    @property
    def measure(self) -> MeasureFunc:
        return self._measure

    @property
    def visible(self) -> bool:
        if self._parent and not self._parent.visible:
            return False
        else:
            return self.style.display != Display.NONE

    @staticmethod
    def _measure_callback(node: Self, width: float, height: float) -> dict[str, float]:
        if not node:
            return dict(width=None, height=None)
        w, h = node.measure(
            None if math.isnan(width) else width / SCALING_FACTOR,
            None if math.isnan(height) else height / SCALING_FACTOR,
        )
        return dict(
            width=w * SCALING_FACTOR if w else None,
            height=h * SCALING_FACTOR if h else None,
        )

    @measure.setter
    def measure(self, value: MeasureFunc) -> None:
        if callable(value):
            self._measure = value
            _bindings.stretch_node_set_measure(
                Stretch.get_ptr(), self._ptr, self, Node._measure_callback
            )
        else:
            self._measure = None

    def dispose(self) -> None:
        """
        This method disposes of references to the node.
        Unless a measure function is defined, invoking this function is not necessary.

        But if a measure function is set, the issue is that the required function call
        (stretch_node_set_measure) includes a reference to the node instance itself.

        This means that the node is never garbage collected (__del__ is not invoked)
        and therefore 'stretch_node_free' is not invoked and the node is never deleted/
        removed from stretch.
        """

        _bindings.stretch_node_set_measure(
            Stretch.get_ptr(), self._ptr, None, Node._measure_callback
        )

    def __del__(self):
        if self._ptr:
            _bindings.stretch_node_free(Stretch.get_ptr(), self._ptr)

    @property
    def dirty(self) -> bool:
        return not self._layout or _bindings.stretch_node_dirty(
            Stretch.get_ptr(), self._ptr
        )

    def mark_dirty(self):
        self._layout = None
        _bindings.stretch_node_mark_dirty(Stretch.get_ptr(), self._ptr)

    @staticmethod
    def _scale_box(
        x: float,
        y: float,
        width: float,
        height: float,
        rect: Rect,
        container: Layout = None,
        *,
        factor: float = 1.0,
    ) -> tuple[float, float, float, float]:
        """
        Returns deltas from rect, converted to floats, using container dimensions in case of percentage values.
        Values returned correspond to: start, end, top, bottom (same as rect).

        A positive factor expands, negative factor contracts.
        """

        _w = container.width if container else None
        start = rect.start.to_float(_w)
        end = rect.end.to_float(_w)
        top = rect.top.to_float(_w)
        bottom = rect.bottom.to_float(_w)

        return (
            x - factor * start,
            y - factor * top,
            width + factor * (start + end),
            height + factor * (top + bottom),
        )

    @property
    def x(self) -> float:
        if self.dirty:
            raise LayoutNotComputedError
        return self._layout.x

    @property
    def y(self) -> float:
        if self.dirty:
            raise LayoutNotComputedError
        return self._layout.y

    @property
    def width(self) -> float:
        if self.dirty:
            raise LayoutNotComputedError
        return self._layout.width

    @property
    def height(self) -> float:
        if self.dirty:
            raise LayoutNotComputedError
        return self._layout.height

    def get_layout(
        self,
        box_type: Box = Box.BORDER,
        *,
        relative: bool = True,
        flip_y: bool = False,
    ) -> Layout:
        # https://developer.mozilla.org/en-US/docs/Learn/CSS/Building_blocks/The_box_model
        # TODO: Consider if this works property for RTL direction

        # self._box : BORDER box (outside of box border)

        if self.dirty:
            raise LayoutNotComputedError

        if box_type == Box.PADDING and relative and not flip_y:
            return self._layout

        x, y, w, h = (
            self._layout.x,
            self._layout.y,
            self._layout.width,
            self._layout.height,
        )

        # NOTE: Consider if/how box_parent can be reused in some scenarios and refactor

        if box_type != Box.BORDER:
            # Expand or contract:
            #   BoxType.CONTENT: -border -padding
            #   BoxType.PADDING: -border
            #   BoxType.BORDER: (none)
            #   BoxType.MARGIN: +margin
            # Padding, border and margin are defined in Style.
            # Points can be used directly. Percentages need to converted based on container dimension.
            # (which container dimension/box?)

            if box_type == Box.CONTENT:
                actions = (
                    (self.style.border, -1),
                    (self.style.padding, -1),
                )
            elif box_type == Box.PADDING:
                actions = ((self.style.border, -1),)
            elif box_type == Box.MARGIN:
                actions = ((self.style.margin, 1),)

            box_parent = self._parent.get_layout(Box.BORDER) if self._parent else None
            # print("BoxType:", box_type)
            for rect, factor in actions:
                # print(f"  {factor=} {rect}")
                # print(f"    {x=} {y=} {w=} {h=} ->")
                x, y, w, h = Node._scale_box(
                    x, y, w, h, rect, box_parent, factor=factor
                )
                # print(f"    -> {x=} {y=} {w=} {h=}")

        if not relative and self._parent:
            box_parent = self._parent.get_layout(Box.BORDER, relative=False)
            x += box_parent.x
            y += box_parent.y

        if flip_y:
            box_ref = (
                self._parent.get_layout(Box.CONTENT)
                if relative
                else self._root.get_layout(Box.MARGIN)
            )
            y = box_ref.height - y - h

        return Layout(x, y, w, h)

    def _set_layout(self, floats: List[float], offset: int = 0) -> int:
        next_offset = offset + 5
        x, y, width, height, child_count = floats[offset:next_offset]
        self._layout = Layout(
            x / SCALING_FACTOR,
            y / SCALING_FACTOR,
            width / SCALING_FACTOR,
            height / SCALING_FACTOR,
        )

        if child_count != len(self.children):
            raise Exception(
                f"Number of children in computed layout ({child_count}) does not match number of child nodes ({len(self.children)})"
            )
        for child in self.children:
            next_offset = child._set_layout(floats, next_offset)

        return next_offset

    @property
    def _root(self) -> Self:
        """Returns the root node."""
        return self._parent._root if self._parent else self

    def compute_layout(self, size: Size = None) -> Layout:
        """
        Computes the layout of the node and any child nodes.
        After invoking this, the position of nodes can be retrieved from the
        x, y, width and height properties on each node. These values define
        the border box relative to the parent node.
        (the border box includes padding and border, but not margins)

        To get the layout of other box types, position relative to the root node,
        or with y values measured from the bottom edge, use get_layout().
        """

        layout = _bindings.stretch_node_compute_layout(
            Stretch.get_ptr(),
            self._ptr,
            size.width.value * SCALING_FACTOR
            if size and size.width.unit == Dimension.POINTS
            else NAN,
            size.height.value * SCALING_FACTOR
            if size and size.height.unit == Dimension.POINTS
            else NAN,
        )
        self._set_layout(layout)
        return self.get_layout()

    # def __str__(self):
    #     return "(node: _ptr={}, measure={}, children={})".format(
    #         self._ptr, self._children, self._measure
    #     )
