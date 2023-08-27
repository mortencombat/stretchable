from demos.example import print_layout
from stretchable import Node, reset
from tests.test_fixtures import _get_xml

filepath = "tests/fixtures/justify_content_min_width_with_padding_child_width_greater_than_parent.html"

reset()
xml = _get_xml(filepath)
print(xml)
node = Node.from_xml(xml)
node.compute_layout()
print_layout(node)
