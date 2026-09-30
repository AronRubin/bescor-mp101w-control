# Tap log corpus, 2026-09-29

Bytes the Remote's MCU sends to the RS-485 transceiver, read from the DI net (BL3085 pin 4).

- **Wiring:** DI through a 10 kohm / 10 kohm divider (about 2.8 V) into the Waveshare TTL port (3V switch), GND to Remote ground, TXD/VCC open. FTDI FT232R on COM3.
- **Serial:** 9600 8N1, idle high. Host timestamps are per read chunk, so bytes within about 2 ms share a timestamp.
- **Tools:** `tools/tap_log.py` (recorder, optional spoken cue script), `tools/tap_frames.py` (frames and bursts; checksum = sum of bytes 1..5 mod 256).
- **Speed level on the Remote at the start of each run:** run 1 `57`/`4f` (changed during the run), run 2 `2f`, run 3 `37`.

## Files

| File | Run | What |
|---|---|---|
| `raw.csv`, `frames.txt` | 1 | Uncued, human-paced: speed sweep (Down to minimum, Up to maximum), one jog Left and one jog Up at each level `57` to `1f`, a 0 degrees press, 10 Jog Right taps, one TRRS unplug. The operator could not recall timings, so segment by frame content. |
| `raw2.csv`, `raw2.csv.events.csv`, `cues2.txt`, `frames2.txt` | 2 | Spoken cues, 4 s apart: 3 holds (about 3 s) each of Jog Up/Down/Left/Right, Spin Left x3, Spin Right x3, 0 deg x3, TRRS unplug/replug x2, one Speed Up. Presses queue when closer together than one 20-frame burst, so counts merge. |
| `raw3.csv`, `raw3.csv.events.csv`, `cues3.txt`, `frames3.txt` | 3 | Spoken cues, 10 to 15 s apart, single actions: one tap each of Jog Up/Down/Left/Right, Spin Left, Spin Right, 0 deg, Spin Left again, Speed Up x2, 10 s TRRS unplug, one jog after replug. |

Cue time to frame time lag is about 4 to 5 s (speech plus reaction).

## Frame table

`ff 01 cmd1 cmd2 data1 data2 chk`, address `01`, `chk` = (01 + cmd1 + cmd2 + data1 + data2) mod 256. All 2700+ frames seen are valid.

| Action (button as labelled) | Frame |
|---|---|
| Jog Up | `ff 01 00 10 00 <lvl> <chk>` |
| Jog Down | `ff 01 00 08 00 <lvl> <chk>` |
| Jog Left | `ff 01 00 02 <lvl> 00 <chk>` |
| Jog Right | `ff 01 00 04 <lvl> 00 <chk>` |
| Release after jog | `ff 01 00 00 00 00 01` |
| Speed Up / Speed Down | `ff 01 08 1c 00 <newlvl> <chk>` |
| Spin Left | `ff 01 08 03 01 69 76` |
| Spin Right | `ff 01 08 03 01 6a 77` |
| 0 deg | `ff 01 08 03 00 00 0c` |

`<lvl>` is the current speed level, `17` to `5f` in steps of 8 (10 levels). Speed Down at `17` and Speed Up at `5f` still send the frame with the same level.

## Behaviour

- Frames repeat about every 50 ms (49.7 ms measured on the wire in `captures/2026-09-30-cross-check`; an earlier 63 ms figure here was wrong). A jog tap sends 2 to 6 command frames; a hold sends command frames for the whole hold (53 to 67 frames for about 3 to 4 s); release sends 20 stop frames.
- Speed, Spin and 0 deg presses send 20 frames (about 1.3 s); presses closer together queue and send 40 or 60 frames back to back. No stop frame follows them.
- Idle: no traffic (silent for 10 s and more). Nothing is sent on power-up or plug-in.
- The speed level survives a TRRS unplug of at least 10 s.
- Spin has no stop button (the operator could not stop it with the same button); 0 deg turns until the physical 0 deg mark lines up with the housing tick mark. Whether Spin ends on its own is not established.
- The operator reports the Head moves as the buttons are labelled; that is the inverse of Pelco-D's tilt bits (`08` up, `10` down) and its pan bits (`02` right, `04` left).
- Jog mapping evidence: cued runs 2 and 3 and the level sweep in run 1 agree (Up `10`, Down `08`, Left `02`, Right `04`). Two hand-paced tests before the corpus (the jog re-tests in the tap-setup ticket) disagreed, probably from pressing in a different order than intended; the cued runs supersede them.
- Repeatability: 10 Jog Right taps gave exactly 10 bursts (run 1, 268 to 275 s). The earlier missing presses were host-side.

## Not covered

45, 90 and 340 degree modes (not needed for a software controller, per the operator), a Speed press mid-jog, two buttons at once, other speed levels for Jog Up/Left, and the meaning of the Spin data byte (`69` vs `6a`).
