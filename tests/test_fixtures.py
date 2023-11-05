import glob
import logging
import math
import os
from enum import IntEnum
from pathlib import Path
from xml.etree import ElementTree

import pytest
from icecream import ic
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from stretchable.node import Node
from stretchable.style.geometry.length import (
    MAX_CONTENT,
    MIN_CONTENT,
    LengthAvailableSpace,
    Scale,
)
from stretchable.style.geometry.size import SizeAvailableSpace, SizePoints

logger = logging.getLogger("stretchable")
logger.setLevel(logging.DEBUG)
logFormatter = logging.Formatter("%(levelname)s:%(name)s:%(message)s")
fileHandler = logging.FileHandler("debug.log")
fileHandler.setFormatter(logFormatter)
logger.addHandler(fileHandler)


H_WIDTH: float = 10.0
H_HEIGHT: float = 10.0
ZERO_WIDTH_SPACE: str = "\u200b"
XML_REPLACE = (("&ZeroWidthSpace;", ZERO_WIDTH_SPACE),)

"""
DEBUGGING NOTES:

Date        Failed      Passes      Remarks
2023.11.05  41          406         Taffy tests only
2023.11.05  45          643         Taffy+Stretch tests
2023.11.05  14          674         Added support for 'gap' in Style.from_inline(...)

"""


def get_fixtures(max_count: int = None) -> dict[str, list]:
    fixtures = []
    folders = [
        "tests/fixtures/**/*.html",
    ]
    files = [
        # "tests/fixtures/taffy/aspect_ratio_flex_row_fill_max_height.html",
    ]
    cwd = os.getcwd()
    for folder in folders:
        for f in glob.glob(cwd + "/" + folder):
            filepath = Path(f)
            if filepath.stem.startswith("x"):
                continue
            if filepath.stem.startswith("grid"):
                continue
            fixtures.append(filepath)
    for file in files:
        fixtures.append(Path(cwd + "/" + file))
    if max_count and len(fixtures) > max_count:
        fixtures = fixtures[:max_count]
    fixtures = sorted(fixtures)
    return dict(argvalues=fixtures, ids=[Path(fixt).stem for fixt in fixtures])


@pytest.fixture(scope="module")
def driver():
    driver = webdriver.Chrome()
    yield driver
    driver.quit()


@pytest.mark.parametrize(
    "filepath",
    **get_fixtures(),
)
def test_html_fixtures(driver: webdriver.Chrome, filepath: Path):
    # Read html file, extract content between <body> and </body> and convert <div> to <node>
    logger.debug("Fixture: %s", filepath.stem)

    xml = get_xml(filepath)

    # TODO: At the moment don't include fixtures that require measure
    req_measure = requires_measure(ElementTree.fromstring(xml))
    # if req_measure:
    #     return

    # Use Node.from_xml() to turn into node instances and compute layout with stretchable.
    node = Node.from_xml(xml, apply_node_measure) if req_measure else Node.from_xml(xml)
    node.compute_layout()

    # Render html with Chrome
    driver.get("file://" + str(filepath))
    driver.implicitly_wait(0.5)
    node_expected = driver.find_element(by=By.ID, value="test-root")

    # Compare rect of Chrome render with stretchable computed layout.
    assert_node_layout(node, node_expected, filepath.stem)


def get_xml(filepath: Path) -> str:
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
    for token, repl in XML_REPLACE:
        xml = xml.replace(token, repl)
    return xml


def assert_node_layout(
    node_actual: Node,
    node_expected: WebElement,
    fixture: str,
) -> None:
    visible = node_expected.is_displayed()
    assert (
        visible == node_actual.is_visible
    ), f"[{fixture}] Expected {visible=}, got {node_actual.is_visible}"
    if visible:
        # Assert position of node
        for param in ("x", "y", "width", "height"):
            rect_actual = node_actual.get_layout(relative=False)
            v_act = round(
                getattr(rect_actual, param), 1 if param == "x" or param == "y" else 0
            )
            v_exp = round(node_expected.rect[param], 1)

            assert (
                v_act == v_exp
            ), f"[{fixture}] Expected {param}={v_exp:.4f}, got {v_act:.4f}"

    # Assert positions of child nodes
    children = node_expected.find_elements(by=By.XPATH, value="*")
    n_actual = len(node_actual)
    n_expected = len(children)
    assert (
        n_actual == n_expected
    ), f"Expected {n_expected} child node(s), got {n_actual}"
    for i, (child_actual, child_expected) in enumerate(zip(node_actual, children)):
        assert (
            child_expected.tag_name == "div"
        ), "Only <div> elements are supported in test fixtures"
        assert_node_layout(child_actual, child_expected, f"{fixture}/{i}")


def requires_measure(element: ElementTree.Element) -> bool:
    if any(requires_measure(child) for child in element):
        return True
    if not element.text or not element.text.strip():
        return False
    return True


def apply_node_measure(node: Node, element: ElementTree.Element) -> Node:
    if not element.text:
        return node

    text = element.text.strip()
    if not text:
        return node

    if "style" in element.attrib:
        style = element.attrib["style"].replace(" ", "").casefold()
        writing_mode = (
            WritingMode.VERTICAL
            if "writing-mode:vertical" in style
            else WritingMode.HORIZONTAL
        )
    else:
        writing_mode = WritingMode.HORIZONTAL
    node.measure = lambda known_dims, available_space: measure_standard_text(
        available_space,
        text,
        writing_mode,
        known_dims,
        node.style.aspect_ratio,
    )

    logger.debug("Set node.measure for '%s'.", text)

    return node


class WritingMode(IntEnum):
    HORIZONTAL = 0
    VERTICAL = 1


def measure_standard_text(
    available_space: SizeAvailableSpace,
    text: str,
    writing_mode: WritingMode,
    known_dimensions: SizePoints = None,
    aspect_ratio: float = None,
) -> SizePoints:
    # If both width and height are known, just return that
    if (
        known_dimensions
        and not math.isnan(known_dimensions.width.value)
        and not math.isnan(known_dimensions.height.value)
    ):
        return known_dimensions

    logger.debug(
        "measure_standard_text('%s', available_space = %s x %s, known_dims = %s x %s, aspect_ratio = %s, writing_mode = %s",
        text,
        available_space.width,
        available_space.height,
        known_dimensions.width if known_dimensions else None,
        known_dimensions.height if known_dimensions else None,
        aspect_ratio,
        writing_mode,
    )

    # Check and process text
    if not text:
        return SizePoints(0)
    if len(text.strip("H" + ZERO_WIDTH_SPACE)) > 0:
        raise Exception("Unsupported characters in text to be measured")
    lines = text.split(ZERO_WIDTH_SPACE)
    if not lines:
        return SizePoints(0)

    # If available space AND aspect ratio is given, reduce available space corresponding to aspect ratio

    # Measure line lengths
    # min_line_length = the max length of any one line (word wrapped at zero width space)
    # max_line_length = the total length of all lines (without word wrapping)
    min_line_length: int = 0
    max_line_length: int = 0
    for line in lines:
        n = len(line)
        if n > min_line_length:
            min_line_length = n
        max_line_length += n

    if writing_mode == WritingMode.VERTICAL:
        inline_space = available_space.height
        inline_size = known_dimensions.height.value
        block_size = known_dimensions.width.value
    else:
        ic(
            available_space.height.scale,
            aspect_ratio,
            available_space.width.value,
            available_space.height.value,
        )
        if (
            available_space.height.scale == Scale.POINTS
            and aspect_ratio
            and available_space.width.value / available_space.height.value
            > aspect_ratio
        ):
            inline_space = LengthAvailableSpace.definite(
                available_space.height.value * aspect_ratio
            )
        else:
            inline_space = available_space.width

        inline_size = known_dimensions.width.value
        block_size = known_dimensions.height.value

    # ic(inline_size)

    if math.isnan(inline_size):
        # ic(inline_space, inline_space.value, min_line_length, max_line_length, H_WIDTH)
        if inline_space == MIN_CONTENT:
            inline_size = min_line_length * H_WIDTH
        elif inline_space == MAX_CONTENT:
            inline_size = max_line_length * H_WIDTH
        elif math.isnan(inline_space.value):
            inline_size = max_line_length * H_WIDTH
        else:
            inline_size = max(
                min(inline_space.value, max_line_length * H_WIDTH),
                min_line_length * H_WIDTH,
            )

    # ic(block_size)

    if math.isnan(block_size):
        inline_line_length = math.floor(inline_size / H_WIDTH)
        line_count = 1
        current_line_length = 0
        for line in lines:
            n = len(line)
            if current_line_length + n > inline_line_length:
                if current_line_length > 0:
                    line_count += 1
                current_line_length = n
            else:
                current_line_length += n
        block_size = line_count * H_HEIGHT

    width, height = (
        (block_size, inline_size)
        if writing_mode == WritingMode.VERTICAL
        else (inline_size, block_size)
    )

    # ic(width, height)

    # Reduce to available_space
    if (
        available_space.height.scale == Scale.POINTS
        and height > available_space.height.value
    ):
        height = available_space.height.value
    if (
        available_space.width.scale == Scale.POINTS
        and width > available_space.width.value
    ):
        width = available_space.width.value

    # NOTE: Not sure this aspect_ratio correction is correct in all cases!
    # ic(
    #     aspect_ratio,
    #     width,
    #     height,
    #     available_space.width.value,
    #     available_space.height.value,
    # )
    if aspect_ratio:
        if (
            available_space.height.scale == Scale.POINTS
            and height > width / aspect_ratio
        ):
            height = width / aspect_ratio
        elif (
            available_space.width.scale == Scale.POINTS
            and width > height * aspect_ratio
        ):
            width = height * aspect_ratio

    size = SizePoints(width, height)
    logger.debug("measure_standard_text(...) -> %s", size)
    return size
