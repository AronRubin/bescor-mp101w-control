# Wire log of the 45 / 90 / 340 degree buttons, 2026-10-01

Bytes decoded from Ring 1 / Ring 2 by the Waveshare RS-485 port in receive mode (A+ Ring 2, B- Ring 1, GND Tip), Remote and Head both connected, Head on M, nothing sent from the PC. COM3, 9600 8N1, recorded with `tools/tap_log.py` and a spoken cue script; frames from `tools/tap_frames.py`. Speed level on the Remote not recorded (the frames below do not carry it).

## Files

| File | What |
|---|---|
| `cues.txt`, `raw.csv`, `raw.csv.events.csv`, `frames.txt` | One run: for each of 45, 90 and 340 degrees, press once, press again, then press 0 degrees to return. |

## Frames

180 frames, 0 stray or bad bytes. Cue time to frame time lag is about 4 s.

| Button | Frame | Count |
|---|---|---|
| 45 deg | `ff 01 08 03 00 2d 39` | 40 |
| 90 deg | `ff 01 08 03 00 5a 66` | 40 |
| 340 deg | `ff 01 08 03 01 54 61` | 40 |
| 0 deg (after each) | `ff 01 08 03 00 00 0c` | 20 |

## Result

- `08 03 <hi> <lo>` carries a 16-bit number in degrees: 0 deg = `0000`, 45 = `002d`, 90 = `005a`, 340 = `0154`, and Spin Left / Right = `0169` / `016a` = 361 / 362 (values above 360 are modes).
- The sweep buttons send 40 frames (about 2 s), against 20 for 0 deg and the other 20-frame presses, then the link goes silent.
- The operator reports the Head sweeps back and forth over roughly that range, so for 45 / 90 / 340 the number is a sweep extent or sweep command, not a go-to position. The Head keeps sweeping while the link is silent, so the oscillation is the Head's own.
- The second press of each button sent nothing on the wire and did not stop the sweep (operator report). Whether the following 0 deg press ended the sweep was not noted.

## Not covered

Whether the sweep is centred on 0 or on the current position, whether other values (for example 5 or 180) also sweep, how a sweep is stopped (a repeat press does nothing; 0 deg or a jog are untested as stops), and whether any command goes to an arbitrary angle.
