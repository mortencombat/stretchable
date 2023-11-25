from stretchable import Edge, Node
from stretchable.style import AUTO, PCT

# Build node tree
root = Node(
    margin=20,
    size=(500, 300),
).add(
    Node(border=5, size=(50 * PCT, AUTO)),
    Node(key="child", padding=10 * PCT, size=50 * PCT),
)

# Compute layout
root.compute_layout()

# Get the second child node
child_node = root.find("/child")
content_box = child_node.get_box(Edge.CONTENT)
print(content_box)
