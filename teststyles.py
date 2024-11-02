from stretchable.style import Style
from stretchable.style.parser import adapters, simple_dimension_converter

adapters.dimension_converter = lambda prop, token, context: simple_dimension_converter(
    prop, token, context, unit_scales={"px": 1, "pt": 17.5}, require_unit=True
)

str1 = "width: 50%; aspect-ratio: 1.5"
style1 = Style.from_str(str1)

str2 = dict(width="50%", aspect_ratio=1.5)
style2 = Style.from_dict(str2)

str3 = "margin: 10px; margin-left: 5pt; margin-right: 5pt; left: 25px; align-content: center; overflow: hidden; overflow-x: scroll"
style3 = Style.from_str(str3)
print(style3.margin)
print(style3.align_content)
print(style3.overflow_x, style3.overflow_y)
print(style3.inset)

str4 = "margin: 5px 10px 5%"
style4 = Style.from_str(str4)
