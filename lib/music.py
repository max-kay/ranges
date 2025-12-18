from math import log2
from typing import Self

from .consts import (
    INT_MODIFIER,
    NOTE_NAMES,
    ACCIDENTALS,
    NOTE_TO_MIDI_PITCH,
    ACCIDENTAL_MAP,
    STAFF_TO_NOTE,
    NOTE_TO_STAFF,
    ACC_UNICODE,
    MIDI_PITCH_TO_NOTE,
)


class Interval:
    def __init__(
        self, number: int, down: bool = False, modifier: str | None = None
    ) -> None:
        modifier = modifier if modifier else "n"
        if number < 1:
            raise ValueError(f"invalid inteval number: {number} < 1")
        normalized_num = (number - 1) % 7 + 1
        if normalized_num in [1, 4, 5]:
            if modifier == "j" or modifier == "m":
                raise ValueError(
                    f"interval with number: {number} (normalized: {normalized_num}) can not have modifier: '{modifier}'"
                )
        else:
            if modifier == "n":
                raise ValueError(
                    f"interval with number: {number} (normalized: {normalized_num}) can not have modifier: '{modifier}'"
                )
        if modifier not in INT_MODIFIER:
            raise ValueError(f"invalid modifier: '{modifier}'")
        if number == 1 and modifier == "n":
            down = False
        self.number = number
        self.down = down
        self.modifier = modifier

        if down ^ (self.to_halftones() < 0) and self.to_halftones() != 0:
            raise ValueError(
                f"encoutered interval with nonsensical direction: \
                dir is {'down' if down else 'up'} but halftones is {self.to_halftones()}"
            )

    def __eq__(self, other) -> bool:
        return (
            self.number == other.number
            and self.down == other.down
            and self.modifier == other.modifier
        )

    def num_lex_ord(self) -> int:
        """
        returns an integer for lexicographic ordering
        the interger is nonsensical for any other application
        """
        return self.get_dir() * (self.number * 100 + INT_MODIFIER.index(self.modifier))

    @classmethod
    def from_str(cls, string: str) -> Self:
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

        try:
            number = int(string)
        except ValueError:
            raise ValueError(f"Invalid Interval '{string}'")

        return cls(number, down, modifier)

    def __repr__(self) -> str:
        direction = "-" if self.down else ""
        modifier = self.modifier if self.modifier != "n" else ""
        return f"{direction}{modifier}{self.number}"

    def display_name(self) -> str:
        return repr(self)

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
                case _:
                    assert False, "unreachable"
        else:
            # difference for a minor version of that interval
            match number:
                case 2:
                    shift += 1
                case 3:
                    shift += 3
                case 6:
                    shift += 8
                case 7:
                    shift += 10
                case _:
                    assert False, "unreachable"
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
        return self.get_dir() * (shift + octave * 12)

    @classmethod
    def from_halftones(cls, num: int) -> Self:
        down = num < 0
        num = abs(num)
        octave = num // 12
        match num % 12:
            case 0:
                return cls(octave * 7 + 1, down, None)
            case 1:
                return cls(octave * 7 + 2, down, "m")
            case 2:
                return cls(octave * 7 + 2, down, "j")
            case 3:
                return cls(octave * 7 + 3, down, "m")
            case 4:
                return cls(octave * 7 + 3, down, "j")
            case 5:
                return cls(octave * 7 + 4, down, None)
            case 6:
                return cls(octave * 7 + 4, down, "a")
            case 7:
                return cls(octave * 7 + 5, down, None)
            case 8:
                return cls(octave * 7 + 6, down, "m")
            case 9:
                return cls(octave * 7 + 6, down, "j")
            case 10:
                return cls(octave * 7 + 7, down, "m")
            case 11:
                return cls(octave * 7 + 7, down, "j")
            case _:
                assert False, "unreachable"

    def normalize(self) -> Self:
        return Interval.from_halftones(self.to_halftones())  # type: ignore


class Pitch:
    def __init__(self, note: str, octave: int, accidental: str | None = None) -> None:
        self.note = note
        self.octave = octave
        self.accidental = accidental if accidental else "n"
        if note not in NOTE_NAMES:
            raise ValueError(f"invalid note name '{note}'")
        if self.accidental not in ACCIDENTALS:
            raise ValueError(f"invalid accidental '{accidental}'")

    @classmethod
    def from_str(cls, string: str) -> Self:
        note = string[0]
        if note not in NOTE_NAMES:
            raise ValueError(f"invalid note name '{note}'")
        if string[1] in ACCIDENTALS:
            accidental = string[1]
            if accidental not in ACCIDENTALS:
                raise ValueError(f"invalid accidental '{accidental}'")
            octave = int(string[2:])
            return cls(note, octave, accidental)
        else:
            octave = int(string[1:])
            return cls(note, octave)

    def __str__(self) -> str:
        acc = "" if self.accidental == "n" else self.accidental
        return f"{self.note}{acc}{self.octave}"

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

    def to_freq(self) -> float:
        midi = self.to_midi_pitch()
        return 2 ** ((midi - 69) / 12) * 440

    @classmethod
    def from_freq(cls, f: float) -> Self:
        midi = round(12 * log2(f / 440) + 69)
        return cls.from_midi_pitch(midi)

    def to_staff_position(self) -> int:
        """
        The staff position puts C4 (middle c) at 0 and D4 at 1
        """
        octave_dif = self.octave - 4  # C4 is middle C
        return octave_dif * 7 + NOTE_TO_STAFF[self.note]

    @classmethod
    def from_staff_position(cls, pos: int, accidental: str | None = None) -> Self:
        octave = pos // 7 + 4
        note = STAFF_TO_NOTE[pos % 7]
        return cls(note, octave, accidental)

    def get_accidental(self) -> str:
        return self.accidental

    def normalized(self):
        return Pitch.from_midi_pitch(self.to_midi_pitch())

    def num_lex_ord(self) -> int:
        """
        returns an integer for lexicographic ordering
        the interger is nonsensical for any other application
        """
        return (
            120 * self.octave
            + 10 * NOTE_TO_STAFF[self.note]
            + ACCIDENTAL_MAP[self.accidental]
        )

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
            print("had to return normalized pitch")
            return Pitch.from_midi_pitch(correct_midi)

    def display_name(self) -> str:
        if self.accidental in ["+", "&"]:
            return self.normalized().display_name()
        if self.accidental == "n":
            return f"{self.note}{self.octave}"
        return f"{self.note}{ACC_UNICODE[self.accidental]}{self.octave}"

    def __eq__(self, other) -> bool:
        return (
            self.note == other.note
            and self.octave == other.octave
            and self.accidental == other.accidental
        )


class AbsoluteRange:
    def __init__(self, start: Pitch, end: Pitch, descr: str, preferred: bool) -> None:
        assert start.num_lex_ord() <= end.num_lex_ord(), (
            "start must be smaller than end"
        )
        self.start = start
        self.end = end
        self.descr = descr
        self.preferred = preferred

    def __lt__(self, other: Self) -> bool:
        assert (self.start.num_lex_ord() >= other.end.num_lex_ord()) or (
            other.start.num_lex_ord() >= self.end.num_lex_ord()
        ), (
            f"tried to compare incompareable ranges ({self}).({self.start.num_lex_ord()} {self.end.num_lex_ord()})"
            f"({other}).({other.start.num_lex_ord()} {other.end.num_lex_ord()})"
        )

        return self.start.num_lex_ord() < other.start.num_lex_ord()

    def __str__(self) -> str:
        start = "" if self.preferred else "!"
        return f"{start}{self.start} {self.end} {self.descr}"

    def transposed(self, interval: Interval):
        return AbsoluteRange(
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
        r_start = Pitch.from_str(start)
        r_end = Pitch.from_str(end)
        return cls(r_start, r_end, " ".join(rest), preferred)


class RelativeRange:
    def __init__(
        self, start: Interval, end: Interval, descr: str, preferred: bool
    ) -> None:
        assert start.num_lex_ord() <= end.num_lex_ord(), (
            "start must be smaller than end"
        )
        self.start = start
        self.end = end
        self.descr = descr
        self.preferred = preferred

    def __lt__(self, other: Self) -> bool:
        assert not (
            (self.start.num_lex_ord() <= other.start.num_lex_ord())
            and (other.start.num_lex_ord() < self.end.num_lex_ord())
        ), f"tried to compare incompareable ranges {self} {other}"
        assert not (
            (self.start.num_lex_ord() < other.end.num_lex_ord())
            and (other.start.num_lex_ord() <= self.end.num_lex_ord())
        ), f"tried to compare incompareable ranges {self} {other}"

        return self.start.num_lex_ord() < other.start.num_lex_ord()

    def __str__(self) -> str:
        start = "" if self.preferred else "!"
        return f"{start}{self.start} {self.end} {self.descr}"

    @classmethod
    def from_str(cls, string: str):
        start, end, *rest = string.split()
        preferred = True
        if start.startswith("!"):
            start = start[1:]
            preferred = False
        r_start = Interval.from_str(start)
        r_end = Interval.from_str(end)
        return cls(r_start, r_end, " ".join(rest), preferred)
