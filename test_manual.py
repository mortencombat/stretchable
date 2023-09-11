import logging

from stretchable.style import Style
from stretchable.style.geometry.length import PT
from stretchable.style.geometry.size import Size, SizeAvailableSpace
from stretchable.taffy import _bindings

logger = logging.getLogger("stretchable")
logger.setLevel(logging.DEBUG)

ptr_taffy = _bindings.init()

# Root node
style_1 = Style(size=Size(450 * PT, 350 * PT))
ptr_style_1 = style_1._create()
ptr_node_1 = _bindings.node_create(ptr_taffy, ptr_style_1)

# First child
style_2 = Style(size=Size(400 * PT, 500 * PT))
ptr_style_2 = style_2._create()
ptr_node_2 = _bindings.node_create(ptr_taffy, ptr_style_2)
_bindings.node_add_child(ptr_taffy, ptr_node_1, ptr_node_2)

# Second child
style_3 = Style(size=Size(350 * PT, 250 * PT))
ptr_style_3 = style_3._create()
ptr_node_3 = _bindings.node_create(ptr_taffy, ptr_style_3)
_bindings.node_add_child(ptr_taffy, ptr_node_2, ptr_node_3)

available_space = SizeAvailableSpace.default()
result = _bindings.node_compute_layout(
    ptr_taffy,
    ptr_node_1,
    available_space.to_dict(),
)

print(ptr_style_1, ptr_style_2, ptr_style_3)

print(result)

layout_node_1 = _bindings.node_get_layout(ptr_taffy, ptr_node_1)
print(layout_node_1)
layout_node_2 = _bindings.node_get_layout(ptr_taffy, ptr_node_2)
print(layout_node_2)
layout_node_3 = _bindings.node_get_layout(ptr_taffy, ptr_node_3)
print(layout_node_3)

_bindings.free(ptr_taffy)
