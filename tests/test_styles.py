from stretchable.style.core import to_css_prop_name


def test_prop_names():
    assert to_css_prop_name("aspect_ratio") == "aspect-ratio"
    assert to_css_prop_name("aspectRatio") == "aspect-ratio"
    assert to_css_prop_name("AspectRatio") == "aspect-ratio"
    assert to_css_prop_name("aspect-ratio") == "aspect-ratio"
    assert to_css_prop_name(" aspect-ratio ") == "aspect-ratio"


def test_token_strip():
    # TODO: Implement test
    pass


def test_token_split():
    # TODO: Implement test
    pass
