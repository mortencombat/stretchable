from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from stretchable.node import Edge, Node
from stretchable.parser import load
from tests.test_fixtures import TestFixtureNodeFactory, get_layout_expected


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


filepath = Path(
    "tests/fixtures/grid/grid_absolute_align_self_sized_all.html",
    # "tests/fixtures/flex/absolute_aspect_ratio_fill_height.html",
    # "tests/fixtures/flex/percentage_padding_should_calculate_based_only_on_width.html",
).resolve()

# Get layout using taffy
node = load(filepath, nodefactory=TestFixtureNodeFactory())
node.compute_layout(use_rounding=False)
print(str(node))
print("*** ACTUAL ***")
print_layout(node[0])

# Get layout using Chrome
driver = webdriver.Chrome()
driver.get(f"file://{filepath}")
driver.implicitly_wait(0.5)
node_expected = driver.find_element(by=By.ID, value="test-root")
print("*** EXPECTED ***")
print_chrome_layout(node_expected)
driver.quit()
