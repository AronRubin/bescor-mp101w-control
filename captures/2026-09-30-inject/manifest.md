# Controller injection experiments, 2026-09-30

First time a Controller drove the Head: the Waveshare USB TO RS232/485/TTL **RS-485 port** (A+ to Ring 2, B- to Ring 1, its GND to Tip) through a TRRS breakout plugged into the Head jack, Head on M, Remote unplugged, frames from `tools/send_frames.py` (Remote-style frames, 49.7 ms cadence, 20 stop frames after).

## Ladder

| Step | Wiring | Result |
|---|---|---|
| 1 | bare: A+ / B- / GND only | Capture below shows a clean differential; the Head moved only once the tilt was off its upper limit (see below) |
| 2 | plus 1 kOhm Ring 1 to Tip | Ring 1 0.5 V idle; driven swing Ring 1 up to ~1.3 V and Ring 2 down to about -3.9 V |
| 3 | plus ~470 ohm Sleeve to Tip | no visible motion (tilt still at its upper limit) |
| back to 1 | bare again | Jog Down, Jog Up, all four diagonals, and a Jog after a Head power-cycle and 30 s of silence all moved the Head |

The Jog Up tests in steps 1 to 3 had no visible effect because the Head tilt was already at its upper limit, not because the Head ignored the frames; the Head moved as soon as the Remote jogged it down and bare Step 1 was re-tested.

## Captures

Labrador CH1 = Ring 1, CH2 = Ring 2, GND = Tip, gain 4, 375 kS/s, one second of Jog Up at level `4f`:

- `step1-bare-up.csv`: Ring 1 / Ring 2 idle 4.88 V / 6.18 V (driver released, Head and Waveshare bias), driven swing about 1.1 V to over 7.5 V (the 7.5 V is the gain 4 clip), differential about -6.4 to +5.7 V, Ring 2 low = start bit, 10 frames decode.
- `step2-bias1k-up.csv`: with the 1 kOhm, Ring 1 idle 0.5 V, Ring 2 idle 4.8 V.

## Result

Bare RS-485 is enough: no Sleeve load, no bias, no Remote ever plugged in first, no keep-alive traffic (30 s idle then a jog worked), Head on M. Diagonal frames move both axes (the tilt is subtle at level `4f`). Not tested: Head on A, other speed levels, speed-set frames, Spin, 0 deg, a bare plug that actuates no jack switch.
