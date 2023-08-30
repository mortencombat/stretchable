import logging

from stretchable.core import Node, Root
from stretchable.style import Style

logger = logging.getLogger("stretchable")
logger.setLevel(logging.DEBUG)

root = Root().add(
    Node(style=Style()).add(
        Node(style=Style()),
    ),
)
