from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from demos.example import print_layout
from stretchable.node import Node
from tests.test_fixtures import apply_node_measure, get_xml


def print_chrome_layout(node: WebElement, index: int = 0):
    print(" " * index + f"is_displayed: {node.is_displayed()}")
    print(" " * index + str(node.rect))
    for prop in ("margin", "border", "padding"):
        print(" " * index + prop + ": " + node.value_of_css_property(prop))
    for child in node.find_elements(by=By.XPATH, value="*"):
        print_chrome_layout(child, index=index + 2)


filepath = Path(
    "/Users/kenneth/Code/Personal/Python/stretchable/tests/fixtures/taffy/percentage_padding_should_calculate_based_only_on_width.html"
    # "/Users/kenneth/Code/Personal/Python/stretchable/tests/fixtures/taffy/max_height_overrides_height_on_root.html"
    # "/Users/kenneth/Code/Personal/Python/stretchable/tests/fixtures/taffy/min_height_overrides_height_on_root.html"
    # "/Users/kenneth/Code/Personal/Python/stretchable/tests/fixtures/taffy/undefined_height_with_min_max.html"
    # "/Users/kenneth/Code/Personal/Python/stretchable/tests/fixtures/taffy/min_width_overrides_max_width.html"
)

# Get layout using taffy
xml = get_xml(filepath)
node = Node.from_xml(xml, apply_node_measure)
node.compute_layout(use_rounding=False)
print("children", len(node))
print_layout(node)

# Get layout using Chrome
driver = webdriver.Chrome()
driver.get("file://" + str(filepath))
driver.implicitly_wait(0.5)
node_expected = driver.find_element(by=By.ID, value="test-root")
print_chrome_layout(node_expected)
driver.quit()
