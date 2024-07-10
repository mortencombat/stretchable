import glob
import logging
import math
import os
from enum import IntEnum
from pathlib import Path
from xml.etree import ElementTree

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from stretchable.node import Box, Edge, Node
from stretchable.style.geometry.length import LengthAvailableSpace, Scale
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
USE_ROUNDING: bool = False

"""
DEBUGGING NOTES:

Date        Failed      Passes      Remarks
2023.11.05  41          406         Taffy tests only
            45          643         Taffy+Stretch tests
            14          674         Added support for 'gap' in Style.from_inline(...)
            11          674         Fixed `measure_standard_text` function
            7           677         Fixed error in bevy_issue_8017*.html,
                                    border_center_child.html and
                                    percentage_sizes_should_not_prevent_flex_shrinking.html fixtures
            3           678         Removed 4 duplicate fixtures (which were all failing)
            1           683         The last failing test is related to is_visible. Seems more like a Selenium/Chrome inconsistency.
"""


def get_fixtures(max_count: int = None) -> dict[str, list]:
    fixtures = []
    folders = [
        # "tests/fixtures/block/*.html",
        "tests/fixtures/**/*.html",
    ]
    files = [
        # "tests/fixtures/flex/margin_auto_right.html",
        # "tests/fixtures/taffy/undefined_height_with_min_max.html",
    ]
    cwd = os.getcwd()
    for folder in folders:
        for f in glob.glob(cwd + "/" + folder):
            filepath = Path(f)
            if filepath.stem.startswith("x"):
                continue
            # if filepath.stem.startswith("grid"):
            #     continue
            fixtures.append(filepath)
    for file in files:
        fixtures.append(Path(cwd + "/" + file))
    if max_count and len(fixtures) > max_count:
        fixtures = fixtures[:max_count]
    fixtures = sorted(fixtures)
    return dict(argvalues=fixtures, ids=[Path(fixt).stem for fixt in fixtures])


@pytest.fixture(scope="module")
def driver():
    options = Options()
    for option in (
        "--headless",
        "--disable-gpu",
        "--window-size=1920,1200",
        "--ignore-certificate-errors",
        "--disable-extensions",
        "--no-sandbox",
        "--disable-dev-shm-usage",
    ):
        options.add_argument(option)
    driver = webdriver.Chrome(options=options)
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

    # Use Node.from_xml() to turn into node instances and compute layout with stretchable.
    req_measure = requires_measure(ElementTree.fromstring(xml))
    node = Node.from_xml(xml, apply_node_measure) if req_measure else Node.from_xml(xml)
    node.compute_layout(use_rounding=USE_ROUNDING)

    # Render html with Chrome
    driver.get("file://" + str(filepath))
    driver.implicitly_wait(0.5)
    node_expected = driver.find_element(by=By.ID, value="test-root")

    # Compare rect of Chrome render with stretchable computed layout.
    assert_node_layout(
        node,
        node_expected,
        filepath.stem,
        num_decimals=0 if USE_ROUNDING else 1,
    )


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


def get_css_values(node: WebElement, prop: str) -> tuple[float, float, float, float]:
    """Returns a tuple of 4 flots corresponding to the widths of either margin, border or padding CSS properties."""
    values = []
    for edge in ("top", "right", "bottom", "left"):
        propname = f"{prop}-{edge}"
        if prop == "border":
            propname += "-width"
        values.append(float(node.value_of_css_property(propname).strip().rstrip("px")))
    return values


def apply_css_values(node: WebElement, layout: Box, prop: str, k: float) -> Box:
    """Applies CSS margin/border/padding to `layout` with a specified factor `k`."""
    values = []
    values = get_css_values(node, prop)
    return Box(
        layout.x + k * values[3],
        layout.y + k * values[0],
        layout.width - k * (values[1] + values[3]),
        layout.height - k * (values[0] + values[2]),
    )


def get_layout_expected(node: WebElement, box: Edge) -> Box:
    layout = Box(**node.rect)
    if box == Edge.MARGIN:
        # Expand by margin
        layout = apply_css_values(node, layout, "margin", -1)
    if box == Edge.PADDING or box == Edge.CONTENT:
        # Contract by border
        layout = apply_css_values(node, layout, "border", 1)
    if box == Edge.CONTENT:
        # Contract by padding
        layout = apply_css_values(node, layout, "padding", 1)
    return layout


def assert_node_layout(
    node_actual: Node,
    node_expected: WebElement,
    fixture: str,
    *,
    num_decimals: int = 1,
) -> None:
    visible = node_expected.is_displayed()
    assert (
        visible == node_actual.is_visible
    ), f"[{fixture}] Expected {visible=}, got {node_actual.is_visible}"
    if visible:
        for box in Edge:
            if box == Edge.MARGIN:  # and node_actual.has_auto_margin:
                # Taffy does not expose calculated/applied margins, and
                # stretchable does not offer to calculate the margin box for
                # 'auto' margins.
                continue
            rect_expected = get_layout_expected(node_expected, box)
            rect_actual = node_actual.get_box(edge=box, relative=False)

            # Assert position of node
            for param in ("x", "y", "width", "height"):
                v_act = round(
                    getattr(rect_actual, param),
                    num_decimals if (param == "x" or param == "y") else 0,
                )
                v_exp = round(getattr(rect_expected, param), num_decimals)

                assert (
                    v_act == v_exp
                ), f"[{fixture}/{box._name_}] Expected {param}={v_exp:.4f}, got {v_act:.4f}"

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
        assert_node_layout(
            child_actual, child_expected, f"{fixture}/{i}", num_decimals=num_decimals
        )


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
    node.measure = lambda _self, known_dims, available_space: measure_standard_text(
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
        if inline_space.scale == Scale.MIN_CONTENT:
            inline_size = min_line_length * H_WIDTH
        elif inline_space.scale == Scale.MAX_CONTENT:
            inline_size = max_line_length * H_WIDTH
        elif math.isnan(inline_space.value):
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
