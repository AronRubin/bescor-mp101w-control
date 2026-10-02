# Head probe session, 2026-10-01

A Controller (Waveshare RS-485 port in send mode, A+ Ring 2, B- Ring 1, GND Tip, through a TRRS breakout in the Head jack, Remote unplugged, Head on M) sent Frames to the Head from `tools/probe_frames.py` (via `tools/run_probe_plan.py` with spoken prompts) and logged anything received with the driver released. Frames repeat at 49.7 ms like the Remote. Plans: `plan_2a.txt`, `plan_2b.txt`, `plan_2c.txt`, `plan_3.txt`, `plan_4.txt`; every step is in `probe.csv` (`host_s,label,frame,rx,rx_at_s`). The Head's behaviour was observed and reported by the operator; nothing was instrumented.

An early run of group 2a (steps 1 to 5 as a single shell command, before the spoken runner) is also in `probe.csv`; its observations were not taken, and the spoken re-run replaced it.

## Replies

None. Across all 56 logged probe steps (Remote-style jogs, stops, speed-set, `08 03` frames, Pelco position queries), the receive side with the driver released saw no byte at any time, and no echo of the Controller's own frames. The Head did not answer a Pelco query (`51`, `53`) either.

## Results

| Probe | Frame | Result |
|---|---|---|
| Baseline jog right, address 01, speed `17` | `ff 01 00 04 17 00 1c` | Moved right. |
| Address 02 | `ff 02 00 04 17 00 1d` | **No motion**: the Head checks the address and answers only to `01`. |
| Speed `1c` (between the Remote's levels), `10` (below), `6f` (above) | `00 04 <spd> 00` | All moved right. Whether faster or slower than the baseline was too hard to judge by eye. |
| Speed `00` | `ff 01 00 04 00 00 05` | No motion. |
| 3-frame jog, then silence | `00 04 17 00` x3 | No visible motion. |
| 12- and 30-frame jogs, then 6 s of silence (speed `4f`) | `00 04 4f 00` | The Head moved while frames arrived and **stopped on its own** after they ceased: it has its own dead-man. |
| Jog, then **one** stop frame | `ff 01 00 00 00 00 01` x1 | Worked (stopped). |
| Speed-set `08 1c 00 5f`, then a baseline jog | `ff 01 08 1c 00 5f 84` | No visible effect reported; speed difference not judgeable by eye. |
| Zero `08 03 00 00` | `ff 01 08 03 00 00 0c` | Ended a sweep, and a go-to-zero was not reported for the first (stand-alone) zero step. |
| `08 03 00 2d` (45), `00 5a` (90), `01 54` (340) | as the Remote sends | Swept back and forth from a Controller. |
| `08 03 00 05` (5), `00 b4` (180), `00 1e` (30), `01 6b` (363) | extrapolated | **Nothing**: the Head ignores angle values the Remote does not send. |
| Spin left `08 03 01 69` | `ff 01 08 03 01 69 76` | Spun; the zero frame ended it. |
| What ends a sweep | | Zero frame and a jog end it; **Stop frames do not**; a repeat press (Remote) neither sends nor stops it. |
| Pelco query pan / tilt `51` / `53` | `ff 01 00 51 00 00 52`, `…53…54` | No motion, no reply. |
| Pelco set pan position, zero `4B` | `ff 01 00 4b 00 00 4c` | No motion reported (the Head was not at its zero mark at the start). |

## Not covered

Speed-to-angular-rate mapping (the speed values were not timed), the first stand-alone zero step's behaviour, Pelco absolute pan to a non-zero angle (`4b 11 94`, moderate risk: Down+Left bits with large data bytes), presets and the other Pelco candidates (deferred: the Head ignores Pelco position queries and set-pan-zero, so they are unlikely to help), Head on A.
