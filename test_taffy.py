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
    node_4 = Node(style=Style())
    node_1.add(node_4)

    node_1.children.remove(node_4)
    print(node_4._parent)
    print(node_4._ptr)
    node_1.children.append(node_4)
    # del node_1.children[0:2]
    # node_1.children[1] = Node(style=Style())
    # for c in node_1.children:
    #     print(c._ptr)
