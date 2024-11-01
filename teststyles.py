from stretchable.style import Style

str1 = "width: 50%; aspect-ratio: 1.5"
style1 = Style.from_str(str1)

str2 = dict(width="50%", aspect_ratio=1.5)
style2 = Style.from_dict(str2)

str3 = "margin: 10px; margin-left: 5px; margin-right: 5px; left: 25px; align-content: center; overflow: hidden; overflow-x: scroll"
style3 = Style.from_str(str3)
print(style3.margin)
print(style3.align_content)
print(style3.overflow_x, style3.overflow_y)
print(style3.inset)

str4 = "margin: 5px 10px 5%"
style4 = Style.from_str(str4)
