import drawsvg as draw
from lib.elements import (
    F_CLEF,
    SVG_ACC_OFFSET,
    EMPTY_NOTEHEAD,
    SVG_ACC_MAP,
)
from lib.music import ACCIDENTALS
from lib.utils import debug_x_line

if __name__ == "__main__":
    LEN = 80
    img = draw.Drawing(LEN, 20)

    C_LINE = 5
    F_LINE = 5 + 4

    for i in range(5):
        y = C_LINE + (i + 1) * 2
        img.append(draw.Line(0, y, LEN, y, stroke_width=0.25, stroke="black"))
    img.append(draw.Use(F_CLEF, 3, F_LINE))

    dist = 10

    for i, acc in enumerate(ACCIDENTALS):
        x = dist * i + 20
        img.append(debug_x_line(x, 0, 20))
        img.append(draw.Use(EMPTY_NOTEHEAD, x, F_LINE))
        img.append(draw.Use(SVG_ACC_MAP[acc], x - SVG_ACC_OFFSET[acc], F_LINE))
    img.save_svg("test.svg")
