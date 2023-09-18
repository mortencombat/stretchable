import logging
import re
from enum import StrEnum, auto
from typing import Callable, Iterable, Self, SupportsIndex
from xml.etree import ElementTree

from attrs import define

from stretchable.style import Style
from stretchable.style.geometry.length import NAN, LengthAvailableSpace
from stretchable.style.geometry.size import SizeAvailableSpace, SizePoints
from stretchable.style.props import Display

from .taffy import _bindings

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

NOTE:

Instead of specific Tree, just have Node.
The root Node would know it is a Root, and when needed, could create an instance
of Taffy. However, if nodes are removed, replaced, etc. this would be really
hard to track, creating new Taffy instances, etc.

One approach would be to have node.compute_layout(taffy) or taffy.compute_layout(root_node) (this mirrors Taffy itself)

You could also

A disadvantage would be that you have to supply a Taffy instance when instancing nodes, eg. Node(taffy, ...)


The "stretched" approach with a shared Taffy instance is not considered very robust.





"""

MeasureFunc = Callable[[SizePoints, SizeAvailableSpace], SizePoints]


class NodeLocatorError(Exception):
    pass


class NodeNotFound(Exception):
    pass


class LayoutNotComputedError(Exception):
    pass


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
        if not isinstance(node, Node):
            raise TypeError("Only nodes can be added")
        elif node.parent:
            raise Exception("Node is already associated with a parent node")
        node.parent = self._parent
        super().append(node)

    def extend(self, __iterable: Iterable["Node"]) -> None:
        for child in __iterable:
            self.append(child)

    def remove(self, node: "Node") -> None:
        if self._parent.tree:
            self._parent.tree._node_remove_child(self._parent, node)
        return super().remove(node)

    def __delitem__(self, __index: SupportsIndex | slice) -> None:
        for index in reversed(
            range(*__index.indices(len(self)))
            if isinstance(__index, slice)
            else [__index]
        ):
            if self._parent.tree:
                self._parent.tree._node_remove_child(self._parent, self[index])
            super().__delitem__(index)

    def __setitem__(self, __index: int, node: "Node") -> None:
        assert __index >= 0 and __index < len(self)
        if self._parent.tree:
            self._parent.tree._node_replace_child_at_index(self._parent, __index, node)
        super().__setitem__(__index, node)


"""

measure_func

"""


class Node:
    __slots__ = (
        "_id",
        "_style",
        "_children",
        "_measure",
        "_ptr",
        "_ptr_style",
        "_layout",
        "_zorder",
        "_parent",
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

        self._ptr = None
        self._layout = None
        self._zorder = None
        self._parent = None
        self._measure = measure

        # Node id requirements:
        #   May consist of -_!:;()[] a-z A-Z 0-9
        #   Must contain at least one alphabetical character
        if id is not None and not _valid_id.match(id):
            raise ValueError("The given `id` is not valid")
        self._id = id

        # Style
        if not style:
            style = Style(**style_args)
        elif style_args:
            raise ValueError("Provide only `style` or style attributes, not both")
        self._style = style
        self._ptr_style = None

        # Children
        self._children = Children(self)
        self.add(*children)

        if self.is_tree:
            self._add_to_tree()

    def add(self, *children) -> Self:
        self._children.extend(children)
        return self

    @property
    def address(self) -> str:
        """
        The address of this node, relative to farthest parent node
        or root if associated with a tree.
        """
        if self.is_tree:
            return "/"
        elif not self.parent:
            return None

        addr = self.parent.address
        if addr is None:
            addr = ""
        if addr and not addr.endswith("/"):
            addr += "/"
        if self.id:
            addr += self.id
        else:
            addr += str(self.parent.children.index(self))

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
            if self.is_tree:
                raise NodeLocatorError("Node is tree, cannot go to parent", addr)
            if not self.parent:
                raise NodeLocatorError(
                    "Node has no parent, cannot locate address", addr
                )
            return self.parent.find(addr[3:])
        if addr.startswith("/"):
            if not self.tree:
                raise NodeLocatorError(
                    "Node is not associated with a tree, cannot locate address", addr
                )
            return self.tree.find(addr[1:])
        if not addr:
            return self
        if len(self.children) == 0:
            raise NodeNotFound("Node not found", addr)

        pre, sep, post = addr.partition("/")
        if _valid_id.match(pre):
            # If pre is valid node id, look in children ids
            for child in self.children:
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
            child = self.children[index]
            return child.find(post) if post else child

    @property
    def style(self) -> Style:
        return self._style

    @property
    def children(self) -> Children:
        return self._children

    @property
    def parent(self) -> Self:
        return self._parent

    @property
    def id(self) -> str:
        return self._id

    @property
    def is_dirty(self) -> bool:
        if self.tree:
            return self.tree._node_dirty(self)

    @parent.setter
    def parent(self, value: Self) -> None:
        if value is None and self._ptr and self.tree and not self.is_tree:
            # Node is currently added to tree, but is being removed
            # Drop it from the tree
            self._drop()
            self._parent = None
            return

        if value and self.id:
            # Check that there are no id collisions with other children of parent
            for child in value.children:
                if child.id and child.id == self.id:
                    raise Exception(
                        "There is another child node with the same `id` on this parent node",
                        self.id,
                    )

        set_tree = self.tree is None and value is not None and value.tree is not None
        self._parent = value
        if set_tree:
            self._add_to_tree()

    def _add_to_tree(self) -> None:
        if self.tree and not self._ptr:
            # Create node
            self._create()

            # Add as child node
            if self.parent and self.tree:
                self.tree._node_add_child(self.parent, self)
        for child in self.children:
            child._add_to_tree()

    def _create(self, tree: "Tree" = None):
        if self._ptr:
            # Node is already created, tree cannot change
            raise Exception(
                "Node is already associated with a tree, cannot add it to another tree"
            )
        _tree = tree if tree else self.tree
        if not _tree:
            raise Exception("Cannot create node without a tree")

        _tree._node_create(self)
        if self.measure:
            _tree._node_set_measure(self)

    def _drop(self, tree: "Tree" = None):
        # Ensure that any child nodes are also dropped
        for child in self.children:
            child._drop(tree)

        # Ensure that node can be dropped
        if not self._ptr:
            raise Exception("Node is not associated with a tree, cannot drop it")
        _tree = tree if tree else self.tree
        if not _tree:
            raise Exception("Cannot drop node without a tree")

        # Drop node
        _tree._node_drop(self)

    @property
    def tree(self) -> "Tree":
        """Returns the associated Tree class instance, if this node has been added to the corresponding tree"""
        return self.parent.tree if self.parent else None

    @property
    def is_tree(self) -> bool:
        return False

    @property
    def is_visible(self) -> bool:
        if self._parent and not self._parent.is_visible:
            return False
        else:
            if self.style.display == Display.NONE:
                # logger.debug("(%s) Display.NONE => not visible", self._ptr)
                return False
            if self.is_dirty:
                raise LayoutNotComputedError(
                    "Cannot determine if node is visible, layout is not computed"
                )
            if (
                (self._layout.width <= 0 or self._layout.height <= 0)
                and not self.children
                and not self.is_tree
            ):
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
        if self.tree and self._ptr:
            if value is None:
                self.tree._node_remove_measure(self)
            else:
                self.tree._node_set_measure(self)

    def __del__(self) -> None:
        if self.tree and self.tree._ptr_tree and self._ptr:
            self.tree._node_drop(self)
            # _bindings.node_drop(self.tree._ptr_tree, self._ptr)
            # logger.debug("node_drop(%s)", self._ptr)
            # self._ptr = None

    def compute_layout(self, available_space: SizeAvailableSpace = None):
        if not self.tree:
            raise Exception("Node must be added to a tree before computing layout")
        self.tree._node_compute_layout(self, available_space)

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


class Tree(Node):
    __slots__ = ("_ptr_tree", "_rounding_enabled")

    def __init__(self, *args, **kwargs) -> None:
        self._rounding_enabled = True
        self._ptr_tree = _bindings.init()
        logger.debug("init() -> %s", self._ptr_tree)
        super().__init__(*args, **kwargs)

    def __del__(self) -> None:
        if hasattr(self, "_ptr_taffy") and self._ptr_tree:
            _bindings.free(self._ptr_tree)
            logger.debug("free(tree: %s) via __del__", self._ptr_tree)
            self._ptr_tree = None

    @property
    def rounding_enabled(self) -> bool:
        return self._rounding_enabled

    @rounding_enabled.setter
    def rounding_enabled(self, value: bool) -> None:
        if value == self._rounding_enabled:
            return
        if value:
            self._enable_rounding()
        else:
            self._disable_rounding()
        self._rounding_enabled = value

    @property
    def tree(self) -> Self:
        return self

    @property
    def is_tree(self) -> bool:
        return True

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> Self:
        if hasattr(self, "_ptr_tree") and self._ptr_tree:
            _bindings.free(self._ptr_tree)
            logger.debug("free(tree: %s) via __exit__", self._ptr_tree)
            self._ptr_tree = None

    # Bindings

    def _enable_rounding(self) -> None:
        _bindings.enable_rounding(self._ptr_tree)
        logger.debug("enable_rounding(tree: %s)", self._ptr_tree)

    def _disable_rounding(self) -> None:
        _bindings.disable_rounding(self._ptr_tree)
        logger.debug("disable_rounding(tree: %s)", self._ptr_tree)

    def _node_add_child(self, parent: Node, child: Node) -> None:
        _bindings.node_add_child(self._ptr_tree, parent._ptr, child._ptr)
        logger.debug(
            "node_add_child(tree: %s, parent: %s, child: %s)",
            self._ptr_tree,
            parent._ptr,
            child._ptr,
        )

    def _node_remove_child(self, parent: Node, child: Node):
        _bindings.node_remove_child(self._ptr_tree, parent._ptr, child._ptr)
        logger.debug(
            "node_remove_child(tree: %s, parent: %s, child: %s)",
            self._ptr_tree,
            parent._ptr,
            child._ptr,
        )

        # Set parent of removed child to None, which will cause it to be dropped from the tree
        child.parent = None

    def _node_replace_child_at_index(
        self, parent: Node, index: int, child: Node
    ) -> None:
        # Get current child at index
        replaced = parent.children[index]

        # Create new child and replace it at index
        child._create(self)
        _bindings.node_replace_child_at_index(
            self._ptr_tree, parent._ptr, index, child._ptr
        )
        logger.debug(
            "node_replace_child_at_index(tree: %s, parent: %s, index: %s, child: %s)",
            self._ptr_tree,
            parent._ptr,
            index,
            child._ptr,
        )

        # Set parent of replaced child to None, which will cause it to be dropped from the tree
        replaced.parent = None

    def _node_create(self, node: Node) -> None:
        node._ptr_style = node.style._create()
        node._ptr = _bindings.node_create(self._ptr_tree, node._ptr_style)
        logger.debug(
            "node_create(tree_ptr: %s, style_ptr: %s) -> %s",
            self._ptr_tree,
            node._ptr_style,
            node._ptr,
        )

    def _node_dirty(self, node: Node) -> bool:
        if not node.tree:
            raise Exception(
                f"Node {node.address} is not associated with a tree, cannot get dirty state"
            )
        elif not node._ptr:
            raise Exception(
                f"Node {node.address} is not created in tree, cannot get dirty state"
            )

        dirty = _bindings.node_dirty(self._ptr_tree, node._ptr)
        logger.debug(
            "node_dirty(tree: %s, node: %s) -> %s",
            self._ptr_tree,
            node._ptr,
            dirty,
        )
        return dirty

    def _node_drop(self, node: Node) -> None:
        if not node.tree:
            raise Exception("Node is not associated with a tree, cannot drop it")

        _bindings.node_drop(self._ptr_tree, node._ptr)
        logger.debug("[implicit] style_drop(style: %s)", node._ptr_style)
        logger.debug("node_drop(tree: %s, node: %s)", self._ptr_tree, node._ptr)
        node._ptr = None
        node._ptr_style = None

    def _node_set_measure(self, node: Node) -> None:
        if not node.tree:
            raise Exception(
                "Node is not associated with a tree, cannot set measure function"
            )
        _bindings.node_set_measure(
            self._ptr_tree, node._ptr, node, Node._measure_callback
        )
        logger.debug("node_set_measure(tree: %s, node: %s)", self._ptr_tree, node._ptr)

    def _node_remove_measure(self, node: Node) -> None:
        if not node.tree:
            raise Exception(
                "Node is not associated with a tree, cannot remove measure function"
            )
        _bindings.node_remove_measure(self._ptr_tree, node._ptr)
        logger.debug(
            "node_remove_measure(tree: %s, node: %s)", self._ptr_tree, node._ptr
        )

    def _node_compute_layout(
        self, node: Node, available_space: SizeAvailableSpace = None
    ) -> bool:
        if not node.tree:
            raise Exception("Node is not associated with a tree, cannot get layout")

        if not available_space:
            available_space = SizeAvailableSpace.default()
        result = _bindings.node_compute_layout(
            self._ptr_tree,
            node._ptr,
            available_space.to_dict(),
        )
        logger.debug(
            "node_compute_layout(tree: %s, node: %s) -> success: %s",
            self._ptr_tree,
            node._ptr,
            result,
        )

        self._node_get_layout(node)

        return result

    def _node_get_layout(self, node: Node) -> None:
        if not node.tree:
            raise Exception("Node is not associated with a tree, cannot get layout")
        if node.is_dirty:
            raise Exception("Node is dirty, layout needs to be computed")

        _layout = _bindings.node_get_layout(self._ptr_tree, node._ptr)
        node._layout = Layout(
            _layout["left"], _layout["top"], _layout["width"], _layout["height"]
        )
        node._zorder = _layout["order"]
        logger.debug(
            "node_get_layout(tree: %s, node: %s) -> (order: %s, left: %s, top: %s, width: %s, height: %s)",
            self._ptr_tree,
            node._ptr,
            node._zorder,
            node._layout.x,
            node._layout.y,
            node._layout.width,
            node._layout.height,
        )

        if node.is_visible and node.children:
            for child in node.children:
                self._node_get_layout(child)
