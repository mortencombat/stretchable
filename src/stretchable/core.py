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
        # _bindings.stretch_node_add_child(
        #     Stretch.get_ptr(), self._parent._ptr, node._ptr
        # )
        if not isinstance(node, Node):
            raise TypeError("Only nodes can be added")
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
            # _bindings.stretch_node_remove_child(
            #     Stretch.get_ptr(), self._parent._ptr, self[index]._ptr
            # )
            super().__delitem__(index)

    def __setitem__(self, __index: int, node: "Node") -> None:
        assert __index >= 0 and __index < len(self)
        # _bindings.stretch_node_replace_child_at_index(
        #     Stretch.get_ptr(), self._parent._ptr, __index, node._ptr
        # )
        super().__setitem__(__index, node)


# NOTE! It does not really make sense that Taffy should subclass Children, rather it might subclass Node? Eg. it could be the root node?


"""
Suggested design approach:

Nodes, styles, etc. are initially created as pure Python objects.
Only when they are added to an instance of Taffy, are the corresponding objects created in Taffy.
The corresponding objects should be created as soon the objects are added to the Taffy instance.
This ensures that all objects added to a Taffy instance have corresponding objects in Taffy.

"""


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
        # self._ptr = _bindings.stretch_node_create(Stretch.get_ptr(), self.style._ptr)
        self._children = Children(self)
        self.add(*children)
        # self.measure = measure
        self._layout = None
        self._parent = None
        if self.is_root:
            self._added_to_root()

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
        added_to_root = not self.root and value.root
        self._parent = value
        if added_to_root:
            self._added_to_root()
            for child in self.children:
                child._added_to_root()

    def _added_to_root(self) -> None:
        if self._ptr:
            # Node is already created, root cannot change
            raise Exception(
                "Node is already associated with a tree, you cannot add it to another tree"
            )

        # Create node
        self._ptr = _bindings.taffy_node_create(self.root._ptr_taffy, self.style._ptr)
        logger.debug("taffy_node_create() -> %s", self._ptr)

        # Add as child node
        if self.parent:
            _bindings.taffy_node_add_child(
                self.root._ptr_taffy, self.parent._ptr, self._ptr
            )
            logger.debug(
                "taffy_node_add_child(%s, %s, %s)",
                self.root._ptr_taffy,
                self.parent._ptr,
                self._ptr,
            )

    @property
    def root(self) -> "Root":
        """Returns the associated Root class instance, if this node has been added to the corresponding tree"""
        return self.parent.root if self.parent else None

    @property
    def is_root(self) -> bool:
        return False

    def __del__(self) -> None:
        if self.root and self.root._ptr_taffy and self._ptr:
            _bindings.taffy_node_drop(self.root._ptr_taffy, self._ptr)
            logger.debug("taffy_node_drop(%s)", self._ptr)
            self._ptr = None

    def compute_layout(self):
        if not self.root:
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


class Root(Node):
    __slots__ = ("_ptr_taffy", "_rounding_enabled")

    def __init__(self) -> None:
        self._rounding_enabled = True
        self._ptr_taffy = _bindings.taffy_init()
        logger.debug("taffy_init -> %s", self._ptr_taffy)
        super().__init__()

    def __del__(self) -> None:
        if hasattr(self, "_ptr_taffy") and self._ptr_taffy:
            _bindings.taffy_free(self._ptr_taffy)
            logger.debug("taffy_free(%s) via __del__", self._ptr_taffy)
            self._ptr_taffy = None

    @property
    def rounding_enabled(self) -> bool:
        return self._rounding_enabled

    @rounding_enabled.setter
    def rounding_enabled(self, value: bool) -> None:
        if value == self._rounding_enabled:
            return
        if value:
            _bindings.taffy_enable_rounding(self._ptr_taffy)
            logger.debug("taffy_enable_rounding(%s)", self._ptr_taffy)
        else:
            _bindings.taffy_disable_rounding(self._ptr_taffy)
            logger.debug("taffy_disable_rounding(%s)", self._ptr_taffy)
        self._rounding_enabled = value

    @property
    def root(self) -> Self:
        return self

    @property
    def is_root(self) -> bool:
        return True

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> Self:
        if hasattr(self, "_ptr_taffy") and self._ptr_taffy:
            _bindings.taffy_free(self._ptr_taffy)
            logger.debug("taffy_free(%s) via __exit__", self._ptr_taffy)
            self._ptr_taffy = None
