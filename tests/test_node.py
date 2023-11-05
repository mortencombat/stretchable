import pytest

from stretchable import Node
from stretchable.exceptions import NodeNotFound


def test_dirty():
    node = Node()
    assert node.is_dirty
    node.compute_layout()
    assert not node.is_dirty
    node.mark_dirty()
    assert node.is_dirty


def test_node_replace_child():
    root = Node()
    for i in range(5):
        root.add(Node(key=f"{i}A"))
    assert root[2].key == "2A"
    root[2] = Node(key="2B")
    assert root[2].key == "2B"
    root[1:4] = [Node(key="1C"), Node(key="2C"), Node(key="3C")]
    for i in range(1, 4):
        assert root[i].key == f"{i}C"


def test_node_find():
    root = Node(key="root").add(
        Node(key="first-child"),
        Node(key="second-child").add(
            Node(key="sub-child-1"),
            Node(),
            Node(),
        ),
    )

    assert root.find("/second-child/sub-child-1").key == "sub-child-1"
    assert root.find("/second-child/1").address == "/second-child/1"
    assert root.find("./0").key == "first-child"
    assert root.find("/1/0").key == "sub-child-1"
    assert root.find("second-child/0").key == "sub-child-1"
    with pytest.raises(NodeNotFound):
        root.find("/non-existing-node")
    with pytest.raises(NodeNotFound):
        root.find("/2")
    with pytest.raises(NodeNotFound):
        root.find("2")
