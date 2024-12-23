import drawsvg as draw
from music import Instrument
from elements import G_CLEF, NOTE_HEAD, CLEF_WIDTH

TEXT_STYLING = {
    "font": "Cochin",
}

CLEF_OFFSET = 10
MARGIN = 100
STAFF_LINE_SPACING = 17
STAFF_STROKE_WIDTH = 1.6
SECONDARY_STROKE_WIDTH = 1.3
FORMAT = (3508, 2480)  # A4
MIN_X = MARGIN
MAX_X = FORMAT[0] - MARGIN


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
        dashes = "none"
        if i > 10 or i < -10 or i == 0:
            dashes = "10 30"

        if display_upper_g and 2 + 14 <= i <= 10 + 14:
            dashes = "none"
        if display_lower_f and -2 - 14 >= i >= -10 - 14:
            dashes = "none"

        staff_lines.append(
            draw.Line(
                MIN_X,
                height,
                MAX_X,
                height,
                stroke="black",
                stroke_width=STAFF_STROKE_WIDTH,
                stroke_dasharray=dashes,
            )
        )

    img.append(staff_lines)
    img.append(
        draw.Group(
            children=[G_CLEF],
            transform=f"translate({CLEF_OFFSET + MARGIN} {middle_c_line-2*STAFF_LINE_SPACING}) scale({STAFF_LINE_SPACING/2})",
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
                    x + instr_width - 4 * SECONDARY_STROKE_WIDTH,
                    middle_c_line - STAFF_LINE_SPACING / 2 * highest_full,
                    x + instr_width - 4 * SECONDARY_STROKE_WIDTH,
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
                    stroke_width=SECONDARY_STROKE_WIDTH * 2,
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
OVERLAP_OFFSET = 0.66

def instr_graph(instr: Instrument, width: float, max_y: float) -> draw.Group:
    """
    This function returns a svg group with all information between x=0 and x=width including margins
    Pitch C4 (middle C) is at y=0 and D4 at y=-1
    """
    group = draw.Group()
    note_position = width - INST_MARGIN
    ranges = instr.get_sounding_pitch_ranges()
    current_offset = 0
    for i in range(len(ranges)):
        group.append(
            draw.Group(
                [NOTE_HEAD],
                transform=f"translate({note_position-current_offset*OVERLAP_OFFSET} {-ranges[i].start.to_staff_position()})",
            )
        )
        if i != len(ranges)-1 and ranges[i].end == ranges[i + 1].start:
            current_offset = 0
            continue
        elif i != len(ranges)-1 and ranges[i].end.to_staff_position()-ranges[i + 1].start.to_staff_position() < 3 :
            current_offset = 1
        else:
            current_offset = 0
        group.append(
            draw.Group(
                [NOTE_HEAD],
                transform=f"translate({note_position+current_offset*OVERLAP_OFFSET} {-ranges[i].end.to_staff_position()})",
            )
        )
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


def parsing_test():
    _trombone = Instrument.from_file("tb.txt")


def grafics_test():
    img = from_names(
        ["mezzosoprano", "fl", "cl", "as", "ts", "bs", "tp", "tb", "btb", "git", "b"]
    )
    img.save_svg("out.svg")


def main():
    grafics_test()


if __name__ == "__main__":
    main()
