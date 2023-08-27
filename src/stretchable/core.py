import logging
from typing import Iterable, Self, SupportsIndex

from attrs import define, field

from .taffy import _bindings

# from attrs import define, field

logging.basicConfig(format="%(levelname)s:%(name)s:%(message)s")
logger = logging.getLogger("stretchable")


class Children(list):
    def __init__(self, parent: "Node"):
        self._parent = parent

    def append(self, node: "Node"):
        # _bindings.stretch_node_add_child(
        #     Stretch.get_ptr(), self._parent._ptr, node._ptr
        # )
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


@define(frozen=True)
class Style:
    _ptr: int = field(init=False, default=None)

    def __attrs_post_init__(self):
        object.__setattr__(self, "_ptr", _bindings.taffy_style_create())
        logger.debug("taffy_style_create -> %s", self._ptr)

    def __del__(self):
        if self._ptr:
            _bindings.taffy_style_drop(self._ptr)
            logger.debug("taffy_style_drop(%s)", self._ptr)


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

    def add(self, *children) -> Self:
        self._children.extend(children)
        return self

    @property
    def children(self) -> Children:
        return self._children

    @property
    def parent(self) -> Self:
        return self._parent

    @parent.setter
    def parent(self, value: Self) -> None:
        self._parent = value

        if not self._ptr and self.taffy:
            self._ptr = _bindings.taffy_node_create(
                self.taffy._ptr_taffy, self.style._ptr
            )
            logger.debug("taffy_node_create -> %s", self._ptr)

    @property
    def taffy(self) -> "Taffy":
        """Returns the associated Taffy class instance, if this node has been added to the corresponding tree"""
        return self.parent.taffy if self.parent else None

    @property
    def is_node(self) -> bool:
        return True

    def __del__(self) -> None:
        if self._ptr:
            _bindings.taffy_node_drop(self._ptr)
            logger.debug("taffy_node_drop(%s)", self._ptr)

    def compute_layout(self):
        raise NotImplementedError


class Taffy(Node):
    __slots__ = ("_ptr_taffy",)

    def __init__(self) -> None:
        super().__init__()
        self._ptr_taffy = _bindings.taffy_init()
        logger.debug("taffy_init -> %s", self._ptr_taffy)

    def __del__(self) -> None:
        _bindings.taffy_free(self._ptr_taffy)
        logger.debug("taffy_free(%s)", self._ptr_taffy)

    @property
    def taffy(self) -> Self:
        return self

    @property
    def is_node(self) -> bool:
        return False
