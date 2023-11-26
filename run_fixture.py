from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from stretchable.node import Edge, Node
from tests.test_fixtures import apply_node_measure, get_layout_expected, get_xml


def print_layout(
    node: Node,
    level: int = 0,
    *,
    relative: bool = True,
):
    print(" " * level + "Visible: " + str(node.is_visible))
    print(node.style.margin, node.style.border, node.style.padding)
    for box in Edge:
        layout = node.get_box(box, relative=relative)
        print(" " * level + box._name_ + ": " + str(layout))
    for child in node:
        print_layout(child, level + 2, relative=relative)


def plot_node(node: Node, ax, index: int = 0, flip_y: bool = False):
    for t in Edge:
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
        if t == Edge.BORDER:
            ax.annotate(f"Node {index}", (box.x, box.y), color=f"C{index}")

    for child in node:
        plot_node(child, ax, index=index + 1, flip_y=flip_y)


def print_chrome_layout(node: WebElement, index: int = 0):
    print(" " * index + f"is_displayed: {node.is_displayed()}")
    for box in Edge:
        layout = get_layout_expected(node, box)
        print(" " * index + box._name_ + ": " + str(layout))
    for child in node.find_elements(by=By.XPATH, value="*"):
        print_chrome_layout(child, index=index + 2)


"""
grid/grid_margins_percent_start.html -> Box.MARGIN fails
In this file, percentage margins are calculated as a percentage of the elements own width, not the container width as is normally the case. Why?

"""

filepath = Path(
    # "/Users/kenneth/Code/Personal/Python/stretchable/tests/fixtures/flex/percentage_moderate_complexity.html"
    # "/Users/kenneth/Code/Personal/Python/stretchable/tests/fixtures/grid/grid_margins_percent_start.html"
    # "/Users/kenneth/Code/Personal/Python/stretchable/tests/fixtures/grid/grid_max_content_single_item_span_2_gap_fixed.html"
    # "/Users/kenneth/Code/Personal/Python/stretchable/tests/fixtures/flex/gap_percentage_row_gap_wrapping.html"
    "/Users/kenneth/Code/Personal/stretchable/tests/fixtures/flex/percentage_padding_should_calculate_based_only_on_width.html"
    # "/Users/kenneth/Code/Personal/Python/stretchable/tests/fixtures/taffy/max_height_overrides_height_on_root.html"
    # "/Users/kenneth/Code/Personal/Python/stretchable/tests/fixtures/taffy/min_height_overrides_height_on_root.html"
    # "/Users/kenneth/Code/Personal/Python/stretchable/tests/fixtures/taffy/undefined_height_with_min_max.html"
    # "/Users/kenneth/Code/Personal/stretchable/tests/fixtures/flex/min_width_overrides_max_width.html"
)

# Get layout using taffy
xml = get_xml(filepath)
node = Node.from_xml(xml, apply_node_measure)
node.compute_layout(use_rounding=False)
print(str(node))
print("*** ACTUAL ***")
print_layout(node)

# Get layout using Chrome
driver = webdriver.Chrome()
driver.get("file://" + str(filepath))
driver.implicitly_wait(0.5)
node_expected = driver.find_element(by=By.ID, value="test-root")
print("*** EXPECTED ***")
print_chrome_layout(node_expected)
driver.quit()

linestyles = {
    Edge.CONTENT: "dotted",
    Edge.PADDING: "dashed",
    Edge.BORDER: "solid",
    Edge.MARGIN: "dashdot",
}

fig, ax = plt.subplots(figsize=(420 / 25.4, 297 / 25.4))

margin_box = node.get_box(Edge.MARGIN)
plot_node(node, ax, flip_y=True)
ax.set_xlim(left=0, right=margin_box.width)
ax.set_ylim(top=margin_box.height, bottom=0)
ax.axis("equal")

plt.savefig("run_fixture.jpg")
