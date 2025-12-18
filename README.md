# Ranges of Instruments


A Python library to generate nice overviews over the ranges instruments.

## Instrument files

*Normal*
```
Alto Saxophone
// Comment

Transposition: -j6              // transposition (here in Eb)

Ranges:
!Bb3 D4 Hard to Control         // the ranges transposed
D4 C#5 Warm Controlable         // (as the player reads it)
D5 C#6 Bright Controlable
D6 F#6 Hard to Control
!F#6 D7 Possible                // '!' marks ranges that should rarely be used
```

*StringedInsruments*
```
Bass

Transposition: -8

Open Strings: E2 A2 D3 G3       // open string

Ranges:                         // the intervals
1 8
8 15
15 22
```

To compose your own range overviews adjust `main.py`

Not the nicest code I've written but it does its thing.
