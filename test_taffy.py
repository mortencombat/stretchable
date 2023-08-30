import logging

from stretchable.core import Node, Root
from stretchable.style import Style

logger = logging.getLogger("stretchable")
logger.setLevel(logging.DEBUG)

with Root() as root:
    root.rounding_enabled = False
    node_1 = Node(style=Style())
    node_2 = Node(style=Style())
    node_1.add(node_2)
    root.add(node_2)
    # Now node_1 thinks node_2 is a child, but node_2 is actually a child of root
