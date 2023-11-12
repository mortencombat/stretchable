from __future__ import annotations

import logging
import re
from enum import StrEnum, auto
from typing import Callable, Iterable, Optional, Self, SupportsIndex
from xml.etree import ElementTree

import attrs
from attrs import define

from . import taffylib
from .context import taffy
from .exceptions import (
    LayoutNotComputedError,
    NodeLocatorError,
    NodeNotFound,
    TaffyUnavailableError,
)
from .style import Display, Rect, Style
from .style.geometry.length import AUTO, NAN, LengthAvailableSpace, Scale
from .style.geometry.size import SizeAvailableSpace, SizePoints, SizePointsPercentAuto

logging.basicConfig(format="%(levelname)s:%(name)s:%(message)s")
logger = logging.getLogger(__name__)

_valid_key = re.compile(r"^[-_!:;()\]\[a-zA-Z0-9]*[a-zA-Z]+[-_!:;()\]\[a-zA-Z0-9]*$")


MeasureFunc = Callable[[SizePoints, SizeAvailableSpace], SizePoints]

USE_ROOT_CONTAINER: bool = False


class Box(StrEnum):
    CONTENT = auto()  # Innermost box, corresponding to inside of padding
    PADDING = auto()  # Outside of padding / inside of border
    BORDER = auto()  # Outside of border
    MARGIN = auto()  # Outside of margin


@define(frozen=True)
class Layout:
    x: float
    y: float
    width: float
    height: float

    def scale(
        self,
        offsets: Rect,
        container: Layout = None,
        *,
        factor: float = 1,
    ) -> Layout:
        """
        Adjusts layout by the provided offsets.

        :param offsets: The offsets to use (typically margin, border or padding)
        :type offsets: Rect
        :param container: The container to use in case of percentage offsets, defaults to None
        :type container: Layout, optional
        :param factor: The factor to apply to offsets (positive value expands, negative value contracts), defaults to 1
        :type factor: float
        :return: Adjusted layout
        :rtype: Layout
        """

        container = container.width if container else None
        left = offsets.left.to_pts(container)
        right = offsets.right.to_pts(container)
        top = offsets.top.to_pts(container)
        bottom = offsets.bottom.to_pts(container)

        return Layout(
            self.x - factor * left,
            self.y - factor * top,
            self.width + factor * (left + right),
            self.height + factor * (top + bottom),
        )


class Node(list["Node"]):
    __slots__ = (
        "_key",
        "_style",
        "_children",
        "_measure",
        "_layout",
        "_container",
        "_view",
        "_zorder",
        "_parent",
        "__ptr",
    )

    def __init__(
        self,
        *children,
        key: str = None,
        measure: MeasureFunc = None,
        style: Style = None,
        **style_args,
    ):
        """
        ...

        Arguments:
            measure:    a callable that takes (available_space: Size[AvailableSpace], known_dimensions: Size[float]) and returns Size[float]
        """

        self.__ptr = None
        if not taffy._ptr:
            raise TaffyUnavailableError

        # Node key requirements:
        #   May consist of -_!:;()[] a-z A-Z 0-9
        #   Must contain at least one alphabetical character
        if key is not None and not _valid_key.match(key):
            raise ValueError("The given `key` is not valid")
        self._key = key

        self._layout = None
        self._zorder = None
        self._parent = None
        self._container: Node = None
        self._measure = measure

        # Style
        if not style:
            style = Style(**style_args)
        elif style_args:
            raise ValueError("Provide only `style` or style attributes, not both")
        self._style = style

        # Create node in taffy
        self.__ptr = taffylib.node_create(taffy._ptr, style._ptr)
        # taffy._nodes.add(self.__ptr)
        logger.debug(
            "node_create(taffy: %s, style: %s) -> %s",
            taffy._ptr,
            style._ptr,
            self.__ptr,
        )

        # Children
        self._children = []
        self.add(*children)

    @property
    def _ptr(self) -> int:
        return self.__ptr

    def __del__(self) -> None:
        if self._ptr is None or not taffy._ptr:
            return
        taffylib.node_drop(taffy._ptr, self._ptr)
        # taffy._nodes.remove(self._ptr)
        logger.debug("node_drop(taffy: %s, node: %s)", taffy._ptr, self._ptr)

    def __hash__(self) -> int:
        return id(self)

    # region Children

    @property
    def parent(self) -> "Node":
        return self._parent

    @parent.setter
    def parent(self, value: "Node") -> None:
        self._parent = value

    @property
    def root(self) -> "Node":
        return self if self.is_root else self.parent.root

    @property
    def is_root(self) -> bool:
        return self.parent is None

    def add(self, *children) -> Self:
        self.extend(children)
        return self

    def append(self, node: "Node"):
        if not taffy._ptr:
            raise TaffyUnavailableError
        if not isinstance(node, Node):
            raise TypeError("Only nodes can be added")
        elif node.parent:
            raise Exception("Node is already associated with a parent node")
        taffylib.node_add_child(taffy._ptr, self._ptr, node._ptr)
        logger.debug(
            "node_add_child(taffy: %s, parent: %s, child: %s)",
            taffy._ptr,
            self._ptr,
            node._ptr,
        )
        node.parent = self
        super().append(node)

    def extend(self, __iterable: Iterable["Node"]) -> None:
        for child in __iterable:
            self.append(child)

    def remove(self, node: "Node") -> None:
        if not taffy._ptr:
            raise TaffyUnavailableError
        taffylib.node_remove_child(taffy._ptr, self._ptr, node._ptr)
        logger.debug(
            "node_remove_child(taffy: %s, parent: %s, child: %s)",
            taffy._ptr,
            self._ptr,
            node._ptr,
        )
        node.parent = None
        return super().remove(node)

    def __delitem__(self, __index: SupportsIndex | slice) -> None:
        if not taffy._ptr:
            raise TaffyUnavailableError
        for index in reversed(
            range(*__index.indices(len(self)))
            if isinstance(__index, slice)
            else [__index]
        ):
            taffylib.node_remove_child_at_index(taffy._ptr, self._ptr, index)
            logger.debug(
                "node_remove_child_at_index(taffy: %s, parent: %s, index: %s)",
                taffy._ptr,
                self._ptr,
                index,
            )
            self[index].parent = None
            super().__delitem__(index)

    def __setitem__(
        self, __index: SupportsIndex | slice, value: "Node" | Iterable["Node"]
    ) -> None:
        if not taffy._ptr:
            raise TaffyUnavailableError

        if isinstance(__index, slice):
            items = zip(range(*__index.indices(len(self))), value)
        else:
            items = [(__index, value)]

        for index, node in items:
            self[index].parent = None
            taffylib.node_replace_child_at_index(
                taffy._ptr, self._ptr, index, node._ptr
            )
            node.parent = self
            super().__setitem__(index, node)

    # endregion

    # region Key/locator

    @property
    def address(self) -> str:
        """
        The address of this node, relative to farthest parent node
        or root if associated with a tree.
        """
        if not self.parent:
            return "/"

        addr = self.parent.address
        if addr is None:
            addr = ""
        if addr and not addr.endswith("/"):
            addr += "/"
        if self.key:
            addr += self.key
        else:
            index = None
            for i, child in enumerate(self.parent):
                if child is not self:
                    continue
                index = i
            if index is None:
                raise NodeLocatorError(
                    "Node is not registered as a child of the parent node"
                )
            addr += str(index)

        return addr

    def find(self, address: str) -> Self:
        """
        Returns the node at the specified address.

        Nodes can be identified either by the node id (str) if it is defined,
        or the 0-based node index.

        Example tree:
            tree
            - 'header'
            - 'body'
              - 'left'
              - 'center'
                - 'title'
                - 'content'
              - 'right'
            - 'footer'

        Absolute address examples (start with a leading /, nodes must be
        associated with a tree, which is the root):
            /body/center/title -> 'title' node
            /1/1/0 -> 'title' node
            /2 -> 'footer' node

        Relative address examples, using find() on the 'body' node:
            center/title -> 'title' node
            ./center/title -> 'title' node
            1/1 -> 'content' node
            ../footer -> 'footer' node


        """

        addr = address.strip()
        if addr.startswith("./"):
            addr = addr[2:]
        if addr.startswith("../"):
            if not self.parent:
                raise NodeLocatorError(
                    "Node has no parent, cannot locate address", addr
                )
            return self.parent.find(addr[3:])
        if addr.startswith("/"):
            return self.root.find(addr[1:])
        if not addr:
            return self
        if len(self) == 0:
            raise NodeNotFound("Node not found", addr)

        pre, sep, post = addr.partition("/")
        if _valid_key.match(pre):
            # If pre is valid node id, look in children ids
            for child in self:
                if child.key and child.key == pre:
                    return child.find(post) if post else child
            raise NodeNotFound("Node not found", addr)
        else:
            # If pre is valid integer, look at children index
            try:
                index = int(pre)
            except ValueError:
                index = -1
            if index < 0:
                raise NodeLocatorError("Address is not valid", addr)
            if index >= len(self):
                raise NodeNotFound("Node not found", addr)
            child = self[index]
            return child.find(post) if post else child

    @property
    def key(self) -> str:
        return self._key

    # endregion

    @property
    def style(self) -> Style:
        return self._style

    @property
    def is_dirty(self) -> bool:
        if not taffy._ptr:
            raise TaffyUnavailableError
        return taffylib.node_dirty(taffy._ptr, self._ptr)

    def mark_dirty(self) -> None:
        if not taffy._ptr:
            raise TaffyUnavailableError
        taffylib.node_mark_dirty(taffy._ptr, self._ptr)

    @property
    def is_visible(self) -> bool:
        if self.parent and not self.parent.is_visible:
            return False
        if self.style.display == Display.NONE:
            return False
        if self.is_dirty:
            raise LayoutNotComputedError(
                "Cannot determine if node is visible, layout is not computed"
            )
        if (
            (self._layout.width <= 0 or self._layout.height <= 0)
            and len(self) == 0
            and not self.is_root
        ):
            # Box is zero-sized with no children
            return False
        if (
            self._layout.y + self._layout.height < 0
            or self._layout.x + self._layout.width < 0
        ):
            # Box is outside canvas
            return False

        return True

    # region Measuring and layout

    @staticmethod
    def _measure_callback(
        node: Self,
        known_width: float,
        known_height: float,
        available_width: dict[int, float],
        available_height: dict[int, float],
    ) -> tuple[float, float]:
        """This function is a wrapper for the user-supplied measure function,
        converting arguments into and results from the call by Taffy."""
        known_dimensions = SizePoints(width=known_width, height=known_height)
        available_space = SizeAvailableSpace(
            LengthAvailableSpace.from_dict(available_width),
            LengthAvailableSpace.from_dict(available_height),
        )
        result = node.measure(known_dimensions, available_space)
        assert isinstance(result, SizePoints)
        print(result)
        return (
            result.width.value if result.width else NAN,
            result.height.value if result.height else NAN,
        )

    @property
    def measure(self) -> MeasureFunc:
        return self._measure

    @measure.setter
    def measure(self, value: MeasureFunc) -> None:
        assert value is None or callable(value)
        self._measure = value
        if not taffy._ptr:
            raise TaffyUnavailableError
        if value is None:
            taffylib.node_remove_measure(taffy._ptr, self._ptr)
            logger.debug(
                "node_remove_measure(taffy: %s, node: %s)", taffy._ptr, self._ptr
            )
        else:
            taffylib.node_set_measure(
                taffy._ptr, self._ptr, self, Node._measure_callback
            )
            logger.debug("node_set_measure(taffy: %s, node: %s)", taffy._ptr, self._ptr)

    def compute_layout(
        self,
        available_space: Optional[SizeAvailableSpace | tuple[float, float]] = None,
        *,
        use_rounding: bool = False,
    ) -> bool:
        if not taffy._ptr:
            raise TaffyUnavailableError

        if not available_space:
            available_space = SizeAvailableSpace.default()
        elif not isinstance(available_space, SizeAvailableSpace):
            available_space = SizeAvailableSpace(*available_space)

        if USE_ROOT_CONTAINER and self.is_root:
            # If this is a root node, use a container node to be able to get the
            # position (x, y) of the root node relative to the 'canvas' (as
            # specified using available_space parameter).
            if self._container:
                self._container.size = available_space
            else:
                self._container = Container(self, available_space)
            ptr = self._container._ptr
        else:
            ptr = self._ptr

        taffy.use_rounding = use_rounding
        result = taffylib.node_compute_layout(
            taffy._ptr, ptr, available_space.to_dict()
        )
        if not result:
            return False

        # Update layout of this node, child nodes and container, if applicable
        self._update_layout()
        if USE_ROOT_CONTAINER and self.is_root:
            self._container._update_layout()

        return result

    def _update_layout(self) -> None:
        if self.is_dirty:
            raise LayoutNotComputedError

        layout = taffylib.node_get_layout(taffy._ptr, self._ptr)
        self._layout = Layout(
            layout["left"], layout["top"], layout["width"], layout["height"]
        )
        self._zorder = layout["order"]
        logger.debug(
            "node_get_layout(taffy: %s, node: %s) -> (order: %s, left: %s, top: %s, width: %s, height: %s)",
            taffy._ptr,
            self._ptr,
            self._zorder,
            self._layout.x,
            self._layout.y,
            self._layout.width,
            self._layout.height,
        )

        if self.is_visible:
            for child in self:
                child._update_layout()

    @property
    def has_auto_margin(self) -> bool:
        if not self.style.margin:
            return False
        return (
            self.style.margin.top.scale == Scale.AUTO
            or self.style.margin.right.scale == Scale.AUTO
            or self.style.margin.bottom.scale == Scale.AUTO
            or self.style.margin.left.scale == Scale.AUTO
        )

    @property
    def layout(self) -> Layout:
        """The computed layout (position and size) of the nodes `border` box relative to the parent."""
        return self._layout

    def get_layout(
        self,
        box: Box = Box.BORDER,
        *,
        relative: bool = True,
        flip_y: bool = False,
    ) -> Layout:
        """
        Get the computed layout (position and size) for the node.

        For a description of the box model, see:
        https://developer.mozilla.org/en-US/docs/Learn/CSS/Building_blocks/The_box_model

        :param box: The box/edge, defaults to Box.BORDER
        :type box: Box, optional
        :param relative: Determines if returned position is relative to parent
            (True, the default) or relative to the root (False)
        :type relative: bool, optional
        :param flip_y: Determines if the vertical position (y) is measured from
            the top (False, the default), or from the bottom (True)
        :type flip_y: bool, optional
        :raises ValueError: If box = Box.MARGIN is requested with AUTO margins,
            since this is currently not supported
        :raises LayoutNotComputedError: If the layout is not computed before
            requesting the layout
        :return: The computed layout
        :rtype: Layout
        """

        if (
            box == Box.MARGIN
            and self.has_auto_margin
            and (not self.is_root or not USE_ROOT_CONTAINER)
        ):
            raise ValueError(
                "Calculating the layout for Box.MARGIN is not currently supported with AUTO margins"
            )

        if self.is_dirty:
            raise LayoutNotComputedError

        layout = self.layout
        if box == Box.BORDER and relative and not flip_y:
            return layout

        # NOTE: Consider if/how box_parent can be reused in some scenarios and refactor
        # Generally consider caching of layouts
        # Remember to reset cache on compute_layout

        if USE_ROOT_CONTAINER and self.is_root and box == Box.MARGIN:
            layout = self._container.layout
        elif box != Box.BORDER:
            # Expand or contract:
            #   Box.CONTENT: -border -padding
            #   Box.PADDING: -border
            #   Box.BORDER: (none)
            #   Box.MARGIN: +margin
            # Padding, border and margin are defined in Style.

            if box == Box.CONTENT:
                actions = (
                    (self.style.border, -1),
                    (self.style.padding, -1),
                )
            elif box == Box.PADDING:
                actions = ((self.style.border, -1),)
            elif box == Box.MARGIN:
                actions = ((self.style.margin, 1),)

            box_parent = self._parent.get_layout(Box.BORDER) if self._parent else None
            for offsets, factor in actions:
                layout = layout.scale(offsets, box_parent, factor=factor)

        if not relative and self._parent:
            box_parent = self._parent.get_layout(Box.BORDER, relative=False)
            layout = attrs.evolve(
                layout, x=layout.x + box_parent.x, y=layout.y + box_parent.y
            )

        if flip_y:
            if relative:
                layout_ref = self.parent.get_layout(Box.CONTENT)
            elif USE_ROOT_CONTAINER:
                layout_ref = self.root._container.layout
            else:
                layout_ref = self.root.layout
            layout = attrs.evolve(
                layout, y=layout_ref.height - layout.y - layout.height
            )

        return layout

    # endregion

    @classmethod
    def from_xml(
        cls, xml: str, customize: Callable[[Self, ElementTree.Element], Self] = None
    ) -> Self:
        root = ElementTree.fromstring(xml)  # , parser=_xml_parser)
        return cls._from_xml(root, customize)

    @classmethod
    def _from_xml(
        cls,
        element: ElementTree.Element,
        customize: Callable[[Self, ElementTree.Element], Self] = None,
    ) -> Self:
        args = dict()
        if "key" in element.attrib:
            args["key"] = element.attrib["key"]
        if "style" in element.attrib:
            args["style"] = Style.from_inline(element.attrib["style"])
        node = cls(**args)
        if customize:
            node = customize(node, element)
        for child in element:
            node.add(Node._from_xml(child, customize))
        return node


class Container:
    __slots__ = ("_size", "__ptr", "_style", "_root", "_layout")

    def __init__(self, root: Node, size: Optional[SizeAvailableSpace] = None):
        self.__ptr = None
        if not taffy._ptr:
            raise TaffyUnavailableError

        self._layout = None
        self._size = None
        self.size = size
        self._root = root

        # Create node in taffy
        self.__ptr = taffylib.node_create(taffy._ptr, self._style._ptr)
        logger.debug(
            "node_create(taffy: %s, style: %s) -> %s",
            taffy._ptr,
            self._style._ptr,
            self.__ptr,
        )
        # Add root node as child of this node
        taffylib.node_add_child(taffy._ptr, self._ptr, root._ptr)

    def _update_layout(self) -> None:
        # NOTE: Since this container node has no margins, border and padding, this layout corresponds to all the boxes.

        layout = taffylib.node_get_layout(taffy._ptr, self._ptr)
        x = layout["left"]
        y = layout["top"]
        width = layout["width"]
        height = layout["height"]
        logger.debug(
            "node_get_layout(taffy: %s, node: %s [container]) -> (left: %s, top: %s, width: %s, height: %s)",
            taffy._ptr,
            self._ptr,
            x,
            y,
            width,
            height,
        )

        # Expand box to contain the root node
        root_width = (
            self._root.layout.x
            + self._root.layout.width
            + self._root.style.margin.right.to_pts(width)
            if width and self._root.style.margin.right.scale != Scale.AUTO
            else 0
        )
        if root_width > width:
            width = root_width
        root_height = (
            self._root.layout.y
            + self._root.layout.height
            + self._root.style.margin.bottom.to_pts(width)
            if width and self._root.style.margin.bottom.scale != Scale.AUTO
            else 0
        )
        if root_height > height:
            height = root_height
        self._layout = Layout(x, y, width, height)
        logger.debug("container dimensions: %s x %s", root_width, root_height)

    @property
    def layout(self) -> Layout:
        return self._layout

    @property
    def _ptr(self) -> int:
        return self.__ptr

    @property
    def size(self) -> SizeAvailableSpace:
        return self._size

    @size.setter
    def size(self, value: SizeAvailableSpace) -> None:
        if value == self._size:
            return
        if self._ptr and not taffy._ptr:
            raise TaffyUnavailableError
        self._size = value
        self._style = Style(
            size=SizePointsPercentAuto(
                width=value.width if value.width.scale == Scale.POINTS else AUTO,
                height=value.height if value.height.scale == Scale.POINTS else AUTO,
            )
        )
        if self._ptr:
            taffylib.node_set_style(taffy._ptr, self._ptr, self._style._ptr)
