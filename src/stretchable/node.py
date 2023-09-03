import logging
import re
from enum import StrEnum, auto
from typing import Callable, Iterable, Self, SupportsIndex

from attrs import define

from stretchable.style.core import Size, Style
from stretchable.style.dimension import MAX_CONTENT

from .taffy import _bindings

logging.basicConfig(format="%(levelname)s:%(name)s:%(message)s")
logger = logging.getLogger(__name__)

_valid_id = re.compile(r"^[-_!:;()\]\[a-zA-Z0-9]*[a-zA-Z]+[-_!:;()\]\[a-zA-Z0-9]*$")

"""
TODO:

 1) Implement __str__ for classes
 2) Use __str__ from 1) in logger
 3) Refactor (?) Length/Size in style.dimension to enforce different types of
    lengths: Some places only points are supported, other places points,
    percentages and maybe auto is supported. In layouting (compute_layout and
    measure functions) "min content" and "max content" concepts are supported.
 4) Measure function support
 5) Support grid_[template/auto]_[rows/columns] in Style
"""


class NodeLocatorError(Exception):
    pass


class NodeNotFound(Exception):
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
        measure: Callable[[Size, Size], Size] = None,
        style: Style = None,
        **style_args,
    ):
        self._ptr = None
        self._layout = None
        self._zorder = None
        self._parent = None

        """
        _summary_

        Arguments:
            measure:    a callable that takes (available_space: Size[AvailableSpace], known_dimensions: Size[float]) and returns Size[float]

        Raises:
            ValueError: _description_
            ValueError: _description_
        """

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

        set_tree = not self.tree and value and value.tree
        self._parent = value
        if set_tree:
            self._add_to_tree()
            for child in self.children:
                child._add_to_tree()

    def _add_to_tree(self) -> None:
        if self.tree and not self._ptr:
            # Create node
            self._create()

            # Add as child node
            if self.parent and self.tree:
                self.tree._node_add_child(self.parent, self)

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

    def __del__(self) -> None:
        if self.tree and self.tree._ptr_tree and self._ptr:
            self.tree._node_drop(self)
            # _bindings.taffy_node_drop(self.tree._ptr_tree, self._ptr)
            # logger.debug("taffy_node_drop(%s)", self._ptr)
            # self._ptr = None

    def compute_layout(self, available_space: Size = None):
        if not self.tree:
            raise Exception("Node must be added to a tree before computing layout")
        self.tree._node_compute_layout(self, available_space)


class Tree(Node):
    __slots__ = ("_ptr_tree", "_rounding_enabled")

    def __init__(self) -> None:
        self._rounding_enabled = True
        self._ptr_tree = _bindings.taffy_init()
        logger.debug("taffy_init() -> %s", self._ptr_tree)
        super().__init__()

    def __del__(self) -> None:
        if hasattr(self, "_ptr_taffy") and self._ptr_tree:
            _bindings.taffy_free(self._ptr_tree)
            logger.debug("taffy_free(taffy: %s) via __del__", self._ptr_tree)
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
            _bindings.taffy_free(self._ptr_tree)
            logger.debug("taffy_free(taffy: %s) via __exit__", self._ptr_tree)
            self._ptr_tree = None

    # Bindings

    def _enable_rounding(self) -> None:
        _bindings.taffy_enable_rounding(self._ptr_tree)
        logger.debug("taffy_enable_rounding(taffy: %s)", self._ptr_tree)

    def _disable_rounding(self) -> None:
        _bindings.taffy_disable_rounding(self._ptr_tree)
        logger.debug("taffy_disable_rounding(taffy: %s)", self._ptr_tree)

    def _node_add_child(self, parent: Node, child: Node) -> None:
        _bindings.taffy_node_add_child(self._ptr_tree, parent._ptr, child._ptr)
        logger.debug(
            "taffy_node_add_child(taffy: %s, parent: %s, child: %s)",
            self._ptr_tree,
            parent._ptr,
            child._ptr,
        )

    def _node_remove_child(self, parent: Node, child: Node):
        _bindings.taffy_node_remove_child(self._ptr_tree, parent._ptr, child._ptr)
        logger.debug(
            "taffy_node_remove_child(taffy: %s, parent: %s, child: %s)",
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
        _bindings.taffy_node_replace_child_at_index(
            self._ptr_tree, parent._ptr, index, child._ptr
        )
        logger.debug(
            "taffy_node_replace_child_at_index(taffy: %s, parent: %s, index: %s, child: %s)",
            self._ptr_tree,
            parent._ptr,
            index,
            child._ptr,
        )

        # Set parent of replaced child to None, which will cause it to be dropped from the tree
        replaced.parent = None

    def _node_create(self, node: Node) -> None:
        node._ptr_style = node.style._create()
        node._ptr = _bindings.taffy_node_create(self._ptr_tree, node._ptr_style)
        logger.debug(
            "taffy_node_create(taffy: %s, style: %s) -> %s",
            self._ptr_tree,
            node._ptr_style,
            node._ptr,
        )

    def _node_dirty(self, node: Node) -> bool:
        if node.tree:
            dirty = _bindings.taffy_node_dirty(self._ptr_tree, node._ptr)
            logger.debug(
                "taffy_node_dirty(taffy: %s, node: %s) -> %s",
                self._ptr_tree,
                node._ptr,
                dirty,
            )
            return dirty

    def _node_drop(self, node: Node) -> None:
        if not node.tree:
            raise Exception("Node is not associated with a tree, cannot get layout")

        _bindings.taffy_node_drop(self._ptr_tree, node._ptr)
        logger.debug("[implicit] taffy_style_drop(style: %s)", node._ptr_style)
        logger.debug("taffy_node_drop(taffy: %s, node: %s)", self._ptr_tree, node._ptr)
        node._ptr = None
        node._ptr_style = None

    def _node_compute_layout(self, node: Node, available_space: Size = None) -> bool:
        if not node.tree:
            raise Exception("Node is not associated with a tree, cannot get layout")

        if not available_space:
            available_space = Size(MAX_CONTENT, MAX_CONTENT)
        result = _bindings.taffy_node_compute_layout(
            self._ptr_tree,
            node._ptr,
            available_space.to_taffy(),
        )
        logger.debug(
            "taffy_node_compute_layout(taffy: %s, node: %s) -> success: %s",
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

        _layout = _bindings.taffy_node_get_layout(self._ptr_tree, node._ptr)
        node._layout = Layout(
            _layout["left"], _layout["top"], _layout["width"], _layout["height"]
        )
        node._zorder = _layout["order"]
        logger.debug(
            "taffy_node_get_layout(taffy: %s, node: %s) -> (order: %s, left: %s, top: %s, width: %s, height: %s)",
            self._ptr_tree,
            node._ptr,
            node._zorder,
            node._layout.x,
            node._layout.y,
            node._layout.width,
            node._layout.height,
        )

        if node.children:
            for child in node.children:
                self._node_get_layout(child)
