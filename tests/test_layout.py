from hypothesis import given
from hypothesis import strategies as st

from stretchable import Box, Node, Size, reset
from stretchable.style.core import AlignItems, JustifyContent, pct


def assert_attrs(
    actual: object,
    identifier: str = None,
    **kwargs,
    # x: float = None,
    # y: float = None,
    # width: float = None,
    # height: float = None,
) -> None:
    desc = f"{identifier}: " if identifier else ""
    for attr, value in kwargs.items():
        assert hasattr(actual, attr), f"{desc}Attribute {attr} not present"
        v = getattr(actual, attr)
        assert v == value, f"{desc}Expected {attr}={value}, got {v}"


@given(
    st.integers(600, 1200),
    st.integers(600, 1200),
    st.integers(0, 50),
)
def test_padding(width: int, height: int, padding: int):
    reset()

    node = Node(
        size=Size(width, height),
        padding=padding,
    )
    child = Node(
        size=Size(100 * pct, 100 * pct),
        padding=0.5 * padding,
    )
    node.add(child)

    node.compute_layout()

    layout = child.get_layout(Box.CONTENT)
    assert layout.x == 1.5 * padding
    assert layout.y == 1.5 * padding
    assert layout.width == width - 3 * padding
    assert layout.height == height - 3 * padding


@given(
    st.integers(600, 1200),
    st.integers(600, 1200),
    st.integers(0, 25),
    st.integers(0, 25),
    st.integers(0, 25),
)
def test_multiple_levels(
    width: int, height: int, margin: int, border: int, padding: int
):
    reset()

    main = Node(
        size=Size(width, height),
        justify_content=JustifyContent.FLEX_END,
        align_items=AlignItems.FLEX_START,
        padding=padding,
        border=border,
        margin=margin,
    )
    child1 = Node(
        size=Size(50 * pct, 50 * pct),
        justify_content=JustifyContent.FLEX_START,
        align_items=AlignItems.FLEX_END,
        padding=padding,
        border=border,
        margin=margin,
    )
    main.add(child1)
    child2 = Node(
        size=Size(50 * pct, 50 * pct),
        padding=padding,
        border=border,
        margin=margin,
    )
    child1.add(child2)

    main.compute_layout()

    # Check child1 border box position
    layout = child1.get_layout(relative=False)
    w_exp = 0.5 * (width - 2 * (border + padding))
    x_exp = width - border - padding - w_exp - margin
    y_exp = margin + border + padding
    h_exp = 0.5 * (height - 2 * (border + padding))
    assert_attrs(
        layout,
        "child1 border box",
        x=x_exp,
        y=y_exp,
        width=w_exp,
        height=h_exp,
    )

    # Check child1 content box position
    layout = child1.get_layout(Box.CONTENT, relative=False)
    assert_attrs(
        layout,
        "child1 content box",
        x=x_exp + border + padding,
        y=y_exp + border + padding,
        width=w_exp - 2 * (border + padding),
        height=h_exp - 2 * (border + padding),
    )

    # Check child2 border box position
    layout_parent = child1.get_layout(Box.CONTENT, relative=False)
    layout = child2.get_layout(relative=False)
    w_exp = 0.5 * layout_parent.width
    h_exp = 0.5 * layout_parent.height
    x_exp = layout_parent.x + margin
    y_exp = layout_parent.y + layout_parent.height - h_exp - margin
    assert_attrs(
        layout,
        "child2 border box",
        x=x_exp,
        y=y_exp,
        width=w_exp,
        height=h_exp,
    )
