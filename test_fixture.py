from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from demos.example import print_layout
from stretchable.node import Node
from tests.test_fixtures import apply_node_measure, get_xml


def print_chrome_layout(node: WebElement, index: int = 0):
    print(" " * index + str(node.rect))
    for child in node.find_elements(by=By.XPATH, value="*"):
        print_chrome_layout(child, index=index + 2)


filepath = Path(
    "/Users/kenneth/Code/Personal/Python/stretchable/tests/fixtures/taffy/aspect_ratio_flex_row_fill_max_height.html"
)

# Get layout using taffy
xml = get_xml(filepath)
node = Node.from_xml(xml, apply_node_measure)
node.compute_layout(use_rounding=False)
print_layout(node)


# Get layout using Chrome
driver = webdriver.Chrome()
driver.get("file://" + str(filepath))
driver.implicitly_wait(0.5)
node_expected = driver.find_element(by=By.ID, value="test-root")
print_chrome_layout(node_expected)
driver.quit()
