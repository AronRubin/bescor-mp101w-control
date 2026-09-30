# Remote joystick Tap log corpus, 2026-09-30

Tap log of the Remote's joystick (DI net, same tap and serial settings as `captures/2026-09-29-tap/manifest.md`), spoken cues, speed level `4f` throughout, no Speed/Spin buttons pressed. Cue-to-frame lag 3 to 10 s here (long cues, human reaction), so segment by frame content.

| File | What |
|---|---|
| `cues.txt`, `raw.csv`, `raw.csv.events.csv`, `frames.txt` | Run 1 (cues 11-12 s apart): the four diagonals, up by a quarter / half / full, slow ramp up, full up eased back to half, left-to-right and up-to-down swings through centre, one circle around the edge. |
| `cues2.txt`, `raw2.csv`, `raw2.csv.events.csv`, `frames2.txt` | Run 2: upper-left x3 and upper-right x3, firm holds (the upper diagonals were not combined in run 1). |

## Frames

Same format `ff 01 cmd1 cmd2 data1 data2 chk`, cmd1 `00`. `cmd2` bits: Left `02`, Right `04`, Down `08`, Up `10`. `data1` = speed of the pan (left/right) axis, `data2` = speed of the tilt (up/down) axis, each the current level when that axis is active and `00` when not.

| Stick position | Frame |
|---|---|
| Upper-left | `ff 01 00 12 4f 4f b1` |
| Upper-right | `ff 01 00 14 4f 4f b3` |
| Lower-left | `ff 01 00 0a 4f 4f a9` |
| Lower-right | `ff 01 00 0c 4f 4f ab` |
| Release | `ff 01 00 00 00 00 01` (20 times) |

## Behaviour

- All four diagonals send one combined frame repeating while held (run 1 lower diagonals, run 2 upper diagonals). In run 1 the upper diagonals were reached via a cardinal first (upper-left sent Left x5 then Up; upper-right sent Right only), so a slow arrival sends cardinal frames before the diagonal.
- Deflection amount is not sent: a quarter, half and full push of Up all send the same `00 10 00 4f` frame (only the hold length differs), and a slow ramp sends the same frame too.
- Swinging through the centre (left to right, up to down) sends 20 stop frames between the two directions; tracing the edge (circle) switches directly between cardinal frames (Up, Right, Down, Left, Up) with no stop frame and no diagonal frames, then 20 stop frames on release.
- Releasing from a partial deflection, eased back to half, behaves like a full release (same frame until release, then 20 stop frames).
- Operator observation (not instrumented): the Head's motion during the diagonals was inconsistent; it did not reliably move along both axes.
- Stray tap-side bytes appear at burst starts as in the cross-check corpus (not on the wire).

## Not covered

How Spin ends (ruled out at the operator's call), the Head's response to combined frames (to validate with a Controller).
