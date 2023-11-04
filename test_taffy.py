import logging

from stretchable.node import Node, Tree
from stretchable.style.geometry.size import Size, SizeAvailableSpace, SizePoints

logger = logging.getLogger("stretchable")
logger.setLevel(logging.DEBUG)


def measure_test(
    known_dims: SizePoints, available_space: SizeAvailableSpace
) -> SizePoints:
    print("measure_test invoked, with:")
    print("  ", known_dims)
    print("  ", available_space)
    r = SizePoints(width=100, height=known_dims.height)
    print("returning", r)
    return r


with Tree() as tree:
    tree.use_rounding = False

    node_1 = Node(id="main")
    tree.add(node_1)
    node_2 = Node(id="header")
    node_1.add(node_2)
    node_3 = Node(id="body", size=Size(150, 200))
    node_1.add(node_3)
    node_4 = Node(id="footer")  # , measure=measure_test)
    node_1.add(node_4)

    tree.compute_layout()

    # for node in (tree, node_1, node_2, node_3, node_4):
    #     print(node.address)

    # node_header = tree.find("./main/footer")
    # print(node_header.address, node_header.id)

    # node_1.children.remove(node_4)
    # node_1.children.append(node_4)
    # # del node_1.children[0:2]
    # node_1.children[1] = Node(style=Style())
    # for c in node_1.children:
    #     print(c._ptr)
