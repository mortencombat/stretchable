import logging

from stretchable.core import Node, Taffy
from stretchable.style import Style

logger = logging.getLogger("stretchable")
logger.setLevel(logging.DEBUG)

taffy = Taffy()

taffy.add(
    Node(style=Style()).add(
        Node(style=Style()),
    ),
)
