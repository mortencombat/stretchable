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


"""
    
"""


class Edge(StrEnum):
    """Describes which edge of a node a given :py:obj:`Box` corresponds to. See the :doc:`glossary` for a description of the box model and the different boxes."""

    CONTENT = auto()
    PADDING = auto()
    BORDER = auto()
    MARGIN = auto()


@define(frozen=True)
class Box:
    """Represents a rectangle with a position and size.

    Parameters
    ----------
    x : float
        The horizontal position of the left edge of the box
    y : float
        The vertical position of the top (default) or bottom (if using ``flip_y = True`` in :py:obj:`Node.get_box()`) edge of the box
    width : float
        The width of the box
    height : float
        The height of the box
    """

    x: float
    y: float
    width: float
    height: float

    def _offset(
        self,
        offsets: Rect,
        container: Box = None,
        *,
        factor: float = 1,
    ) -> Box:
        """
        Returns a copy of the frame offset by the specified ``offsets``.

        :param offsets: The offsets to use (typically margin, border or padding)
        :type offsets: Rect
        :param container: The container to use in case of percentage offsets, defaults to None
        :type container: Frame, optional
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

        return Box(
            self.x - factor * left,
            self.y - factor * top,
            self.width + factor * (left + right),
            self.height + factor * (top + bottom),
        )


class Node(list["Node"]):
    """A node in a layout.

    Parameters
    ----------
    *children
        Any child nodes to add to this node, optional
    key
        Node identifier that can be used to locate the node in the node tree, optional
    measure
        A method that is able to measure and return the size of the node
        during computation of layout, optional
    style
        The style to apply to the node, optional
    **kwargs
        If the ``style`` parameter is not provided, any additional keyword arguments are passed
        to a new instance of :py:obj:`Style` which is assigned to this node, optional

    """

    __slots__ = (
        "_key",
        "_style",
        "_children",
        "_measure",
        "_box",
        "_container",
        "_view",
        "_zorder",
        "_parent",
        "__ptr",
    )

    def __init__(
        self,
        *children: Node,
        key: str = None,
        measure: Callable[[SizePoints, SizeAvailableSpace], SizePoints] = None,
        style: Style = None,
        **kwargs,
    ):
        self.__ptr = None
        if not taffy._ptr:
            raise TaffyUnavailableError

        # Node key requirements:
        #   May consist of -_!:;()[] a-z A-Z 0-9
        #   Must contain at least one alphabetical character
        if key is not None and not _valid_key.match(key):
            raise ValueError("The given `key` is not valid")
        self._key = key

        self._box: dict[Edge, Box] = None
        self._zorder = None
        self._parent = None
        self._container: Node = None

        # Style
        if not style:
            style = Style(**kwargs)
        elif kwargs:
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

        if measure is None:
            self._measure = None
        else:
            self.measure = measure

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
    def parent(self) -> Node | None:
        """The parent :py:obj:`Node` of this node, or :py:obj:`None` if it does not have a parent node."""
        return self._parent

    @parent.setter
    def parent(self, value: Node) -> None:
        self._parent = value

    @property
    def root(self) -> Node:
        """The root :py:obj:`Node` of the node tree with which this node is associated."""
        return self if self.is_root else self.parent.root

    @property
    def is_root(self) -> bool:
        """``True`` if this node is the root node, ``False`` otherwise."""
        return self.parent is None

    def add(self, *children: Node) -> Node:
        """Add one or more child nodes and return the node itself (enables chaining of node instantiation, see :ref:`Building Node Trees`)."""
        self.extend(children)
        return self

    def append(self, node: Node):
        """Add a child node."""
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

    def extend(self, __iterable: Iterable[Node]) -> None:
        """Add one or more child nodes."""
        for child in __iterable:
            self.append(child)

    def remove(self, node: Node) -> None:
        """Remove child `Node`."""
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
        The address of this node, relative to the root node.
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

    def find(self, address: str) -> Node:
        """Returns the node at the specified address.

        Node addresses use a syntax similar to file paths, eg. a leading ``/``
        starts from the root of the node tree, ``./`` indicates the current
        location and ``../`` steps up a level.

        Nodes can be identified either by the :py:attr:`Node.key` (optional), or
        the 0-based node index.

        See :ref:`Locating Nodes` for some examples of how to locate nodes using
        this method.

        Parameters
        ----------
        address
            The address of the node to find
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
    def key(self) -> str | None:
        """Node identifier."""
        return self._key

    # endregion

    @property
    def style(self) -> Style:
        return self._style

    @property
    def is_dirty(self) -> bool:
        """``True`` if the layout needs to be (re)computed to get the layout of this node, ``False`` otherwise."""
        if not taffy._ptr:
            raise TaffyUnavailableError
        return taffylib.node_dirty(taffy._ptr, self._ptr)

    def mark_dirty(self):
        """Marks this node as `dirty` meaning that the layout needs to be recomputed."""
        if not taffy._ptr:
            raise TaffyUnavailableError
        taffylib.node_mark_dirty(taffy._ptr, self._ptr)

    @property
    def is_visible(self) -> bool:
        """Whether the node is visible."""

        if self.parent and not self.parent.is_visible:
            return False
        if self.style.display == Display.NONE:
            return False
        if self.is_dirty:
            raise LayoutNotComputedError(
                "Cannot determine if node is visible, layout is not computed"
            )
        if (
            (self._box[Edge.BORDER].width <= 0 or self._box[Edge.BORDER].height <= 0)
            and len(self) == 0
            and not self.is_root
        ):
            # Box is zero-sized with no children
            return False
        if (
            self._box[Edge.BORDER].y + self._box[Edge.BORDER].height < 0
            or self._box[Edge.BORDER].x + self._box[Edge.BORDER].width < 0
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
        logger.debug("node_measure_callback() -> %s", result)
        return (
            result.width.value if result.width else NAN,
            result.height.value if result.height else NAN,
        )

    @property
    def measure(self) -> MeasureFunc:
        """Method invoked to measure the node size during computation of layout."""
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
        """Computes the layout for this node and any child nodes.

        Parameters
        ----------
        available_space
            The available space for the layout. It may be provided as :py:obj:`SizeAvailableSpace`, as a :py:obj:`tuple` of width and height, or omitted
        use_rounding
            If ``True``, all positions and dimensions will be rounded to integers.

        Returns
        -------
        ``True`` if layout was computed successfully, ``False`` otherwise.

        Notes
        -----

        Depending on the nodes, the resulting layout may extend outside ``available_space``.
        """

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

        # Update the border box and clear cached boxes for other edges
        box = Box(layout["left"], layout["top"], layout["width"], layout["height"])
        self._box = {Edge.BORDER: box}
        self._zorder = layout["order"]

        logger.debug(
            "node_get_layout(taffy: %s, node: %s) -> (order: %s, left: %s, top: %s, width: %s, height: %s)",
            taffy._ptr,
            self._ptr,
            self._zorder,
            box.x,
            box.y,
            box.width,
            box.height,
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
    def border_box(self) -> Box:
        """The computed layout (position and size) of the nodes `border` box relative to the parent."""
        return self._box[Edge.BORDER]

    def get_box(
        self,
        edge: Edge = Edge.BORDER,
        *,
        relative: bool = True,
        flip_y: bool = False,
    ) -> Box:
        """
        Get the computed layout (position and size) for the node.

        See :term:`CSS box model` for more information.

        Parameters
        ----------
        edge
            The edge for which to get the corresponding :obj:`Box`
        relative
            Determines if returned position is relative to parent
            (if ``True``) or relative to the root (if ``False``)
        flip_y
            Determines if the vertical position (y) is measured from
            the top (if ``False``), or from the bottom (if ``True``)

        Returns
        -------
        The :obj:`Box` corresponding to the provided arguments
        """

        if (
            edge == Edge.MARGIN
            and self.has_auto_margin
            and (not self.is_root or not USE_ROOT_CONTAINER)
        ):
            raise ValueError(
                "Calculating the layout for Box.MARGIN is not currently supported with AUTO margins"
            )

        if self.is_dirty:
            raise LayoutNotComputedError

        box = self.border_box
        if edge == Edge.BORDER and relative and not flip_y:
            return box

        # h = hash((edge, relative, flip_y))

        if USE_ROOT_CONTAINER and self.is_root and edge == Edge.MARGIN:
            box = self._container.border_box
        elif edge != Edge.BORDER:
            # Expand or contract:
            #   Edge.CONTENT: -border -padding
            #   Edge.PADDING: -border
            #   Edge.BORDER: (none)
            #   Edge.MARGIN: +margin
            # Padding, border and margin are defined in Style.

            if edge in self._box:
                box = self._box[edge]
            else:
                if edge == Edge.CONTENT:
                    actions = (
                        (self.style.border, -1),
                        (self.style.padding, -1),
                    )
                elif edge == Edge.PADDING:
                    actions = ((self.style.border, -1),)
                elif edge == Edge.MARGIN:
                    actions = ((self.style.margin, 1),)

                box_parent = self._parent.get_box(Edge.BORDER) if self._parent else None
                for offsets, factor in actions:
                    box = box._offset(offsets, box_parent, factor=factor)

                self._box[edge] = box

        # TODO: Consider implementing a caching mechanism for relative and/or flip_y

        if not relative and self._parent:
            box_parent = self._parent.get_box(Edge.BORDER, relative=False)
            box = attrs.evolve(box, x=box.x + box_parent.x, y=box.y + box_parent.y)

        if flip_y:
            if relative:
                layout_ref = self.parent.get_box(Edge.CONTENT)
            elif USE_ROOT_CONTAINER:
                layout_ref = self.root._container.border_box
            else:
                layout_ref = self.root.border_box
            box = attrs.evolve(box, y=layout_ref.height - box.y - box.height)

        return box

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

    def __str__(self) -> str:
        try:
            addr = self.address
        except NodeLocatorError:
            addr = "<unknown>"

        children = len(self)
        children = f"<{children}>" if children else ""
        return f"Node('{addr}', children: [{children}], is_dirty: {self.is_dirty})"


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
            self._root.border_box.x
            + self._root.border_box.width
            + self._root.style.margin.right.to_pts(width)
            if width and self._root.style.margin.right.scale != Scale.AUTO
            else 0
        )
        if root_width > width:
            width = root_width
        root_height = (
            self._root.border_box.y
            + self._root.border_box.height
            + self._root.style.margin.bottom.to_pts(width)
            if width and self._root.style.margin.bottom.scale != Scale.AUTO
            else 0
        )
        if root_height > height:
            height = root_height
        self._layout = Box(x, y, width, height)
        logger.debug("container dimensions: %s x %s", root_width, root_height)

    @property
    def layout(self) -> Box:
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
