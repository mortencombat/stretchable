import logging

from stretchable.core import Node, Root
from stretchable.style import Style

logger = logging.getLogger("stretchable")
logger.setLevel(logging.DEBUG)

with Root() as root:
    root.rounding_enabled = False
    root.add(
        Node(style=Style()).add(
            Node(style=Style()),
        ),
    )


# root = Root().add(
#     Node(style=Style()).add(
#         Node(style=Style()),
#     ),
# )
