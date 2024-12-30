from typing import Any

import drawsvg as draw

from music import *
from elements import *
from utils import length, sub, add, mult
INST_MARGIN = 4
INSTR_TITLE_SIZE = 4
SMALL_STROKE_WIDTH = 0.2


def calc_note_heads(ranges: list[PartialRange]) -> tuple[list[Pitch], list[bool]]:
    pitches = []
    preferred = []
    for i in range(len(ranges)):
        # start of range
        full = False
        if i != 0 and ranges[i - 1].preferred:
            full = True
        if ranges[i].preferred:
            full = True
        pitches.append(ranges[i].start)
        preferred.append(full)

        # end of range
        full = False
        if i != len(ranges) - 1 and ranges[i].end == ranges[i + 1].start:
            continue
        if ranges[i].preferred:
            full = True
        if i != len(ranges) - 1 and ranges[i + 1].preferred:
            full = True
        pitches.append(ranges[i].end)
        preferred.append(full)
    return pitches, preferred

def find_accidentals(pitches: list[Pitch]) -> list[str]:
    accidentals = []
    for i in range(len(pitches)):
        if i!=0 and pitches[i].to_staff_position() == pitches[i-1].to_staff_position():
            if pitches[i].get_accidental() != pitches[i-1].get_accidental():
                accidentals.append(pitches[i].get_accidental())
            else:
                accidentals.append("")
        else:
            acc = "" if pitches[i].get_accidental() == "n" else pitches[i].get_accidental()
            accidentals.append(acc)
    return accidentals

def calc_positions(pitches: list[Pitch], accidentals: list[str] , x_0: float, x_max: float) -> list[float]:
    widths = [ACC_MARGIN + SVG_ACC_OFFSET[acc] + NOTE_WIDTH/2 for acc in accidentals]
    staff_distances = [pitches[i].to_staff_position() - pitches[i-1].to_staff_position() for i in range(1, len(pitches))]

    tot_staff_dist = sum(staff_distances)
    available_width = x_max - x_0 - sum(widths)

    between_dist = list(map(lambda x: x/tot_staff_dist*available_width, staff_distances))

    positions = []
    current_position = x_0
    for i, width in enumerate(widths):
        positions.append(current_position + SVG_ACC_OFFSET[pitches[i].get_accidental()])

        current_position += width
        if i < len(between_dist):
            current_position += between_dist[i]

    return positions

def draw_notes(pitches:list[Pitch], preferred: list[bool], positions: list[float], accidentals: list[str])-> draw.Group:
    notes = draw.Group()
    for pitch, full, note_head_pos, acc in zip(pitches, preferred, positions, accidentals):
        if full:
            notes.append(
                translate(
                    FULL_NOTEHEAD,
                    note_head_pos,
                    -pitch.to_staff_position(),
                )
            )
        else:
            notes.append(
                translate(
                    EMPTY_NOTEHEAD,
                    note_head_pos,
                    -pitch.to_staff_position(),
                )
            )
        notes.append(
            translate(
                SVG_ACCIDENTAL_MAP[acc],
                note_head_pos - SVG_ACC_OFFSET[acc],
                -pitch.to_staff_position(),
            )
        )
    return notes

def draw_range_lines(pitches: list[Pitch], positions: list[float])-> draw.Group:
    range_lines = draw.Group()
    for i in range(len(pitches) - 1):
        start = (
            positions[i],
            -pitches[i].to_staff_position(),
        )
        end = (
            positions[i + 1],
            -pitches[i + 1].to_staff_position(),
        )
        diff = sub(end, start)
        line_len = length(diff)
        OFFSET_LEN = 2.5
        if line_len - 2 * OFFSET_LEN > 3:
            range_lines.append(
                draw.Line(
                    *add(start, mult(OFFSET_LEN / line_len, diff)),
                    *add(end, mult(-OFFSET_LEN / line_len, diff)),
                    stroke_width=SMALL_STROKE_WIDTH,
                    stroke="black",
                )
            )
    return range_lines

def instr_graph(
    instr: Instrument, y_min: float, y_max: float
) -> draw.Group:
    """
    This function returns a svg group with all information between x=0 and x=width including margins
    Pitch C4 (middle C) is at y=0 and D4 at y=-1
    """
    pitches, preferred = calc_note_heads(instr.get_sounding_pitch_ranges())
    accidentals = find_accidentals(pitches)
    positions = calc_positions(pitches, accidentals, INST_MARGIN, INST_WIDTH - INST_MARGIN)
    group = draw.Group()
    group.append(draw_notes(pitches, preferred, positions, accidentals))
    group.append(draw_range_lines(pitches, positions))

    group.append(
        draw.Text(
            instr.name,
            x=INST_MARGIN,
            y=y_min - TEXT_MARGIN,
            font_size=INSTR_TITLE_SIZE,
            text_anchor="start",
            **TEXT_STYLING,
        )
    )
    return group

TEXT_MARGIN = 3
TEXT_STYLING: dict[str, Any] = {
    "font": "Cochin",
}
SECONDARY_COLOR = "#666666"

# A4 = (3508, 2480)

INST_WIDTH = 60


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
        clefs.append(translate(UG_CLEF, CLEF_OFFSET, -(UG_RANGE[0] + 2)))
    clefs.append(translate(G_CLEF, CLEF_OFFSET, -(G_RANGE[0] + 2)))
    clefs.append(translate(F_CLEF, CLEF_OFFSET, -(F_RANGE[1] - 2)))
    if draw_lf:
        clefs.append(translate(LF_CLEF, CLEF_OFFSET, -(LF_RANGE[1] - 2)))
    return clefs


DOUBLE_BARLINE_WIDTH = 5*BAR_LINE_WIDTH
def draw_d_barline(x: float, min_y_spos: float, max_y_spos: float) -> draw.Group:
    group = draw.Group()
    group.append(
        draw.Line(
            x-BAR_LINE_WIDTH*3/2,
            -min_y_spos,
            x-BAR_LINE_WIDTH*3/2,
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
    instruments: list[Instrument],
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

    groups = []
    groups.append(draw_staff_lines(min_spos, max_spos, 0, total_length, draw_ug, draw_lf))
    groups.append(draw_d_barline(total_length, highest_full, lowest_full))
    groups.append(draw_clefs(draw_ug, draw_lf))

    for i, instr in enumerate(instruments):
        x = CLEF_OFFSET + CLEF_WIDTH + i * INST_WIDTH
        groups.append(
            translate(instr_graph(instr, -max_spos, -min_spos), x, 0,)
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
    y_min = -max_spos - INSTR_TITLE_SIZE - TEXT_MARGIN
    y_max = -min_spos
    height = y_max - y_min

    return draw.Group(children=groups, transform=f"translate(0 {-y_min})"), (total_length, height)

PX_PER_CM = 37.79
LINE_SPACE = 0.25 * PX_PER_CM
MARGIN = 1 * PX_PER_CM
TITLE_FONT_SIZE = 70
TITLE_MARGIN = TITLE_FONT_SIZE


def make_img(title: str, instruments: list[Instrument]) -> draw.Drawing:
    main_group, (width, height) = generate_staff(instruments)

    width = width * LINE_SPACE / 2 + 2 * MARGIN
    height = height * LINE_SPACE / 2 + 2 * MARGIN + TITLE_FONT_SIZE + TITLE_MARGIN

    img = draw.Drawing(width, height)
    img.append(draw.Rectangle(0, 0, width, height, fill="#cccccc"))
    img.append(
        draw.Text(
            title,
            x=width / 2,
            y=MARGIN+TITLE_FONT_SIZE,
            font_size=TITLE_FONT_SIZE,
            **TEXT_STYLING,
            text_anchor="middle",
        )
    )
    img.append(
        draw.Group(
            children=[main_group],
            transform=f"translate({MARGIN},{1 * MARGIN + TITLE_FONT_SIZE + TITLE_MARGIN})scale({LINE_SPACE/2})",
        )
    )
    return img


def from_names(title: str, names: list[str]) -> draw.Drawing:
    return make_img(
        title, [Instrument.from_file(f"insts/{name}.txt") for name in names]
    )


def main():
    img = from_names(
        "Polyband Ranges",
        [
            "mezzosoprano",
            "fl",
            "cl",
            "as",
            "ts",
            "bs",
            "tp",
            "tb",
            "btb",
            "pn",
            "git",
            "b",
        ],
    )
    img.save_svg("out.svg")
    # cairosvg.svg2pdf(url="out.svg", write_to="output.pdf")


if __name__ == "__main__":
    main()
