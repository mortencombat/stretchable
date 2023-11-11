from stretchable.node import Node
from stretchable.style.geometry.length import AUTO, PCT
from stretchable.style.geometry.rect import RectPointsPercentAuto
from stretchable.style.geometry.size import SizeAvailableSpace
from stretchable.style.props import Position

view = Node(size=(100, 100))
node = Node(
    size=(600, 400),
    margin=AUTO,
    position=Position.ABSOLUTE,
    inset=RectPointsPercentAuto(left=100),
)
# view.add(node)
node.compute_layout()

# layout = view.get_layout()
# print(layout)
layout = node.get_layout()
print(layout)

# TODO: test with Chrome

# TAKEWAYS: is inset switching x and y?
# Add a faux box containing the root node?
