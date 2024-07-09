from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from stretchable.node import Edge, Node
from tests.test_fixtures import apply_node_measure, get_layout_expected, get_xml


def print_layout(node: Node, index: int = 0):
    print(" " * index + f"is_visible: {node.is_visible}")
    for box in Edge:
        layout = node.get_box(box)
        print(" " * index + box._name_ + ": " + str(layout))
    for child in node:
        print_layout(child, index=index + 2)


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
    # "/Users/kenneth/Code/Personal/Python/stretchable/tests/fixtures/flex/percentage_padding_should_calculate_based_only_on_width.html"
    # "/Users/kenneth/Code/Personal/Python/stretchable/tests/fixtures/taffy/max_height_overrides_height_on_root.html"
    # "/Users/kenneth/Code/Personal/Python/stretchable/tests/fixtures/taffy/min_height_overrides_height_on_root.html"
    # "/Users/kenneth/Code/Personal/Python/stretchable/tests/fixtures/taffy/undefined_height_with_min_max.html"
    "/Users/kenneth/Code/Personal/stretchable/tests/fixtures/block/block_overflow_scrollbars_overridden_by_available_space.html"
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
