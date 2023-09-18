import logging
import os
from xml.etree import ElementTree

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from demos.example import print_layout
from stretchable.node import Node, Tree
from tests.test_fixtures import apply_node_measure, get_fixtures, get_xml

logger = logging.getLogger("stretchable.tests")
logger.setLevel(logging.DEBUG)

# filepath = "tests/fixtures/taffy/absolute_aspect_ratio_fill_max_width.html"
filepath = "tests/fixtures/taffy/absolute_aspect_ratio_fill_min_height.html"
# filepath = "tests/fixtures/taffy/grid_aspect_ratio_fill_child_max_height.html"


# def list_nodes(node: Node, index: int = 0) -> None:
#     print(
#         "  " * index
#         + f"{node.address} (node: {node._ptr}, style: {node._ptr_style}, parent: {node.parent._ptr if node.parent else 'None'})"
#     )
#     for child in node.children:
#         list_nodes(child, index + 1)


# def print_chrome_layout(node: WebElement, index: int = 0) -> None:
#     visible = node.is_displayed()
#     x = node.rect["x"]
#     y = node.rect["y"]
#     width = node.rect["width"]
#     height = node.rect["height"]
#     print("  " * index + f"{x=:.1f}, {y=:.1f}, {width=:.1f}, {height=:.1f}, {visible=}")

#     for child in node.find_elements(by=By.XPATH, value="*"):
#         print_chrome_layout(child, index + 1)


# with Tree.from_xml(get_xml(filepath), apply_node_measure) as tree:
#     list_nodes(tree)
#     tree.compute_layout()
#     print_layout(tree)


# driver = webdriver.Chrome()
# driver.get("file://" + os.getcwd() + "/" + filepath)
# driver.implicitly_wait(0.5)
# node_expected = driver.find_element(by=By.ID, value="test-root")
# print_chrome_layout(node_expected)


# def browse(element: ElementTree.Element, index: int = 0):
#     print("  " * index, element.tag, element.text)

#     for child in element:
#         browse(child, index + 1)


# xml = get_xml(filepath)

# tree = ElementTree.fromstring(xml)
# browse(tree)


from stretchable.style.geometry.length import LengthAvailableSpace, LengthPoints
from stretchable.style.geometry.size import SizeAvailableSpace, SizePoints
from tests.test_fixtures import WritingMode, get_fixtures, measure_standard_text

text = "HH\u200bHH\u200bHH\u200bHH\u200bHH\u200bHH\u200bHH\u200bHH\u200bHH\u200bHH\u200bHH\u200bHH\u200bHH\u200bHH"
writing_mode = WritingMode.HORIZONTAL
available_space = SizeAvailableSpace(LengthAvailableSpace.min_content(), 20)
known_dims = SizePoints(width=50)
aspect_ratio = 3

result = measure_standard_text(
    available_space, text, writing_mode, known_dims, aspect_ratio
)
print(result)
