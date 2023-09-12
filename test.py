import logging

from demos.example import print_layout
from stretchable.node import Node, Tree
from stretchable.style.geometry.length import PCT, PT
from stretchable.style.geometry.rect import Rect
from stretchable.style.geometry.size import Size
from stretchable.style.props import Display, Position
from tests.test_fixtures import _get_xml

logger = logging.getLogger("stretchable")
logger.setLevel(logging.DEBUG)

filepath = "tests/fixtures/absolute_layout_align_items_and_justify_content_center_and_bottom_position.html"
# filepath = "tests/fixtures/align_baseline_nested_column.html"
# filepath = "tests/fixtures/grid_min_content_flex_single_item.html"


def list_nodes(node: Node, index: int = 0) -> None:
    print(
        "  " * index
        + f"{node.address} (node: {node._ptr}, style: {node._ptr_style}, parent: {node.parent._ptr if node.parent else 'None'})"
    )
    for child in node.children:
        list_nodes(child, index + 1)


with Tree.from_xml(_get_xml(filepath)) as tree:
    list_nodes(tree)
    tree.compute_layout()
    print_layout(tree)

# from stretchable.style.geometry.length import (
#     AUTO,
#     PCT,
#     PT,
#     LengthPointsPercent,
#     LengthPointsPercentAuto,
# )
# from stretchable.style.geometry.rect import Rect
# from stretchable.style.geometry.size import (
#     Size,
#     SizePointsPercent,
#     SizePointsPercentAuto,
# )

# size = Size(100, 50 * PCT)
# print(size)

# rect = Rect(left=5 * PCT)
# print(rect)

# # length = LengthPointsPercent.from_any(5 * PCT)

# # size = SizePointsPercentAuto(AUTO, AUTO)
# # print(size)
