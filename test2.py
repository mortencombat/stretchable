from stretchable.style import Style
from stretchable.style.geometry.length import PT
from stretchable.style.geometry.rect import RectPointsPercentAuto

# rect = RectPointsPercentAuto(bottom=10 * PT)
# print(rect)

inline = "position: absolute; width: 60px; height: 40px;bottom:10px;"
style = Style.from_inline(inline)
print(style.inset)
