import drawsvg as draw

from .music import Interval, Pitch, RelativeRange, AbsoluteRange
from .elements import (
    EMPTY_NOTEHEAD,
    FULL_NOTEHEAD,
    SVG_ACC_MAP,
    SVG_ACC_WIDTH,
    NOTE_WIDTH,
    SVG_ACC_OFFSET,
    ACC_MARGIN,
    FONT_FAMILY,
    TEXT_MARGIN_FACTOR,
)
from .utils import length, sub, add, mult


class StringedInst:
    def __init__(
        self,
        name: str,
        ranges: list[RelativeRange],
        open_strings: list[Pitch],
        transposition: Interval | None = None,
        notes: str | None = None,
    ) -> None:
        self.name = name
        self.ranges = sorted(ranges)
        self.transposition = transposition if transposition else Interval.from_str("1")
        self.notes = notes if notes else ""
        self.open_strings = sorted(open_strings, key=lambda p: p.num_lex_ord())
        for i in range(0, len(self.ranges) - 1):
            assert (
                self.ranges[i].end.num_lex_ord()
                <= self.ranges[i + 1].start.num_lex_ord()
            ), f"{self.name} has invalid ranges"

    def __str__(self):
        transposition = (
            f"{self.transposition}\n"
            if self.transposition != Interval.from_str("1")
            else ""
        )
        open_strings = "Open Strings:" + " ".join(str(n) for n in self.open_strings)
        ranges_str = "Ranges:\n" + "\n".join(str(r) for r in self.ranges)
        notes = "Notes:\n" + self.notes if self.notes else ""
        return f"{self.name}\n{transposition}Open Strings\n{open_strings}{ranges_str}{notes}"

    def min_sounding_pitch(self) -> Pitch:
        return (
            self.open_strings[0]
            .transposed(self.ranges[0].start)
            .transposed(self.transposition)
        )

    def max_sounding_pitch(self) -> Pitch:
        return (
            self.open_strings[-1]
            .transposed(self.ranges[-1].end)
            .transposed(self.transposition)
        )

    @classmethod
    def from_strs(cls, name: str, fields: dict[str, list[str]]):
        if "transposition" in fields:
            if len(fields["transposition"]) != 1:
                raise ValueError
            transposition = Interval.from_str(fields["transposition"][0])
        else:
            transposition = None
        ranges = [RelativeRange.from_str(r) for r in fields["ranges"]]
        open_strings = [Pitch.from_str(p) for p in fields["open strings"]]
        notes = "\n".join(fields["notes"]) if "notes" in fields else None
        return cls(name, ranges, open_strings, transposition, notes)

    def generate_s_pitch_ranges(self, y_min: float, y_max: float) -> draw.Group:
        group = draw.Group()
        reduced_intervals, fills = calc_note_heads_relative(self.ranges)
        string_notes: list[list[Pitch]] = []
        for base_note in self.open_strings:
            string_notes.append(
                [
                    base_note.transposed(i).transposed(self.transposition)
                    for i in reduced_intervals
                ]
            )

        staff_positions = []
        for pitches in string_notes:
            staff_positions.append([pitch.to_staff_position() for pitch in pitches])

        # calculate accidentals needed
        accidentals: list[list[str]] = []
        for string_idx, pitches in enumerate(string_notes):
            inner = []
            for note, pitch in enumerate(pitches):
                if string_idx == 0:
                    inner.append(
                        pitch.get_accidental() if pitch.get_accidental() != "n" else ""
                    )
                else:
                    spos = staff_positions[string_idx][note]
                    last_conflict_idx = None
                    # TODO: resolve conflicts within the same string
                    for i in range(string_idx):
                        for j in range(len(reduced_intervals)):
                            if staff_positions[i][j] == spos:
                                last_conflict_idx = (i, j)
                    if not last_conflict_idx:
                        inner.append(
                            pitch.get_accidental()
                            if pitch.get_accidental() != "n"
                            else ""
                        )
                    else:
                        accidental = pitch.get_accidental()
                        i, j = last_conflict_idx
                        if accidental == "n" and accidentals[i][j] in ["", "n"]:
                            inner.append("")
                        elif accidentals[i][j] == accidental:
                            inner.append("")
                        else:
                            inner.append(accidental)
            accidentals.append(inner)

        layout_widths = []
        for inner in accidentals:
            layout_widths.append(
                max([ACC_MARGIN + SVG_ACC_WIDTH[a] + NOTE_WIDTH for a in inner])
            )
        x_step = (INST_WIDTH - 2 * INST_MARGIN - sum(layout_widths)) / (
            len(self.open_strings) - 1
        )
        center_xs: list[list[float]] = []
        current_position = INST_MARGIN
        for width, accs in zip(layout_widths, accidentals):
            center_xs.append([current_position + SVG_ACC_OFFSET[acc] for acc in accs])
            current_position += width + x_step

        notes = draw.Group()
        group.append(notes)
        group.append(
            draw.Text(
                self.name,
                x=INST_MARGIN,
                y=y_min - INST_TITLE_MARGIN,
                font_size=INST_TITLE_MARGIN,
                text_anchor="start",
                font_family=FONT_FAMILY,
                font_weight="bold",
            )
        )

        for xs, sposs, accs in zip(center_xs, staff_positions, accidentals):
            for x, full, spos, acc in zip(xs, fills, sposs, accs):
                if full:
                    notes.append(
                        draw.Use(
                            FULL_NOTEHEAD,
                            x,
                            -spos,
                        )
                    )
                else:
                    notes.append(
                        draw.Use(
                            EMPTY_NOTEHEAD,
                            x,
                            -spos,
                        )
                    )
                notes.append(
                    draw.Use(
                        SVG_ACC_MAP[acc],
                        x - SVG_ACC_OFFSET[acc],
                        -spos,
                    )
                )

        lines = draw.Group()
        for xs, sposs in zip(center_xs, staff_positions):
            lines.append(
                draw_range_lines([Pitch.from_staff_position(s) for s in sposs], xs)
            )
        group.append(lines)

        description = draw.Group()
        start_x, end_x, text_x = TEXT_SIZE * 1.5, TEXT_SIZE * 4.5, TEXT_SIZE * 7.5
        for i, r in enumerate(reversed(self.ranges)):
            y = y_max + TEXT_MARGIN + i * LINE_HEIGHT
            description.append(
                draw.Text(
                    r.start.display_name(),
                    x=start_x,
                    y=y,
                    font_weight="bold",
                    **TEXT_KWARGS,
                )
            )
            description.append(
                draw.Text(
                    r.end.display_name(),
                    x=end_x,
                    y=y,
                    font_weight="bold",
                    **TEXT_KWARGS,
                )
            )
            font_style = "italic" if not r.preferred else ""
            description.append(
                draw.Text(
                    r.descr,
                    x=text_x,
                    y=y,
                    **TEXT_KWARGS,
                    font_style=font_style,
                )
            )
        group.append(description)
        return group


class Instrument:
    def __init__(
        self,
        name: str,
        ranges: list[AbsoluteRange],
        transposition: Interval | None = None,
        notes: str | None = None,
    ) -> None:
        self.name = name
        self.ranges = sorted(ranges)
        self.transposition = transposition if transposition else Interval.from_str("1")
        self.notes = notes if notes else ""
        for i in range(0, len(self.ranges) - 1):
            assert (
                self.ranges[i].end.num_lex_ord()
                <= self.ranges[i + 1].start.num_lex_ord()
            ), f"{self.name} has invalid ranges"

    def __str__(self):
        transposition = (
            f"{self.transposition}\n"
            if self.transposition != Interval.from_str("1")
            else ""
        )
        ranges_str = "\n".join(str(r) for r in self.ranges)
        notes = "Notes:\n" + self.notes if self.notes else ""
        return f"{self.name}\n{transposition}{ranges_str}{notes}"

    def min_sounding_pitch(self) -> Pitch:
        return self.ranges[0].start.transposed(self.transposition)

    def max_sounding_pitch(self) -> Pitch:
        return self.ranges[-1].end.transposed(self.transposition)

    def get_sounding_pitch_ranges(self) -> list[AbsoluteRange]:
        out = []
        for r in self.ranges:
            out.append(r.transposed(self.transposition))
        return out

    @classmethod
    def from_strs(cls, name: str, fields: dict[str, list[str]]):
        ranges = [AbsoluteRange.from_str(r) for r in fields["ranges"]]

        if "transposition" in fields:
            if len(fields["transposition"]) != 1:
                raise ValueError
            transposition = Interval.from_str(fields["transposition"][0])

        else:
            transposition = None
        notes = "\n".join(fields["notes"]) if "notes" in fields else None
        return cls(name, ranges, transposition, notes)

    def generate_s_pitch_ranges(self, y_min: float, y_max: float) -> draw.Group:
        """
        This function returns a svg group with all information between x=0 and x=INST_WIDTH including margins
        Pitch C4 (middle C) is at y=0 and D4 at y=-1
        """
        pitches, preferred = calc_note_heads(self.get_sounding_pitch_ranges())
        accidentals = find_accidentals(pitches)
        positions = calc_positions(
            pitches, accidentals, INST_MARGIN, INST_WIDTH - INST_MARGIN
        )
        group = draw.Group()
        group.append(draw_notes(pitches, preferred, positions, accidentals))
        group.append(draw_range_lines(pitches, positions))

        group.append(
            draw.Text(
                self.name,
                x=INST_MARGIN,
                y=y_min - INST_TITLE_MARGIN,
                font_size=INST_TITLE_MARGIN,
                text_anchor="start",
                font_family=FONT_FAMILY,
                font_weight="bold",
            )
        )
        description = draw.Group()
        start_x, end_x, text_x = TEXT_SIZE * 1.5, TEXT_SIZE * 4.5, TEXT_SIZE * 7.5
        for i, r in enumerate(reversed(self.get_sounding_pitch_ranges())):
            y = y_max + TEXT_MARGIN + i * LINE_HEIGHT
            description.append(
                draw.Text(
                    r.start.display_name(),
                    x=start_x,
                    y=y,
                    font_weight="bold",
                    **TEXT_KWARGS,
                )
            )
            description.append(
                draw.Text(
                    r.end.display_name(),
                    x=end_x,
                    y=y,
                    font_weight="bold",
                    **TEXT_KWARGS,
                )
            )
            font_style = "italic" if not r.preferred else ""
            description.append(
                draw.Text(
                    r.descr,
                    x=text_x,
                    y=y,
                    **TEXT_KWARGS,
                    font_style=font_style,
                )
            )
        group.append(description)
        return group


INST_WIDTH = 60.0
INST_MARGIN = 4.0

INST_TITLE_SIZE = 6.0
INST_TITLE_MARGIN = INST_TITLE_SIZE * TEXT_MARGIN_FACTOR
TEXT_SIZE = 3.2
LINE_HEIGHT = TEXT_SIZE * 1.6
TEXT_KWARGS = {
    "font_family": FONT_FAMILY,
    "font_size": TEXT_SIZE,
    "dominant_baseline": "hanging",
    "text_anchor": "start",
}
TEXT_MARGIN = TEXT_SIZE * TEXT_MARGIN_FACTOR

SMALL_STROKE_WIDTH = 0.2


def calc_note_heads_relative(
    ranges: list[RelativeRange],
) -> tuple[list[Interval], list[bool]]:
    # exactly the same body as function below
    # this is bad
    # reason is typing stuff
    intervals = []
    preferred = []
    for i in range(len(ranges)):
        # start of range
        full = False
        if i != 0 and ranges[i - 1].preferred:
            full = True
        if ranges[i].preferred:
            full = True
        intervals.append(ranges[i].start)
        preferred.append(full)

        # end of range
        full = False
        if i != len(ranges) - 1 and ranges[i].end == ranges[i + 1].start:
            continue
        if ranges[i].preferred:
            full = True
        if i != len(ranges) - 1 and ranges[i + 1].preferred:
            full = True
        intervals.append(ranges[i].end)
        preferred.append(full)
    return intervals, preferred


def calc_note_heads(ranges: list[AbsoluteRange]) -> tuple[list[Pitch], list[bool]]:
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
        if (
            i != 0
            and pitches[i].to_staff_position() == pitches[i - 1].to_staff_position()
        ):
            if pitches[i].get_accidental() != pitches[i - 1].get_accidental():
                accidentals.append(pitches[i].get_accidental())
            else:
                accidentals.append("")
        else:
            acc = (
                ""
                if pitches[i].get_accidental() == "n"
                else pitches[i].get_accidental()
            )
            accidentals.append(acc)
    return accidentals


def calc_positions(
    pitches: list[Pitch], accidentals: list[str], x_0: float, x_max: float
) -> list[float]:
    widths = [ACC_MARGIN + SVG_ACC_OFFSET[acc] + NOTE_WIDTH for acc in accidentals]
    staff_distances = [
        pitches[i].to_staff_position() - pitches[i - 1].to_staff_position()
        for i in range(1, len(pitches))
    ]

    tot_staff_dist = sum(staff_distances)
    available_width = x_max - x_0 - sum(widths)

    between_dist = list(
        map(lambda x: x / tot_staff_dist * available_width, staff_distances)
    )

    positions = []
    current_position = x_0
    for i, width in enumerate(widths):
        positions.append(current_position + SVG_ACC_OFFSET[accidentals[i]])

        current_position += width
        if i < len(between_dist):
            current_position += between_dist[i]

    return positions


def draw_notes(
    pitches: list[Pitch],
    preferred: list[bool],
    positions: list[float],
    accidentals: list[str],
) -> draw.Group:
    notes = draw.Group()
    for pitch, full, note_head_pos, acc in zip(
        pitches, preferred, positions, accidentals
    ):
        if full:
            notes.append(
                draw.Use(
                    FULL_NOTEHEAD,
                    note_head_pos,
                    -pitch.to_staff_position(),
                )
            )
        else:
            notes.append(
                draw.Use(
                    EMPTY_NOTEHEAD,
                    note_head_pos,
                    -pitch.to_staff_position(),
                )
            )
        notes.append(
            draw.Use(
                SVG_ACC_MAP[acc],
                note_head_pos - SVG_ACC_OFFSET[acc],
                -pitch.to_staff_position(),
            )
        )
    return notes


def draw_range_lines(pitches: list[Pitch], positions: list[float]) -> draw.Group:
    range_lines = draw.Group()
    for i in range(len(pitches) - 1):
        start = (
            positions[i] + NOTE_WIDTH / 2,
            -pitches[i].to_staff_position(),
        )
        end = (
            positions[i + 1] + NOTE_WIDTH / 2,
            -pitches[i + 1].to_staff_position(),
        )
        diff = sub(end, start)
        line_len = length(diff)
        MIN_LINE_LEN = 1
        OFFSET_LEN = 2
        if line_len - 2 * OFFSET_LEN > MIN_LINE_LEN:
            range_lines.append(
                draw.Line(
                    *add(start, mult(OFFSET_LEN / line_len, diff)),
                    *add(end, mult(-OFFSET_LEN / line_len, diff)),
                    stroke_width=SMALL_STROKE_WIDTH,
                    stroke="black",
                )
            )
    return range_lines
