import glob
import os
from pathlib import Path

import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from stretchable.node import Node, Tree

driver = webdriver.Chrome()

unsupported_xml_entities = ("&ZeroWidthSpace;",)


def _get_xml(filepath: Path) -> str:
    """From HTML with <body>...</body> containing only <div> elements, return
    the <div> elements renamed to <node>"""
    with open(filepath, "r") as f:
        in_body = False
        xml = ""
        for line in f.readlines():
            c = line.strip()
            if not c:
                continue
            if c == "</body>":
                break
            if in_body:
                xml += line
            if c == "<body>":
                in_body = True
        xml = xml.replace("<div", "<node").replace("</div>", "</node>")
    for entity in unsupported_xml_entities:
        xml = xml.replace(entity, "")
    return xml


@pytest.mark.parametrize(
    "filepath",
    sorted(glob.glob(os.getcwd() + "/tests/fixtures/stretch/*.html")),
)
def test_html_fixtures(filepath: str):
    # Read html file, extract content between <body> and </body> and convert <div> to <node>
    xml = _get_xml(filepath)

    # Use Node.from_xml() to turn into node instances and compute layout with stretchable.
    with Tree.from_xml(xml) as tree:
        tree.rounding_enabled = False
        tree.compute_layout()

        # Render html with Chrome
        driver.get("file://" + filepath)
        driver.implicitly_wait(0.5)
        node_expected = driver.find_element(by=By.ID, value="test-root")

        # Compare rect of Chrome render with stretchable computed layout.
        name = Path(filepath).stem
        _assert_node_positions(tree, node_expected, name)


def _assert_node_positions(
    node_actual: Node,
    node_expected: WebElement,
    fixture: str,
) -> None:
    visible = node_expected.is_displayed()
    assert (
        visible == node_actual.visible
    ), f"[{fixture}] Expected {visible=}, got {node_actual.visible}"
    if visible:
        # Assert position of node
        for param in ("x", "y", "width", "height"):
            rect_actual = node_actual.get_layout(relative=False)
            v_act = getattr(rect_actual, param)
            v_exp = node_expected.rect[param]
            assert (
                abs(v_act - v_exp) < 0.5  # 0.015
            ), f"[{fixture}] Expected {param}={v_exp:.4f}, got {v_act:.4f}"

    # Assert positions of child nodes
    children = node_expected.find_elements(by=By.XPATH, value="*")
    assert len(node_actual.children) == len(
        children
    ), "Number of child nodes does not match"
    for i, (child_actual, child_expected) in enumerate(
        zip(node_actual.children, children)
    ):
        assert (
            child_expected.tag_name == "div"
        ), "Only <div> elements are supported in test fixtures"
        _assert_node_positions(child_actual, child_expected, f"{fixture}/{i}")
