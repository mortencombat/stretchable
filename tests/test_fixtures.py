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

from stretchable.node import Node, Tree
from stretchable.style.geometry.length import (
    MAX_CONTENT,
    MIN_CONTENT,
    LengthAvailableSpace,
    Scale,
)
from stretchable.style.geometry.size import SizeAvailableSpace, SizePoints

logger = logging.getLogger("stretchable")
logger.setLevel(logging.DEBUG)

logger = logging.getLogger("stretchable.tests")
logger.setLevel(logging.DEBUG)
logFormatter = logging.Formatter("%(levelname)s:%(name)s:%(message)s")
fileHandler = logging.FileHandler("debug.log")
fileHandler.setFormatter(logFormatter)
logger.addHandler(fileHandler)


H_WIDTH: float = 10.0
H_HEIGHT: float = 10.0
ZERO_WIDTH_SPACE: str = "\u200b"
XML_REPLACE = (("&ZeroWidthSpace;", ZERO_WIDTH_SPACE),)


def get_fixtures() -> list[Path]:
    fixtures = []
    folders = ("tests/fixtures/taffy/*.html",)
    files = (
        # "tests/fixtures/taffy/absolute_aspect_ratio_fill_max_height.html",
    )
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
    return sorted(fixtures)


@pytest.fixture(scope="module")
def driver():
    return webdriver.Chrome()


@pytest.mark.parametrize(
    "filepath",
    get_fixtures(),
)
def test_html_fixtures(driver: webdriver.Chrome, filepath: Path):
    # Read html file, extract content between <body> and </body> and convert <div> to <node>
    logger.debug("Fixture: %s", filepath.stem)

    xml = get_xml(filepath)

    # Use Node.from_xml() to turn into node instances and compute layout with stretchable.
    with Tree.from_xml(xml, apply_node_measure) as tree:
        logger.debug("Set rounding_enabled = False")
        tree.rounding_enabled = False
        logger.debug("Invoking compute_layout...")
        tree.compute_layout()
        logger.debug("compute_layout finished.")

        # Render html with Chrome
        driver.get("file://" + str(filepath))
        driver.implicitly_wait(0.5)
        node_expected = driver.find_element(by=By.ID, value="test-root")

        # Compare rect of Chrome render with stretchable computed layout.
        assert_node_layout(tree, node_expected, filepath.stem)
        logger.debug("assert_node_layout finished.")


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
        assert_node_layout(child_actual, child_expected, f"{fixture}/{i}")


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

    if math.isnan(inline_size):
        if inline_space == MIN_CONTENT:
            inline_size = min_line_length * H_WIDTH
        elif inline_space == MAX_CONTENT:
            inline_size = max_line_length * H_WIDTH
        else:
            inline_size = max(
                min(inline_space.value, max_line_length * H_WIDTH),
                min_line_length * H_WIDTH,
            )

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
    ic(
        aspect_ratio,
        width,
        height,
        available_space.width.value,
        available_space.height.value,
    )
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


"""

22230 segmentation fault, last occurred on:
[MainThread  ] [DEBUG]  Fixture: intrinsic_sizing_cross_size_column
[MainThread  ] [DEBUG]  Applying node_measure...
[MainThread  ] [DEBUG]  -> Done.
[MainThread  ] [DEBUG]  Set rounding_enabled = False
[MainThread  ] [DEBUG]  Invoking compute_layout...

29458 segmentation fault, occured on:
DEBUG:stretchable.tests:Invoking compute_layout...
DEBUG:stretchable.tests:Measure 'HH​HH​HH​HH​HH​HH​HH​HH​HH​HH​HH'
DEBUG:stretchable.tests:Measured size Size(width=100.00 pt, height=30.00 pt)
DEBUG:stretchable.tests:Measure 'HH​HH​HH​HH​HH​HH​HH​HH​HH​HH​HH'

36409 abort
DEBUG:stretchable.tests:Fixture: aspect_ratio_flex_row_fill_max_height
DEBUG:stretchable.tests:Set node.measure for 'HH​HH​HH​HH​HH​HH​HH​HH​HH​HH​HH'.
DEBUG:stretchable.tests:Set rounding_enabled = False
DEBUG:stretchable.tests:Invoking compute_layout...
DEBUG:stretchable.tests:Measure 'HH​HH​HH​HH​HH​HH​HH​HH​HH​HH​HH', avail space width 100.00 pt height 20.00 pt
DEBUG:stretchable.tests:Measured size Size(width=40.00 pt, height=20.00 pt)
DEBUG:stretchable.tests:Measure 'HH​HH​HH​HH​HH​HH​HH​HH​HH​HH​HH', avail space width min-content height 20.00 pt

37816 abort
DEBUG:stretchable.tests:Fixture: aspect_ratio_flex_row_fill_max_height
DEBUG:stretchable.tests:Set node.measure for 'HH​HH​HH​HH​HH​HH​HH​HH​HH​HH​HH'.
DEBUG:stretchable.tests:Set rounding_enabled = False
DEBUG:stretchable.tests:Invoking compute_layout...
DEBUG:stretchable.tests:measure_standard_text('HH​HH​HH​HH​HH​HH​HH​HH​HH​HH​HH', available_space = 100.00 pt x 20.00 pt, known_dims = nan x nan, aspect_ratio = 2.0, writing_mode = 0
DEBUG:stretchable.tests:measure_standard_text(...) -> Size(width=40.00 pt, height=20.00 pt)
DEBUG:stretchable.tests:measure_standard_text('HH​HH​HH​HH​HH​HH​HH​HH​HH​HH​HH', available_space = min-content x 20.00 pt, known_dims = nan x nan, aspect_ratio = 2.0, writing_mode = 0


"""
