from stretchable.node import Node, Size, Tree


def test_dirty():
    with Tree() as tree:
        node = Node()
        tree.add(node)
        node.compute_layout()
        assert not node.dirty
        node.mark_dirty()
        assert node.dirty


# def test_layout_node():
#     with Tree() as tree:
#         node = Node(size=Size(100, 100))
#         tree.add(node)
#         layout = node.compute_layout()
#         assert layout.width == 100.0
#         assert layout.height == 100.0


# def test_layout_leaf():
#     reset()

#     node = Node(measure=lambda w, h: (100, 100))
#     layout = node.compute_layout()
#     assert layout.width == 100.0
#     assert layout.height == 100.0
#     node.dispose()


# def test_node_with_children():
#     reset()

#     child1 = Node(size=Size(100, 100))
#     child2 = Node(size=Size(200, 200))
#     node = Node(child1, child2)

#     assert len(node.children) == 2
#     layout = node.compute_layout()
#     assert layout.width == 300
#     assert layout.height == 200

#     del node.children[0]

#     assert len(node.children) == 1
#     layout = node.compute_layout()
#     assert layout.width == 200
#     assert layout.height == 200


# def test_replace_child_node():
#     reset()

#     child1 = Node(size=Size(100, 100))
#     child2 = Node(size=Size(200, 200))
#     node = Node(child1)
#     node.children[0] = child2
#     layout = node.compute_layout()
#     assert layout.width == 200
#     assert layout.height == 200
