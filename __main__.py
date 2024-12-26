from typing import Any
import drawsvg as draw
from music import Instrument, Pitch
from elements import ACC_OFFSET, EMPTY_NOTEHEAD, FULL_NOTEHEAD, LF_CLEF, F_CLEF, SVG_ACCIDENTAL_MAP, UG_CLEF, G_CLEF, CLEF_WIDTH, translate
from utils import length, sub, add, mult

TEXT_STYLING: dict[str, Any] = {
    "font": "Cochin",
}

FORMAT = (2*3508, 2480/2)  # 2 times A4 landscape
MARGIN = 100
MIN_X = MARGIN
MAX_X = FORMAT[0] - MARGIN

STAFF_LINE_SPACING = 17
CLEF_OFFSET = STAFF_LINE_SPACING / 17 * 10
STAFF_STROKE_WIDTH = STAFF_LINE_SPACING/2 * 0.22
SECONDARY_STROKE_WIDTH = STAFF_LINE_SPACING/2 * 0.36


def generate_staff(instruments: list[Instrument]) -> draw.Drawing:
    lowest_full = -10
    highest_full = 10
    img = draw.Drawing(*FORMAT)
    img.append(draw.Rectangle(0, 0, *FORMAT, fill="white"))
    min_spos = min(
        map(lambda inst: inst.min_sounding_pitch(), instruments)
    ).to_staff_position()
    min_spos = min(-10, min_spos)
    max_spos = max(
        map(lambda inst: inst.max_sounding_pitch(), instruments)
    ).to_staff_position()
    max_spos = max(10, max_spos)

    display_lower_f = False
    if min_spos < -10 - 14 + 4:
        display_lower_f = True
        lowest_full = -14 - 10
        min_spos = min(min_spos, -10 - 14)

    display_upper_g = False
    if min_spos < 10 + 14 - 4:
        display_upper_g = True
        highest_full = 14 + 10
        max_spos = max(max_spos, 10 + 14)

    center_spos = (min_spos + max_spos) / 2

    middle_c_line = FORMAT[1] / 2 + STAFF_LINE_SPACING / 2 * center_spos

    staff_lines = draw.Group()

    for i in range(min_spos, max_spos + 1):
        if i % 2 == 1:
            continue
        height = middle_c_line - STAFF_LINE_SPACING / 2 * i
        stroke_width = STAFF_STROKE_WIDTH
        color = "black"
        if i > 10 or i < -10 or i == 0:
            stroke_width = STAFF_STROKE_WIDTH/2
            color = "#aaaaaa"

        if display_upper_g and 2 + 14 <= i <= 10 + 14:
            stroke_width = STAFF_STROKE_WIDTH
            color = "black"
        if display_lower_f and -2 - 14 >= i >= -10 - 14:
            stroke_width = STAFF_STROKE_WIDTH
            color = "black"

        staff_lines.append(
            draw.Line(
                MIN_X,
                height,
                MAX_X,
                height,
                stroke=color,
                stroke_width=stroke_width,
            )
        )
    img.append(draw.Text("Polyband Ranges", x=FORMAT[0]/2, y=MARGIN, font_size=70, **TEXT_STYLING, anchor="middle" ))

    img.append(staff_lines)
    img.append(
        draw.Group(
            children=[UG_CLEF],
            transform=f"translate({CLEF_OFFSET + MARGIN} {middle_c_line-9*STAFF_LINE_SPACING}) scale({STAFF_LINE_SPACING/2})",
        )
    )
    img.append(
        draw.Group(
            children=[G_CLEF],
            transform=f"translate({CLEF_OFFSET + MARGIN} {middle_c_line-2*STAFF_LINE_SPACING}) scale({STAFF_LINE_SPACING/2})",
        )
    )
    img.append(
        draw.Group(
            children=[F_CLEF],
            transform=f"translate({CLEF_OFFSET + MARGIN} {middle_c_line+2*STAFF_LINE_SPACING}) scale({STAFF_LINE_SPACING/2})",
        )
    )
    img.append(
        draw.Group(
            children=[LF_CLEF],
            transform=f"translate({CLEF_OFFSET + MARGIN} {middle_c_line+9*STAFF_LINE_SPACING}) scale({STAFF_LINE_SPACING/2})",
        )
    )

    x_offset = CLEF_OFFSET + CLEF_WIDTH * STAFF_LINE_SPACING / 2
    instr_width = (FORMAT[0] - 2 * MARGIN - x_offset) / len(instruments)
    for i, instr in enumerate(instruments):
        x = MARGIN + x_offset + i * instr_width
        if i != len(instruments) - 1:
            img.append(
                draw.Line(
                    x + instr_width,
                    middle_c_line - STAFF_LINE_SPACING / 2 * highest_full,
                    x + instr_width,
                    middle_c_line - STAFF_LINE_SPACING / 2 * lowest_full,
                    stroke_width=SECONDARY_STROKE_WIDTH,
                    stroke="black",
                )
            )
        else:
            img.append(
                draw.Line(
                    x + instr_width - 3.5 * SECONDARY_STROKE_WIDTH,
                    middle_c_line - STAFF_LINE_SPACING / 2 * highest_full,
                    x + instr_width - 3.5 * SECONDARY_STROKE_WIDTH,
                    middle_c_line - STAFF_LINE_SPACING / 2 * lowest_full,
                    stroke_width=SECONDARY_STROKE_WIDTH,
                    stroke="black",
                )
            )
            img.append(
                draw.Line(
                    x + instr_width,
                    middle_c_line
                    - STAFF_LINE_SPACING / 2 * highest_full
                    - STAFF_STROKE_WIDTH / 2,
                    x + instr_width,
                    middle_c_line
                    - STAFF_LINE_SPACING / 2 * lowest_full
                    + STAFF_STROKE_WIDTH / 2,
                    stroke_width=SECONDARY_STROKE_WIDTH * 3,
                    stroke="black",
                )
            )
        instrument = draw.Group(
            [instr_graph(instr, instr_width / (STAFF_LINE_SPACING / 2), -min_spos)],
            transform=f"translate({x} {middle_c_line}) scale({STAFF_LINE_SPACING/2})",
        )
        img.append(instrument)
    return img


INST_MARGIN = 5
MAIN_FONT_SIZE = 3
OVERLAP_OFFSET = 2.7837096774/2
SMALL_STROKE_WIDTH = 0.2


def instr_graph(instr: Instrument, width: float, max_y: float) -> draw.Group:
    """
    This function returns a svg group with all information between x=0 and x=width including margins
    Pitch C4 (middle C) is at y=0 and D4 at y=-1
    """
    ranges = instr.get_sounding_pitch_ranges()
    pitches: list[tuple[Pitch, bool]] = []
    lines: list[bool] = []  # [i] == True -> line from pitches[i] to [i+1]
    for i in range(len(ranges)):
        # start of range
        is_prefred = False
        if i!=0 and ranges[i-1].preferred:
            is_prefred = True
        if ranges[i].preferred:
            is_prefred=True
        pitches.append((ranges[i].start, is_prefred))

        # end of range
        is_prefred = False
        if (ranges[i].end.to_staff_position() - ranges[i].start.to_staff_position()) > 3:
            lines.append(True)
        else:
            lines.append(False)
        if i != len(ranges) - 1 and ranges[i].end == ranges[i + 1].start:
            continue
        if ranges[i].preferred:
            is_prefred = True
        if i != len(ranges) - 1 and ranges[i+1].preferred:
            is_prefred = True
        pitches.append((ranges[i].end, is_prefred))
        if i != len(ranges) - 1:
            lines.append(False)


    to_close = []
    for i in range(len(pitches) - 1):
        to_close.append(
            (pitches[i + 1][0].to_staff_position() - pitches[i][0].to_staff_position()) < 2
        )

    SAME_POS_MULTIPLIER = 1.8
    note_offsets = [0.0] * len(pitches)
    current_note_offset = 1
    for i, b in enumerate(to_close):
        if b:
            note_offsets[i] = current_note_offset
            current_note_offset *= -1
            note_offsets[i + 1] = current_note_offset
            if pitches[i][0].to_staff_position() == pitches[i+1][0].to_staff_position():
                note_offsets[i] *= SAME_POS_MULTIPLIER
                note_offsets[i+1] *= SAME_POS_MULTIPLIER
        else:
            current_note_offset = 1

    notes = draw.Group()

    note_position = width - INST_MARGIN
    for (pitch, prefered), offset in zip(pitches, note_offsets):
        if prefered:
            notes.append(translate(FULL_NOTEHEAD,note_position+offset*OVERLAP_OFFSET, -pitch.to_staff_position()))
        else:
            notes.append(translate(EMPTY_NOTEHEAD,note_position+offset*OVERLAP_OFFSET, -pitch.to_staff_position()))
        notes.append(translate(SVG_ACCIDENTAL_MAP[pitch.accidental], note_position+offset*OVERLAP_OFFSET - ACC_OFFSET, -pitch.to_staff_position()))



    range_lines = draw.Group()
    for i, line in enumerate(lines):
        if line:
            start = (note_position + note_offsets[i] * OVERLAP_OFFSET,
                    -pitches[i][0].to_staff_position())
            end = (note_position + note_offsets[i + 1] * OVERLAP_OFFSET,
                    -pitches[i + 1][0].to_staff_position())
            diff = sub(end, start)
            l = length(diff)
            OFFSET_LEN = 1.5
            range_lines.append(
                draw.Line(
                    *add(start, mult(OFFSET_LEN/l, diff)),
                    *add(end, mult(-OFFSET_LEN/l, diff)),
                    stroke_width=SMALL_STROKE_WIDTH,
                    stroke="black",
                )
            )

    group = draw.Group(children = [range_lines, notes])

    group.append(
        draw.Group(
            children=[
                draw.Text(
                    instr.name,
                    x=0,
                    y=0,
                    font_size=MAIN_FONT_SIZE,
                    text_anchor="end",
                    **TEXT_STYLING,
                )
            ],
            transform=f"translate({note_position} {max_y+3}) rotate(-45)",
        )
    )
    return group


def from_names(names: list[str]) -> draw.Drawing:
    return generate_staff([Instrument.from_file(f"insts/{name}.txt") for name in names])



def grafics_test():
    img = from_names(
        ["mezzosoprano", "fl", "cl", "as", "ts", "bs", "tp", "tb", "btb", "pn", "git", "b"]
    )
    img.save_svg("out.svg")


def main():
    grafics_test()


if __name__ == "__main__":
    main()
