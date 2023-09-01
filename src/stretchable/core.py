import logging
from typing import Iterable, Self, SupportsIndex

from stretchable.style import Style

from .taffy import _bindings

# from attrs import define, field

logging.basicConfig(format="%(levelname)s:%(name)s:%(message)s")
logger = logging.getLogger(__name__)


class Children(list):
    def __init__(self, parent: "Node"):
        self._parent = parent

    def append(self, node: "Node"):
        # if self._parent.tree and node._ptr:
        #     # NOTE: this might be redundant, since whenever a new node is added to the tree,
        #     # _added_to_tree will fire first and will include _node_add_child
        #     logger.debug("_node_add_child via Children.append()")
        #     self._parent.tree._node_add_child(self._parent, node)
        if not isinstance(node, Node):
            raise TypeError("Only nodes can be added")
        elif node.parent:
            raise Exception("Node is already associated with a parent node")
        node.parent = self._parent
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
            if self._parent.tree:
                # TODO: Update state on removed child node, eg. drop it and _ptr = None
                self._parent.tree._node_remove_child(self._parent, self[index])
            super().__delitem__(index)

    def __setitem__(self, __index: int, node: "Node") -> None:
        assert __index >= 0 and __index < len(self)
        if self._parent.tree:
            # TODO: Update state on replaced child node, eg. drop it and _ptr = None
            self._parent.tree._node_replace_child_at_index(self._parent, __index, node)
        super().__setitem__(__index, node)


class Node:
    __slots__ = (
        "_style",
        "_children",
        "_measure",
        "_ptr",
        "_layout",
        "_parent",
    )

    def __init__(self, *children, style: Style = None, **kwargs):
        self._ptr = None
        if not style:
            style = Style(**kwargs)
        elif kwargs:
            raise ValueError("Provide only `style` or style attributes, not both")
        self._style = style
        self._children = Children(self)
        self.add(*children)
        self._layout = None
        self._parent = None
        if self.is_tree:
            self._added_to_tree()

    def add(self, *children) -> Self:
        self._children.extend(children)
        return self

    @property
    def style(self) -> Style:
        return self._style

    @property
    def children(self) -> Children:
        return self._children

    @property
    def parent(self) -> Self:
        return self._parent

    @parent.setter
    def parent(self, value: Self) -> None:
        added_to_tree = not self.tree and value.tree
        self._parent = value
        if added_to_tree:
            self._added_to_tree()
            for child in self.children:
                child._added_to_tree()

    def _added_to_tree(self) -> None:
        # Create node
        self._create()

        # Add as child node
        if self.parent and self.tree:
            self.tree._node_add_child(self.parent, self)

    def _create(self, tree: "Tree" = None):
        if self._ptr:
            # Node is already created, tree cannot change
            raise Exception(
                "Node is already associated with a tree, you cannot add it to another tree"
            )

        _tree = tree if tree else self.tree
        if not _tree:
            raise Exception("Cannot create node without a tree")
        self._ptr = _tree._node_create(self.style)

    @property
    def tree(self) -> "Tree":
        """Returns the associated Tree class instance, if this node has been added to the corresponding tree"""
        return self.parent.tree if self.parent else None

    @property
    def is_tree(self) -> bool:
        return False

    def __del__(self) -> None:
        if self.tree and self.tree._ptr_tree and self._ptr:
            _bindings.taffy_node_drop(self.tree._ptr_tree, self._ptr)
            logger.debug("taffy_node_drop(%s)", self._ptr)
            self._ptr = None

    def compute_layout(self):
        if not self.tree:
            raise Exception("Node must be added to a tree based on a Root instance")
        raise NotImplementedError


"""
HANDLING TAFFY/RUST OBJECTS

All objects are created and referred via an i64 pointer.

TAFFY/TREE (ROOT)




NODE

Node is associated with a specific Tree/Root.
When a Node is first instanced, it has no associated Tree.
Possible actions:
    - Add node to parent node, which is not associated with a Tree -> Nothing
    - Parent Node is added to Tree -> Create both parent node and child nodes
    - Add node to parent node, which is associated with a Tree -> Create node and add


Use event propagation system?


STYLE

Style is not associated with a specific Tree/Root.


"""


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

    def _enable_rounding(self):
        _bindings.taffy_enable_rounding(self._ptr_tree)
        logger.debug("taffy_enable_rounding(taffy: %s)", self._ptr_tree)

    def _disable_rounding(self):
        _bindings.taffy_disable_rounding(self._ptr_tree)
        logger.debug("taffy_disable_rounding(taffy: %s)", self._ptr_tree)

    def _node_add_child(self, parent: Node, child: Node):
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

    def _node_replace_child_at_index(self, parent: Node, index: int, child: Node):
        # Get current child at index and drop it (in bindings and class state)
        # current_child = ...
        child._create(self)
        _bindings.taffy_node_replace_child_at_index(
            self._ptr_tree, parent._ptr, index, child._ptr
        )
        # _node_drop(current_child)

        logger.debug(
            "taffy_node_replace_child_at_index(taffy: %s, parent: %s, index: %s, child: %s)",
            self._ptr_tree,
            parent._ptr,
            index,
            child._ptr,
        )

    def _node_create(self, style: Style) -> int:
        ptr = _bindings.taffy_node_create(self._ptr_tree, style._ptr)
        logger.debug("taffy_node_create() -> %s", ptr)
        return ptr
