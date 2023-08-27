import logging

from stretchable.core import Node, Style, Taffy

logger = logging.getLogger("stretchable")
logger.setLevel(logging.DEBUG)

taffy = Taffy()

taffy.add(
    Node(Style()).add(
        Node(Style()),
    ),
)
