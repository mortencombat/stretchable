import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

from stretchable import Node, Rect, Size, Style, pct, pt, reset

reset()


def print_layout(node, level: int = 0):
    print(
        " " * level
        + f"x={node.x:.1f}, y={node.y:.1f}, width={node.width:.1f}, height={node.height:.1f}"
    )
    for child in node.children:
        print_layout(child, level + 2)


def plot_node(node, ax):
    # TODO: plot node
    ax.add_patch(
        Rectangle(
            (node.x, node.y), node.width, node.height, edgecolor="k", facecolor="none"
        )
    )

    for child in node.children:
        plot_node(child, ax)


p, m, b = 50 * pt, 20 * pt, 15 * pt

root = Node(
    style=Style(
        padding=Rect(start=0 * pt, end=0 * pt, top=50 * pt, bottom=0 * pt),
    ),
    children=[
        Node(
            style=Style(
                size=Size(200 * pt, 200 * pt),
                padding=Rect(p, p, p, p),
                margin=Rect(m, m, m, m),
                border=Rect(b, b, b, b),
            ),
        )
    ],
)


w, h = 500, 500
layout = root.compute_layout(Size(w, h))

print_layout(root)

fig, ax = plt.subplots(figsize=(420 / 25.4, 297 / 25.4))

plot_node(root, ax)
ax.set_xlim(left=0, right=w)
ax.set_ylim(top=h, bottom=0)
ax.invert_yaxis()
ax.axis("equal")

plt.savefig("demos/example.jpg")
