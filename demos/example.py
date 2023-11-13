import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

from stretchable import Box, Node
from stretchable.style import PCT, Rect, Size


def print_layout(
    node: Node,
    level: int = 0,
    *,
    relative: bool = True,
):
    print(" " * level + "Visible: " + str(node.is_visible))
    print(node.style.margin, node.style.border, node.style.padding)
    for box in Box:
        layout = node.get_frame(box, relative=relative)
        print(" " * level + box._name_ + ": " + str(layout))
    for child in node:
        print_layout(child, level + 2, relative=relative)


def plot_node(node: Node, ax, index: int = 0, flip_y: bool = False):
    for t in Box:
        box = node.get_frame(t, relative=False, flip_y=flip_y)
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
        if t == Box.BORDER:
            ax.annotate(f"Node {index}", (box.x, box.y), color=f"C{index}")

    for child in node:
        plot_node(child, ax, index=index + 1, flip_y=flip_y)


if __name__ == "__main__":
    linestyles = {
        Box.CONTENT: "dotted",
        Box.PADDING: "dashed",
        Box.BORDER: "solid",
        Box.MARGIN: "dashdot",
    }

    m, b, p = 30, 3, 10 * PCT

    root = Node(
        border=Rect(b, b, b, b),
    ).add(
        Node(
            size=Size(300, 200),
            margin=Rect(m, m, m, m),
            border=Rect(b, b, b, b),
            padding=Rect(p, p, p, p),
        ).add(
            Node(
                size=Size(100 * PCT, 100 * PCT),
                border=Rect(b, b, b, b),
                padding=Rect(0.75 * p, 0.75 * p, 0.75 * p, 0.75 * p),
            ).add(
                Node(
                    size=Size(100 * PCT, 100 * PCT),
                    border=Rect(b, b, b, b),
                    padding=Rect(0.5 * p, 0.5 * p, 0.5 * p, 0.5 * p),
                )
            ),
        ),
    )

    w, h = 500, 500
    root.compute_layout(Size(w, h))

    print_layout(root, relative=False)

    fig, ax = plt.subplots(figsize=(420 / 25.4, 297 / 25.4))

    flip_y = False
    plot_node(root, ax, flip_y=flip_y)
    ax.set_xlim(left=0, right=w)
    ax.set_ylim(top=h, bottom=0)
    if not flip_y:
        ax.invert_yaxis()
    ax.axis("equal")

    plt.savefig("demos/example.jpg")
