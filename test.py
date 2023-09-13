import logging
import os

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from demos.example import print_layout
from stretchable.node import Node, Tree
from tests.test_fixtures import _get_xml

logger = logging.getLogger("stretchable")
logger.setLevel(logging.DEBUG)

filepath = "tests/fixtures/stretch/display_none_with_child.html"


def list_nodes(node: Node, index: int = 0) -> None:
    print(
        "  " * index
        + f"{node.address} (node: {node._ptr}, style: {node._ptr_style}, parent: {node.parent._ptr if node.parent else 'None'})"
    )
    for child in node.children:
        list_nodes(child, index + 1)


def print_chrome_layout(node: WebElement, index: int = 0) -> None:
    visible = node.is_displayed()
    x = node.rect["x"]
    y = node.rect["y"]
    width = node.rect["width"]
    height = node.rect["height"]
    print("  " * index + f"{x=:.1f}, {y=:.1f}, {width=:.1f}, {height=:.1f}, {visible=}")

    for child in node.find_elements(by=By.XPATH, value="*"):
        print_chrome_layout(child, index + 1)


with Tree.from_xml(_get_xml(filepath)) as tree:
    list_nodes(tree)
    tree.compute_layout()
    print_layout(tree)


driver = webdriver.Chrome()
driver.get("file://" + os.getcwd() + "/" + filepath)
driver.implicitly_wait(0.5)
node_expected = driver.find_element(by=By.ID, value="test-root")
print_chrome_layout(node_expected)
