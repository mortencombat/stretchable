import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

from stretchable import Node, reset
from stretchable.style import Rect, Size, pct

reset()


def print_layout(node: Node, level: int = 0):
    box = node.get_box()
    print(" " * level + str(box))
    for child in node.children:
        print_layout(child, level + 2)


def plot_node(node, ax):
    # TODO: plot node
    box = node.get_box()
    ax.add_patch(
        Rectangle(
            (box.x, box.y), box.width, box.height, edgecolor="k", facecolor="none"
        )
    )

    for child in node.children:
        plot_node(child, ax)


m, b, p = 20, 2.5 * pct, 12.15

root = Node().add(
    Node(
        size=Size(300, 200),
        padding=Rect(p, p, p, p),
        margin=Rect(m, m, m, m),
        border=Rect(b, b, b, b),
    ).add(
        Node(size=Size(100 * pct, 100 * pct)),
    ),
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

# %%
