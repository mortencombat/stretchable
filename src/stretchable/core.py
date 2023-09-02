import logging
from typing import Iterable, Self, SupportsIndex

from attrs import define

from stretchable.style import Style

from .taffy import _bindings

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


class Node:
    __slots__ = (
        "_id",
        "_style",
        "_children",
        "_measure",
        "_ptr",
        "_ptr_style",
        "_layout",
        "_parent",
    )

    # TODO: Node should also handle style_create and style_drop, tracking ptr_style

    def __init__(self, *children, id: str = None, style: Style = None, **kwargs):
        self._ptr = None
        if not style:
            style = Style(**kwargs)
        elif kwargs:
            raise ValueError("Provide only `style` or style attributes, not both")
        self._style = style
        self._ptr_style = None
        self._children = Children(self)
        self.add(*children)
        self._layout = None
        self._parent = None
        # TODO: validate id, eg:
        #   1) check that id is valid (valid chars) or None
        #   2) check that there are no id collisions with nodes on the same level
        #      (this should also be enforced when parent is set)
        # Node id requirements:
        #   May consist of -_!:;()[] a-z A-Z 0-9
        #   Must contain at least one alphabetical character
        self._id = id
        if self.is_tree:
            self._add_to_tree()

    def add(self, *children) -> Self:
        self._children.extend(children)
        return self

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
        raise NotImplementedError

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
        if value is None and self._ptr and self.tree and not self.is_tree:
            # Node is currently added to tree, but is being removed
            # Drop it from the tree
            self._drop()
            self._parent = None
            return

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

        self._ptr = _tree._node_create(self.style)

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
        self._ptr = None

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

    def _node_create(self, style: Style) -> int:
        logger.debug("before taffy_node_create()")
        # Issue with "double free" is related to Style.
        # Even though style is not dropped when node is dropped, and style is not associated with a specific
        # tree, when creating a node using the same style it fails.
        # Maybe taffy is automatically dropping the style when the node with associated style is dropped?
        # Then the _ptr is invalid because it was already dropped.
        # Implement create and drop methods on style.
        ptr = _bindings.taffy_node_create(self._ptr_tree, Style()._ptr)  # style._ptr)
        logger.debug("taffy_node_create() -> %s", ptr)
        return ptr

    def _node_drop(self, node: Node) -> None:
        _bindings.taffy_node_drop(self._ptr_tree, node._ptr)
        logger.debug("taffy_node_drop(taffy: %s, node: %s)", self._ptr_tree, node._ptr)
