# import logging

# from stretchable.parser import load

# logger = logging.getLogger("stretchable.parser")
# logger.setLevel(logging.DEBUG)

# filepath = "test.html"


# def print_nodes(node, level: int = 0):
#     print(" " * level * 2, node)
#     for e in node:
#         print_nodes(e, level + 1)


# root = load(filepath)
# print_nodes(root)

import tinycss2

# from stretchable.style import GridPlacement
from stretchable.style.parser import strip

# if isinstance(None, str):
#     print("is str")
# else:
#     print("is None")

# from stretchable.style.props import GridIndex

# css = " grid-column: 3 / 2 "
css = "   "
nodes = tinycss2.parse_component_value_list(css, skip_comments=True)
print(nodes)
stripped = strip(nodes, internal=False)
print(stripped)

# grid = GridPlacement.from_inline(css)  # , axis="row")

# print(grid)
