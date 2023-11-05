import logging
import re
from enum import StrEnum, auto
from typing import Callable, Iterable, Optional, Self, SupportsIndex
from xml.etree import ElementTree

from attrs import define

from stretchable import taffy, taffylib
from stretchable.style import Style
from stretchable.style.geometry.length import NAN, LengthAvailableSpace
from stretchable.style.geometry.size import SizeAvailableSpace, SizePoints
from stretchable.style.props import Display

logging.basicConfig(format="%(levelname)s:%(name)s:%(message)s")
logger = logging.getLogger(__name__)

_valid_id = re.compile(r"^[-_!:;()\]\[a-zA-Z0-9]*[a-zA-Z]+[-_!:;()\]\[a-zA-Z0-9]*$")
# _xml_parser = ElementTree.XMLParser()
# _xml_parser.parser.UseForeignDTD(True)
# _xml_parser.entity["&ZeroWidthSpace;"] = ""

"""
TODO:

 1) Consider renaming Tree to Root (?)
 2) Implement __str__ for classes (Node/Tree)
 3) Use __str__ from 1) in logger
 4) Add tests from Taffy
    4a) Implement measure_standard_text equivalent (from taffy tests/fixtures.rs) and implement this on nodes with inner-content
 5) Run/fix tests
 6) Support grid_[template/auto]_[rows/columns] in Style




"""

MeasureFunc = Callable[[SizePoints, SizeAvailableSpace], SizePoints]


class TaffyUnavailableError(Exception):
    ...


class NodeLocatorError(Exception):
    ...


class NodeNotFound(Exception):
    ...


class LayoutNotComputedError(Exception):
    ...


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


# TODO:
#   Add parent


class Node(list["Node"]):
    __slots__ = (
        "_id",
        "_style",
        "_children",
        "_measure",
        "_layout",
        "_zorder",
        "_parent",
        "__ptr",
    )

    def __init__(
        self,
        *children,
        id: str = None,
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

        # Node id requirements:
        #   May consist of -_!:;()[] a-z A-Z 0-9
        #   Must contain at least one alphabetical character
        if id is not None and not _valid_id.match(id):
            raise ValueError("The given `id` is not valid")
        self._id = id

        self._layout = None
        self._zorder = None
        self._parent = None
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
        return self if not self.parent else self.parent.root

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

    def __setitem__(self, __index: int, node: "Node") -> None:
        assert __index >= 0 and __index < len(self)
        if not taffy._ptr:
            raise TaffyUnavailableError

        self[__index].parent = None
        taffylib.node_replace_child_at_index(taffy._ptr, self._ptr, __index, node)
        node.parent = self
        super().__setitem__(__index, node)

    # endregion

    # region Id/locator

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
        if self.id:
            addr += self.id
        else:
            addr += str(self.parent.index(self))

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
        if _valid_id.match(pre):
            # If pre is valid node id, look in children ids
            for child in self:
                if child.id and child.id == pre:
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
            if index >= len(self.children):
                raise NodeNotFound("Node not found", addr)
            child = self[index]
            return child.find(post) if post else child

    @property
    def id(self) -> str:
        return self._id

    # endregion

    @property
    def style(self) -> Style:
        return self._style

    @property
    def is_dirty(self) -> bool:
        if not taffy._ptr:
            raise TaffyUnavailableError
        return taffylib.node_dirty(taffy._ptr, self._ptr)

    @property
    def is_visible(self) -> bool:
        if self.parent and not self.parent.is_visible:
            return False
        if self.style.display == Display.NONE:
            # logger.debug("(%s) Display.NONE => not visible", self._ptr)
            return False
        if self.is_dirty:
            raise LayoutNotComputedError(
                "Cannot determine if node is visible, layout is not computed"
            )
        if (self._layout.width <= 0 or self._layout.height <= 0) and len(self) == 0:
            # Box is zero-sized with no children
            # logger.debug(
            #     "(%s) zero-sized with no children, width %s, height %s => not visible",
            #     self._ptr,
            #     self._layout.width,
            #     self._layout.height,
            # )
            return False
        if (
            self._layout.y + self._layout.height < 0
            or self._layout.x + self._layout.width < 0
        ):
            # Box is outside
            # logger.debug(
            #     "(%s) box is outside visible area => not visible", self._ptr
            # )
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
        available_space: Optional[SizeAvailableSpace] = None,
        *,
        use_rounding: bool = True,
    ) -> bool:
        if not taffy._ptr:
            raise TaffyUnavailableError

        if not available_space:
            available_space = SizeAvailableSpace.default()

        taffy.use_rounding = use_rounding
        result = taffylib.node_compute_layout(
            taffy._ptr, self._ptr, available_space.to_dict()
        )
        if result:
            self._update_layout()

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

    def get_layout(
        self,
        box_type: Box = Box.BORDER,
        *,
        relative: bool = True,
        flip_y: bool = False,
    ) -> Layout:
        # https://developer.mozilla.org/en-US/docs/Learn/CSS/Building_blocks/The_box_model
        if self.is_dirty:
            raise LayoutNotComputedError

        # self._layout => BORDER box (outside of box border)

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
        if "id" in element.attrib:
            args["id"] = element.attrib["id"]
        if "style" in element.attrib:
            args["style"] = Style.from_inline(element.attrib["style"])
        node = cls(**args)
        if customize:
            node = customize(node, element)
        for child in element:
            node.add(Node._from_xml(child, customize))
        return node
