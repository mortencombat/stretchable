import logging

from stretchable.style import Style
from stretchable.style.geometry.length import PT, LengthAvailableSpace
from stretchable.style.geometry.size import Size, SizeAvailableSpace
from stretchable.taffy import _bindings

logger = logging.getLogger("stretchable")
logger.setLevel(logging.DEBUG)

ptr_taffy = _bindings.init()

size_1 = Size(500 * PT, 320 * PT)
size_2 = Size(310 * PT, 260 * PT)
size_3 = Size(260 * PT, 210 * PT)

# # Second child
style_3 = Style(size=size_3)
ptr_style_3 = style_3._create()
ptr_node_3 = _bindings.node_create(ptr_taffy, ptr_style_3)

# # First child
style_2 = Style(size=size_2)
ptr_style_2 = style_2._create()
ptr_node_2 = _bindings.node_create(ptr_taffy, ptr_style_2)
_bindings.node_add_child(ptr_taffy, ptr_node_2, ptr_node_3)

# # Root node
style_1 = Style(size=size_1)
ptr_style_1 = style_1._create()
ptr_node_1 = _bindings.node_create(ptr_taffy, ptr_style_1)
_bindings.node_add_child(ptr_taffy, ptr_node_1, ptr_node_2)

available_space = SizeAvailableSpace(LengthAvailableSpace.max_content())
result = _bindings.node_compute_layout(
    ptr_taffy,
    ptr_node_1,
    available_space.to_dict(),
)

print("compute_layout", result)

for ptr, ptr_style in (
    (ptr_node_1, ptr_style_1),
    (ptr_node_2, ptr_style_2),
    (ptr_node_3, ptr_style_3),
):
    layout = _bindings.node_get_layout(ptr_taffy, ptr)
    print(ptr, ptr_style, layout)

_bindings.free(ptr_taffy)
