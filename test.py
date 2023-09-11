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

filepath = "tests/fixtures/absolute_aspect_ratio_fill_height.html"

# xml = _get_xml(filepath)
# with Tree() as tree:
#     node = Node.from_xml(xml)
#     tree.add(node)
#     tree.compute_layout()
#     print(tree.style.size)
#     print(tree.children[0].style.size, node.id)
#     print(tree.children[0].children[0].style.size)
#     # print_layout(node)

tree = Tree().add(
    Node(size=Size(450 * PT, 350 * PT)).add(
        Node(size=Size(400 * PT, 300 * PT)).add(
            Node(
                size=Size(width=50 * PCT),
                inset=Rect(left=5 * PCT, top=5 * PCT),
                aspect_ratio=3.0,
                position=Position.ABSOLUTE,
            )
        )
    )
)

tree.compute_layout()

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
