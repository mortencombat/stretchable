from stretchable import Node
from stretchable.style import (
    GridTrackSize,
    GridTrackSizingRepeat,
    GridTrackSizingSingle,
)
from stretchable.style.geometry.length import LengthMaxTrackSize, LengthMinTrackSize

"""
TODO:
- Implement various instancing helper methods on GridTrackSize, LengthMinTrackSize, LengthMaxTrackSize
- Initial testing
- Add support for grid fixtures:
        from_inline support for grid properties
        include grid fixtures in test_fixtures
"""

node = Node(
    grid_template_columns=[
        GridTrackSizingSingle(),
    ],
    grid_auto_columns=[
        GridTrackSize(),
    ],
)
node.compute_layout()
