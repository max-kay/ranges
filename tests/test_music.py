import pytest
from lib.music import Pitch, Interval


def test_pitch():
    assert Pitch.from_str("C0").to_midi_pitch() == 12
    assert Pitch.from_str("E0").to_midi_pitch() == 12 + 4
    assert Pitch.from_str("C1").to_midi_pitch() == 24
    assert Pitch.from_str("Bb0").to_midi_pitch() == 24 - 2
    assert Pitch.from_str("C#1").to_midi_pitch() == 24 + 1
    assert str(Pitch.from_str("C#1")) == "C#1"
    assert str(Pitch.from_str("Cb1")) == "Cb1"
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


def test_interval():
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

    with pytest.raises(ValueError):
        # this should fail because the direction of this doesn't make sense
        # the dir is up but the interval actually transposes down
        Interval.from_str("d1")
        # same but other dir
        Interval.from_str("-d1")

    assert Interval.from_str("d2").to_halftones() == 0
    assert Interval.from_str("a2").to_halftones() == 3

    assert Interval.from_str("d3").to_halftones() == 2
    assert Interval.from_str("a3").to_halftones() == 5

    assert Interval.from_str("-m6").to_halftones() == -8
    assert Interval.from_str("-1").to_halftones() == 0
    assert Interval.from_str("m13").to_halftones() == 20

    assert Interval.from_str("d2").normalize() == Interval.from_str("1")
    assert Interval.from_str("-d2").normalize() == Interval.from_str("1")
    assert Interval.from_str("d5").normalize() == Interval.from_str("a4")
    assert Interval.from_str("-d5").normalize() == Interval.from_str("-a4")
    assert Interval.from_str("a3").normalize() == Interval.from_str("4")
    assert Interval.from_str("-a3").normalize() == Interval.from_str("-4")

    trans("C0", "m3", "Eb0")
    trans("C2", "j3", "E2")
    trans("E2", "j3", "G#2")
    trans("E2", "m9", "F3")
    trans("Bb1", "j3", "D2")
    trans("B1", "j3", "D#2")
    trans("C1", "5", "G1")
    trans("C1", "8", "C2")

    trans("Ab1", "d8", "A&2")
    trans("A1", "d8", "Ab2")
    trans("A#1", "d8", "A2")

    trans("Ab1", "a8", "A2")
    trans("A1", "a8", "A#2")
    trans("A#1", "a8", "A+2")

    trans("A&1", "d8", "F#2")  # with renormalization
    trans("A+1", "a8", "C3")  # with renormalization


def trans(start: str, interval: str, end: str):
    assert str(Pitch.from_str(start).transposed(Interval.from_str(interval))) == end
