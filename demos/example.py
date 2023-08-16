import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

from stretchable import BoxType, Node, reset
from stretchable.style import Rect, Size, pct

reset()


def print_layout(
    node: Node,
    level: int = 0,
    *,
    box_type: BoxType = BoxType.PADDING,
    relative: bool = True,
):
    for t in BoxType:
        box = node.get_box(box_type=t, relative=relative)
        print(" " * level + t._name_ + ": " + str(box))
    for child in node.children:
        print_layout(child, level + 2, box_type=box_type, relative=relative)


linestyles = {
    BoxType.CONTENT: "dotted",
    BoxType.PADDING: "dashed",
    BoxType.BORDER: "solid",
    BoxType.MARGIN: "dashdot",
}


def plot_node(node: Node, ax, index: int = 0, flip_y: bool = False):
    for t in BoxType:
        box = node.get_box(t, relative=False, flip_y=flip_y)
        ax.add_patch(
            Rectangle(
                (box.x, box.y),
                box.width,
                box.height,
                edgecolor=f"C{index}",
                linestyle=linestyles[t],
                facecolor="none",
            )
        )

    for child in node.children:
        plot_node(child, ax, index=index + 1, flip_y=flip_y)


m, b, p = 10 * pct, 2.5, 12

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

# THERE IS AN ISSUE WITH PERCENTAGES
# HOW DOES CSS/STRETCH INTERPRET PERCENTAGES
# If using

w, h = 500, 500
layout = root.compute_layout(Size(w, h))

print_layout(root, box_type=BoxType.MARGIN, relative=False)

fig, ax = plt.subplots(figsize=(420 / 25.4, 297 / 25.4))

# NEXT STEP:
#   1) Plot all boxes for all nodes, to verify that everything lines up
#   2) Test with flip_y

plot_node(root, ax)
ax.set_xlim(left=0, right=w)
ax.set_ylim(top=h, bottom=0)
ax.invert_yaxis()
ax.axis("equal")

plt.savefig("demos/example.jpg")

# %%
