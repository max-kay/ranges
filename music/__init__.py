from functools import total_ordering
from .consts import *


class Interval:
    def __init__(
        self, number: int, down: bool = False, modifier: str | None = None
    ) -> None:
        modifier = modifier if modifier else "n"
        assert number >= 1
        normalized_num = (number - 1) % 7 + 1
        if normalized_num in [1, 4, 5]:
            assert modifier != "j" and modifier != "m"
        else:
            assert modifier != "n"
        assert modifier in INT_MODIFIER
        self.number = number
        self.down = down
        self.modifier = modifier

    def __eq__(self, other) -> bool:
        return self.number == other.number and self.down == other.down and self.modifier == other.modifier

    @classmethod
    def from_str(cls, string: str):
        """
        Parse an interval from its string representation.
        Format: [Direction (optional '-')][Modifier][Number]
        Examples: 'm3', '-a4', '5'
        """
        if string.startswith("-"):
            down = True
            string = string[1:]
        else:
            down = False

        if string[0] in INT_MODIFIER:
            modifier = string[0]
            string = string[1:]
        else:
            modifier = None

        number = int(string)

        return cls(number, down, modifier)

    def __repr__(self):
        direction = "-" if self.down else ""
        modifier = self.modifier if self.modifier!= "n" else ""
        return f"{modifier}{self.number}{direction}"

    def get_dir(self) -> int:
        return -1 if self.down else 1

    def to_halftones(self) -> int:
        octave = (self.number - 1) // 7
        number = (self.number - 1) % 7 + 1
        shift = 0
        if number in [1, 4, 5]:
            match number:
                case 1:
                    pass
                case 4:
                    shift += 5
                case 5:
                    shift += 7
                case _:
                    assert False, "unreachable"
            match self.modifier:
                case "n":
                    pass
                case "a":
                    shift += 1
                case "d":
                    shift += -1
        else:
            # difference from a minor version of that interval
            match number:
                case 2:
                    shift += 1
                case 3:
                    shift += 3
                case 6:
                    shift += 8
                case 7:
                    shift += 10
            match self.modifier:
                case "d":
                    shift += -1
                case "m":
                    pass
                case "j":
                    shift += 1
                case "a":
                    shift += 2
                case _:
                    assert False, "unreachable"
        direction = -1 if self.down else 1
        return direction * (shift + octave * 12)


@total_ordering
class Pitch:
    def __init__(self, note: str, octave: int, accidental: str | None = None) -> None:
        self.note = note
        self.octave = octave
        self.accidental = accidental if accidental else "n"

    @classmethod
    def from_str(cls, string: str):
        note = string[0]
        assert ord("A") <= ord(string[0]) <= ord("G"), f"invalid note name {note}"
        if not string[1].isdigit():
            accidental = string[1]
            assert accidental in ACCIDENTALS, f"invalid accidental {accidental}"
            octave = int(string[2:])
            return cls(note, octave, accidental)
        else:
            octave = int(string[1:])
            return cls(note, octave)

    def __str__(self) -> str:
        return f"{self.note}{self.accidental}{self.octave}"

    def to_midi_pitch(self) -> int:
        return (
            NOTE_TO_MIDI_PITCH[self.note]
            + ACCIDENTAL_MAP[self.accidental]
            + self.octave * 12
            + 12
        )

    @classmethod
    def from_midi_pitch(cls, pitch: int):
        octave = pitch // 12 - 1
        note = MIDI_PITCH_TO_NOTE[pitch % 12]
        return cls.from_str(f"{note}{octave}")

    def to_staff_position(self) -> int:
        """
        The staff position puts C4 (middle c) at 0 and D4 at 1
        """
        octave_dif = self.octave - 4  # C4 is middle C
        return octave_dif * 7 + NOTE_TO_STAFF[self.note]

    @classmethod
    def from_staff_position(cls, pos: int, accidental: str | None = None):
        octave = pos // 7 + 4
        note = STAFF_TO_NOTE[pos % 7]
        return cls(note, octave, accidental)

    def get_accidental(self) -> str:
        return self.accidental

    def transposed(self, interval: Interval):
        shift = interval.get_dir() * (interval.number - 1)
        position = self.to_staff_position() + shift
        current_midi = Pitch.from_staff_position(position).to_midi_pitch()
        correct_midi = self.to_midi_pitch() + interval.to_halftones()
        additional_shift = correct_midi - current_midi
        try:
            accidental = ACCIDENTALS[additional_shift + 2]
            return Pitch.from_staff_position(position, accidental)
        except (
            IndexError
        ):  # happens if the needed accidental exceeds double sharps or double flats
            return Pitch.from_midi_pitch(correct_midi)

    def __eq__(self, other) -> bool:
        return self.note == other.note and self.octave == other.octave and self.accidental == other.accidental

    def __lt__(self, other) -> bool:
        if self.to_staff_position() == other.to_staff_position():
            return ACCIDENTALS.index(self.accidental) < ACCIDENTALS.index(other.accidental)
        return self.to_staff_position() < other.to_staff_position()


class PartialRange:
    def __init__(self, start: Pitch, end: Pitch, descr: str, preferred: bool) -> None:
        assert start <= end, "start must be smaller than end"
        self.start = start
        self.end = end
        self.descr = descr
        self.preferred = preferred

    def __lt__(self, other) -> bool:
        assert self.start != other.start
        return self.start < other.start

    def __str__(self) -> str:
        start = "" if self.preferred else "!"
        return f"{start}{self.start} {self.end} {self.descr}"

    def transposed(self, interval: Interval):
        return PartialRange(
            self.start.transposed(interval),
            self.end.transposed(interval),
            self.descr,
            self.preferred,
        )

    @classmethod
    def from_str(cls, string: str):
        start, end, *rest = string.split()
        preferred = True
        if start.startswith("!"):
            start = start[1:]
            preferred = False
        start = Pitch.from_str(start)
        end = Pitch.from_str(end)
        return cls(start, end, " ".join(rest), preferred)


class Instrument:
    def __init__(
        self,
        name: str,
        ranges: list[PartialRange],
        transposition: Interval | None = None,
    ) -> None:
        self.name = name
        self.ranges = sorted(ranges)
        self.transposition = transposition if transposition else Interval.from_str("1")
        for i in range(0, len(self.ranges) - 1):
            assert (
                self.ranges[i].end <= self.ranges[i + 1].start
            ), f"{self.name} has invalid ranges"

    def __str__(self):
        ranges_str = "\n".join(str(r) for r in self.ranges)
        transposition = (
            f"{self.transposition}\n" if self.transposition != Interval.from_str("1") else ""
        )
        return f"{self.name}\n{transposition}{ranges_str}"

    def min_sounding_pitch(self) -> Pitch:
        return self.ranges[0].start.transposed(self.transposition)

    def max_sounding_pitch(self) -> Pitch:
        return self.ranges[-1].end.transposed(self.transposition)

    def get_sounding_pitch_ranges(self) -> list[PartialRange]:
        out = []
        for r in self.ranges:
            out.append(r.transposed(self.transposition))
        return out

    @classmethod
    def from_file(cls, path: str):
        with open(path, encoding="utf8", mode="r") as file:
            lines = [line.strip() for line in file.readlines() if line.strip() != ""]
        name = lines[0]
        if lines[1].startswith("tran"):
            try:
                transposition = Interval.from_str(lines[1].split()[1])
            except:
                print(f"failed to parse transposition of {name} file: {path}")
                assert False
            lines = lines[2:]
        else:
            transposition = Interval.from_str("1")
            lines = lines[1:]
        ranges = []
        for line in lines:
            try:
                ranges.append(PartialRange.from_str(line))
            except:
                print(f"failed to parse range of {name} file: {path}\n {line}")
                assert False
        return cls(name, ranges, transposition)


def pitch_test():
    assert Pitch.from_str("C0").to_midi_pitch() == 12
    assert Pitch.from_str("E0").to_midi_pitch() == 12 + 4
    assert Pitch.from_str("C1").to_midi_pitch() == 24
    assert Pitch.from_str("Bb0").to_midi_pitch() == 24 - 2
    assert Pitch.from_str("C#1").to_midi_pitch() == 24 + 1
    assert str(Pitch.from_str("C#1")) == "C#1"
    assert Pitch.from_str("C4").to_staff_position() == 0
    assert Pitch.from_str("D4").to_staff_position() == 1
    assert Pitch.from_str("D#4").to_staff_position() == 1
    assert Pitch.from_str("Db4").to_staff_position() == 1
    assert Pitch.from_str("Bb3").to_staff_position() == -1
    assert Pitch.from_str("C5").to_staff_position() == 7
    assert Pitch.from_str("C3").to_staff_position() == -7

    note = Pitch.from_str("D4")
    assert note == Pitch.from_midi_pitch(note.to_midi_pitch())
    assert str(note) == str(Pitch.from_midi_pitch(note.to_midi_pitch()))
    note = Pitch.from_str("C3")
    assert note == Pitch.from_midi_pitch(note.to_midi_pitch())
    assert str(note) == str(Pitch.from_midi_pitch(note.to_midi_pitch()))
    note = Pitch.from_str("Bb2")
    assert note == Pitch.from_midi_pitch(note.to_midi_pitch())
    assert str(note) == str(Pitch.from_midi_pitch(note.to_midi_pitch()))
    note = Pitch.from_str("F#4")
    assert note == Pitch.from_midi_pitch(note.to_midi_pitch())
    assert str(note) == str(Pitch.from_midi_pitch(note.to_midi_pitch()))


def interval_test():
    assert Interval.from_str("1").to_halftones() == 0
    assert Interval.from_str("m2").to_halftones() == 1
    assert Interval.from_str("j2").to_halftones() == 2
    assert Interval.from_str("m3").to_halftones() == 3
    assert Interval.from_str("j3").to_halftones() == 4
    assert Interval.from_str("4").to_halftones() == 5
    assert Interval.from_str("a4").to_halftones() == 6
    assert Interval.from_str("d5").to_halftones() == 6
    assert Interval.from_str("5").to_halftones() == 7
    assert Interval.from_str("m6").to_halftones() == 8
    assert Interval.from_str("j6").to_halftones() == 9
    assert Interval.from_str("m7").to_halftones() == 10
    assert Interval.from_str("j7").to_halftones() == 11

    assert Interval.from_str("a3").to_halftones() == 5
    assert Interval.from_str("d3").to_halftones() == 2

    assert Interval.from_str("-m6").to_halftones() == -8
    assert Interval.from_str("m13").to_halftones() == 20

    assert str(Pitch.from_str("C0").transposed(Interval.from_str("m3"))) == "Eb0"
    assert str(Pitch.from_str("C0").transposed(Interval.from_str("j3"))) == "E0"
    assert str(Pitch.from_str("Bb1").transposed(Interval.from_str("j3"))) == "D2"
    assert str(Pitch.from_str("B1").transposed(Interval.from_str("j3"))) == "D#2"
    assert str(Pitch.from_str("C1").transposed(Interval.from_str("5"))) == "G1"
    assert str(Pitch.from_str("C1").transposed(Interval.from_str("8"))) == "C2"


if __name__ == "__main__":
    pitch_test()
    interval_test()
