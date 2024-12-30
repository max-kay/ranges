UG_RANGE = (16, 24)
G_RANGE = (2, 10)
F_RANGE = (-10, -2)
LF_RANGE = (-24, -16)
NOTE_NAMES = [chr(ord("A") + i) for i in range(7)]

NOTE_TO_STAFF = {
    "C": 0,
    "D": 1,
    "E": 2,
    "F": 3,
    "G": 4,
    "A": 5,
    "B": 6,
}
STAFF_TO_NOTE = {
    0: "C",
    1: "D",
    2: "E",
    3: "F",
    4: "G",
    5: "A",
    6: "B",
}

NOTE_TO_MIDI_PITCH = {
    "C": 0,
    "D": 2,
    "E": 4,
    "F": 5,
    "G": 7,
    "A": 9,
    "B": 11,
}

MIDI_PITCH_TO_NOTE = {
    0: "C",
    1: "C#",
    2: "D",
    3: "Eb",
    4: "E",
    5: "F",
    6: "F#",
    7: "G",
    8: "Ab",
    9: "A",
    10: "Bb",
    11: "B",
}
ACCIDENTALS = ["&", "b", "n", "#", "+"]
ACCIDENTAL_MAP = {
    "b": -1,
    "#": 1,
    "n": 0,
    "+": 2,
    "&": -2,
}

INT_MODIFIER = ["j", "m", "a", "d", "n"]
