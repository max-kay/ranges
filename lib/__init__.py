from math import ceil

import drawsvg as draw


from .elements import (
    translated_group,
    STAFF_STROKE_WIDTH,
    LF_CLEF,
    F_CLEF,
    G_CLEF,
    UG_CLEF,
    CLEF_OFFSET,
    BAR_LINE_WIDTH,
    CLEF_WIDTH,
    PX_PER_CM,
    A4,
    FONT_FAMILY,
    TEXT_MARGIN_FACTOR,
)
from .inst_graph import (
    INST_TITLE_MARGIN,
    LINE_HEIGHT,
    INST_WIDTH,
    INST_TITLE_SIZE,
    TEXT_MARGIN,
    Instrument,
    StringedInst,
)
from .consts import (
    LF_RANGE,
    F_RANGE,
    G_RANGE,
    UG_RANGE,
)
from .parser import parse

SECONDARY_COLOR = "#666666"


def calc_lowest_line(min_spos: int) -> tuple[int, bool]:
    """
    calculates the lowest staff line with the bool indicating if the lower F clef should be drawn
    """
    min_spos = min(F_RANGE[0], min_spos)

    draw_lf = False
    if min_spos < LF_RANGE[0] + 4:
        draw_lf = True
        min_spos = min(min_spos, LF_RANGE[0])

    return min_spos, draw_lf


def calc_highest_line(max_spos: int) -> tuple[int, bool]:
    """
    calculates the highest staff line with the bool indicating if the upper G clef should be drawn
    """
    max_spos = max(G_RANGE[1], max_spos)

    draw_ug = False
    if max_spos > UG_RANGE[1] - 4:
        draw_ug = True
        max_spos = max(max_spos, UG_RANGE[1])

    return max_spos, draw_ug


def draw_staff_lines(
    min_spos: int,
    max_spos: int,
    x_min: float,
    x_max: float,
    draw_ug: bool,
    draw_lf: bool,
) -> draw.Group:
    staff_lines = draw.Group()
    for staff_pos in range(min_spos, max_spos + 1):
        if staff_pos % 2 == 1:
            continue
        stroke_width = STAFF_STROKE_WIDTH
        color = "black"
        if staff_pos > G_RANGE[1] or staff_pos < F_RANGE[0] or staff_pos == 0:
            stroke_width = STAFF_STROKE_WIDTH / 2
            color = SECONDARY_COLOR

        if draw_ug and UG_RANGE[0] <= staff_pos <= UG_RANGE[1]:
            stroke_width = STAFF_STROKE_WIDTH
            color = "black"
        if draw_lf and LF_RANGE[0] <= staff_pos <= LF_RANGE[1]:
            stroke_width = STAFF_STROKE_WIDTH
            color = "black"

        staff_lines.append(
            draw.Line(
                x_min,
                -staff_pos,
                x_max,
                -staff_pos,
                stroke=color,
                stroke_width=stroke_width,
            )
        )
    return staff_lines


def draw_clefs(draw_ug: bool, draw_lf: bool) -> draw.Group:
    clefs = draw.Group()
    if draw_ug:
        clefs.append(draw.Use(UG_CLEF, CLEF_OFFSET, -(UG_RANGE[0] + 2)))
    clefs.append(draw.Use(G_CLEF, CLEF_OFFSET, -(G_RANGE[0] + 2)))
    clefs.append(draw.Use(F_CLEF, CLEF_OFFSET, -(F_RANGE[1] - 2)))
    if draw_lf:
        clefs.append(draw.Use(LF_CLEF, CLEF_OFFSET, -(LF_RANGE[1] - 2)))
    return clefs


DOUBLE_BARLINE_WIDTH = 5 * BAR_LINE_WIDTH


def draw_d_barline(x: float, min_y_spos: float, max_y_spos: float) -> draw.Group:
    group = draw.Group()
    group.append(
        draw.Line(
            x - BAR_LINE_WIDTH * 3 / 2,
            -min_y_spos,
            x - BAR_LINE_WIDTH * 3 / 2,
            -max_y_spos,
            stroke_width=BAR_LINE_WIDTH * 3,
            stroke="black",
        )
    )
    group.append(
        draw.Line(
            x - 5 * BAR_LINE_WIDTH,
            -min_y_spos,
            x - 5 * BAR_LINE_WIDTH,
            -max_y_spos,
            stroke_width=BAR_LINE_WIDTH,
            stroke="black",
        )
    )
    return group


def generate_staff(
    instruments: list[Instrument | StringedInst],
) -> tuple[draw.Group, tuple[float, float]]:
    """
    generates everything with C4 at 0 and D4 at -1
    """
    min_spos = min(
        map(lambda inst: inst.min_sounding_pitch().to_staff_position(), instruments)
    )
    min_spos, draw_lf = calc_lowest_line(min_spos)

    max_spos = max(
        map(lambda inst: inst.max_sounding_pitch().to_staff_position(), instruments)
    )
    max_spos, draw_ug = calc_highest_line(max_spos)

    highest_full = G_RANGE[1] if not draw_ug else UG_RANGE[1]
    lowest_full = F_RANGE[0] if not draw_lf else LF_RANGE[0]

    total_length = (
        CLEF_OFFSET + CLEF_WIDTH + len(instruments) * INST_WIDTH + DOUBLE_BARLINE_WIDTH
    )

    groups: list[draw.Group | draw.Line] = []
    groups.append(
        draw_staff_lines(min_spos, max_spos, 0, total_length, draw_ug, draw_lf)
    )
    groups.append(draw_d_barline(total_length, highest_full, lowest_full))
    groups.append(draw_clefs(draw_ug, draw_lf))

    for i, inst in enumerate(instruments):
        x = CLEF_OFFSET + CLEF_WIDTH + i * INST_WIDTH
        groups.append(
            translated_group(
                inst.generate_s_pitch_ranges(-max_spos, -min_spos),
                x,
                0,
            )
        )
        if i < len(instruments) - 1:
            groups.append(
                draw.Line(
                    x + INST_WIDTH,
                    -highest_full,
                    x + INST_WIDTH,
                    -lowest_full,
                    stroke_width=BAR_LINE_WIDTH,
                    stroke="black",
                )
            )
    longest_descr = max(map(lambda x: len(x.ranges), instruments))

    y_min = -max_spos - INST_TITLE_SIZE - INST_TITLE_MARGIN
    y_max = -min_spos + longest_descr * LINE_HEIGHT + TEXT_MARGIN

    height = y_max - y_min

    return draw.Group(children=groups, transform=f"translate(0,{-y_min})"), (
        total_length,
        height,
    )


LINE_SPACE = 0.2 * PX_PER_CM
MARGIN = 1 * PX_PER_CM
TITLE_FONT_SIZE = 50
TITLE_MARGIN = TITLE_FONT_SIZE * TEXT_MARGIN_FACTOR


def make_graph(
    title: str, instruments: list[Instrument | StringedInst]
) -> tuple[draw.Group, tuple[float, float]]:
    content, (width, height) = generate_staff(instruments)

    width = width * LINE_SPACE / 2 + 2 * MARGIN
    height = height * LINE_SPACE / 2 + 2 * MARGIN + TITLE_FONT_SIZE + TITLE_MARGIN

    group = draw.Group()
    # img.append(draw.Rectangle(0, 0, width, height, fill="#cccccc")) # debug
    group.append(
        draw.Text(
            title,
            x=width / 2,
            y=MARGIN,
            font_size=TITLE_FONT_SIZE,
            font_family=FONT_FAMILY,
            text_anchor="middle",
            dominant_baseline="hanging",
            font_weight="bold",
        )
    )
    group.append(
        draw.Group(
            children=[content],
            transform=f"translate({MARGIN},{1 * MARGIN + TITLE_FONT_SIZE + TITLE_MARGIN})scale({LINE_SPACE / 2})",
        )
    )
    return group, (width, height)


def make_svg(title: str, instruments: list[Instrument | StringedInst]) -> draw.Drawing:
    content, (width, height) = make_graph(title, instruments)
    img = draw.Drawing(width, height)
    img.append(content)
    return img


def make_split_svg(
    title: str,
    instruments: list[Instrument | StringedInst],
    /,
    margin: float = PX_PER_CM,
    min_overlap: float = PX_PER_CM,
    format: tuple[float, float] = A4,
) -> list[tuple[draw.Drawing, tuple[int, int]]]:
    content, content_format = make_graph(title, instruments)
    return split_into_tiles(
        content, content_format, format=format, margin=margin, min_overlap=min_overlap
    )


CUT_OFFSET = 8
MARK_STROKE_WIDTH = 1
CUT_LINE = {
    "stroke": "black",
    "stroke_width": MARK_STROKE_WIDTH,
}

OVER_LAP_LINE_WIDTH = 0.3
OVER_LAP_START_LINE = {
    "stroke": "black",
    "stroke_width": OVER_LAP_LINE_WIDTH,
}


def get_cut_mark(margin: float) -> draw.Group:
    group = draw.Group()
    group.append(
        draw.Line(
            -MARK_STROKE_WIDTH / 2,
            -margin,
            -MARK_STROKE_WIDTH / 2,
            -CUT_OFFSET,
            **CUT_LINE,
        )
    )
    group.append(
        draw.Line(
            -margin,
            -MARK_STROKE_WIDTH / 2,
            -CUT_OFFSET,
            -MARK_STROKE_WIDTH / 2,
            **CUT_LINE,
        )
    )
    return group


def calc_tiles(
    content_format: tuple[float, float],
    format: tuple[float, float],
    margin: float,
    overlap: float,
) -> tuple[
    tuple[float, float], tuple[int, int], tuple[float, float], tuple[float, float]
]:
    fill_width_a = format[0] - 2 * margin
    fill_height_a = format[1] - 2 * margin
    x_tiles_a = ceil((content_format[0] - overlap) / (fill_width_a - overlap))
    y_tiles_a = ceil((content_format[1] - overlap) / (fill_height_a - overlap))

    fill_width_b = format[1] - 2 * margin
    fill_height_b = format[0] - 2 * margin
    x_tiles_b = ceil((content_format[0] - overlap) / (fill_width_b - overlap))
    y_tiles_b = ceil((content_format[1] - overlap) / (fill_height_b - overlap))

    if x_tiles_a * y_tiles_a <= x_tiles_b * y_tiles_b:
        fill_width = fill_width_a
        fill_height = fill_height_a
        x_tiles = x_tiles_a
        y_tiles = y_tiles_a
    else:
        format = (format[1], format[0])
        fill_width = fill_width_b
        fill_height = fill_height_b
        x_tiles = x_tiles_b
        y_tiles = y_tiles_b

    x_offset = (
        fill_width * x_tiles - overlap * (x_tiles - 1) - content_format[0]
    ) / 2.0
    y_offset = (
        fill_height * y_tiles - overlap * (y_tiles - 1) - content_format[1]
    ) / 2.0
    return (
        format,
        (x_tiles, y_tiles),
        (fill_width - overlap, fill_height - overlap),
        (x_offset, y_offset),
    )


def split_into_tiles(
    content: draw.Group,
    content_format: tuple[float, float],
    /,
    margin: float = PX_PER_CM,
    min_overlap: float = 2.0 * PX_PER_CM,
    format: tuple[float, float] = A4,
) -> list[tuple[draw.Drawing, tuple[int, int]]]:
    format, (x_tiles, y_tiles), (tile_width, tile_height), (x_offset, y_offset) = (
        calc_tiles(content_format, format, margin, min_overlap)
    )

    cut_mark = get_cut_mark(margin)
    mask = draw.Mask()
    mask.append(
        draw.Rectangle(
            margin,
            margin,
            format[0] - 2 * margin,
            format[1] - 2 * margin,
            fill="white",
        )
    )

    tiles = []
    for x in range(x_tiles):
        for y in range(y_tiles):
            tile = draw.Drawing(*format)
            img_x_min = x * tile_width - x_offset
            img_y_min = y * tile_height - y_offset
            v_x = margin - img_x_min
            v_y = margin - img_y_min

            tile.append(draw.Group(children=[translated_group(content, v_x, v_y)]))

            # cut marks
            tile.append(
                draw.Use(
                    cut_mark,
                    0,
                    0,
                    transform=f"translate({margin},{margin}) rotate(0)",
                )
            )
            tile.append(
                draw.Use(
                    cut_mark,
                    0,
                    0,
                    transform=f"translate({format[0] - margin},{margin}) rotate(90)",
                )
            )
            tile.append(
                draw.Use(
                    cut_mark,
                    0,
                    0,
                    transform=f"translate({format[0] - margin},{format[1] - margin}) rotate(180)",
                )
            )
            tile.append(
                draw.Use(
                    cut_mark,
                    0,
                    0,
                    transform=f"translate({margin},{format[1] - margin}) rotate(-90)",
                )
            )

            # overlap lines
            if x != x_tiles - 1:
                tile.append(
                    draw.Line(
                        margin + tile_width + OVER_LAP_LINE_WIDTH / 2,
                        0,
                        margin + tile_width + OVER_LAP_LINE_WIDTH / 2,
                        format[1],
                        **OVER_LAP_START_LINE,
                    )
                )
            if y != y_tiles - 1:
                tile.append(
                    draw.Line(
                        0,
                        margin + tile_height + OVER_LAP_LINE_WIDTH / 2,
                        format[0],
                        margin + tile_height + OVER_LAP_LINE_WIDTH / 2,
                        **OVER_LAP_START_LINE,
                    )
                )

            tiles.append((tile, (x, y)))

    return tiles


def test_tiles():
    out_format = A4[0] * 5, A4[1] * 7.5

    group = draw.Group()
    p = draw.Path(stroke="black", stroke_width=2, fill="none")
    p.M(150, 150)
    import random

    for _ in range(40):
        p.L(random.random() * out_format[0], random.random() * out_format[1])
    group.append(p)

    test_img = draw.Drawing(*out_format)
    test_img.append(group)
    test_img.save_svg("out/test.svg")

    for tile, (x, y) in split_into_tiles(
        group, out_format, format=A4, min_overlap=50, margin=20
    ):
        tile.save_svg(f"out/test{x}_{y}.svg")


def from_names(names: list[str]) -> list[Instrument | StringedInst]:
    insts = []
    for name in names:
        path = f"{name}.txt"
        name, fields = parse(path)
        if "open strings" in fields:
            insts.append(StringedInst.from_strs(name, fields))
        else:
            insts.append(Instrument.from_strs(name, fields))
    return insts
