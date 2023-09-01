import logging

from stretchable.core import Node, Tree
from stretchable.style import Style

logger = logging.getLogger("stretchable")
logger.setLevel(logging.DEBUG)

with Tree() as tree:
    # tree.rounding_enabled = False
    node_1 = Node(style=Style())
    tree.add(node_1)
    node_2 = Node(style=Style())
    node_1.add(node_2)
    node_3 = Node(style=Style())
    node_1.add(node_3)
    node_1.children[1] = Node(style=Style())
    for c in node_1.children:
        print(c._ptr)
