from pathlib import Path

from stretchable.node import Node
from tests.test_fixtures import get_xml

filepath = Path(
    "/Users/kenneth/Code/Personal/Python/stretchable/tests/fixtures/taffy/rounding_fractial_input_6.html"
)

xml = get_xml(filepath)

# double clear could be caused by an exception in Python?

node = Node.from_xml(xml)
node.compute_layout(use_rounding=False)



# # Render html with Chrome
# driver.get("file://" + str(filepath))
# driver.implicitly_wait(0.5)
# node_expected = driver.find_element(by=By.ID, value="test-root")

# # Compare rect of Chrome render with stretchable computed layout.
# assert_node_layout(node, node_expected, filepath.stem)
# logger.debug("assert_node_layout finished.")
