# stretchable is inspired by/based on stretched (archived) by nmichlo:
# https://github.com/nmichlo/stretched

# Stretch is an implementation of CSS Flexbox written in Rust:
# https://github.com/vislyhq/stretch

# import bindings etc.
# from .node import Box, Layout, Node, reset
# from .style import Rect, Size, Style

from .node import Box, Edge, Node
from .style import Style

__all__ = [
    "Node",
    "Edge",
    "Box",
    "Style",
]


"""
TODO:

  - Implement __str__ for Node class
  - Use __str__ from 1) in logger
  - Support grid_[template/auto]_[rows/columns] in Style
  - Script to download and process fixtures from taffy github? (LOW)

"""
