# Bescor MP101W wired-control reverse engineering — findings to date

**Superseded by [spec.md](spec.md).** Snapshot of the research handoff that started this effort (2026-09). Later decisions live in the GitHub issues of this repo; this file is the starting evidence, not the spec, and some of its hypotheses (UART reading, "do not call it RS-485") were settled later.

No public MP101W protocol specification, open-source library, or useful teardown has been found. Existing MP-101 reverse-engineering projects apply to the older model and are electrically different.

## Physical interface

The MP101W remote connects through a **3.5 mm TRRS cable**. The wired remote **does not require batteries when connected** (it does for wireless).

Head powered from its normal 6 V / 1 A supply, remote disconnected:

```
Tip → battery/supply ground: continuity
Tip → Ring 1: ~5.63 V
Tip → Ring 2: ~5.70 V
Tip → Sleeve: ~6.165 V
```

Verified conductor roles and idle behaviour:

| Conductor | Role | Head only (no remote) | Remote connected, idle |
|---|---|---|---|
| Tip | GND | — | — |
| Ring 1 (Labrador CH1, yellow) | signal | ~5.6 V (pulled high by head) | ~0 V (pulled low by remote) |
| Ring 2 (Labrador CH2, cyan) | signal | ~5.6 V (pulled high by head) | ~6.0–6.2 V (driven higher by remote); periodic dips to ~5.7 V |
| Sleeve | remote power | ~6.1 V | ~6.1 V |

Interpretation (unconfirmed): the head pulls both signal lines up; the remote actively drives both lines, in opposite states at idle. Origin of the Ring 2 dips (remote load vs. head signalling back) is unknown.

## Remote resistance, unpowered

```
Tip → Ring 1 = 19.85 kΩ
Tip → Ring 2 = 19.85 kΩ
Tip → Sleeve: cycling ~7.5 kΩ → ~10 kΩ → >13 kΩ → ~10 kΩ (ohmmeter charging the remote's supply; not meaningful)
```

The matched 19.85 kΩ paths on both signal conductors appear deliberate.

## Remote controls

MCU + display. Speed +/−, speed display; jog up/down/left/right; 0°/45°/90°/340° modes; continuous spin left/right. Strongly indicates command encoding rather than passive contact wiring.

## Oscilloscope findings (EspoTek Labrador)

Connections: Tip → GND, Ring 1 → CH1, Ring 2 → CH2, Sleeve untouched.

During Speed Up / Speed Down, Ring 1 and Ring 2 show nearly exact **complementary transitions** at the same instants — strong evidence of one bitstream carried as a complementary pair (not TX/RX, not clock/data). Do **not** call it RS-485 yet; the 0–6 V behaviour does not justify it.

## Timing

Edge-to-edge intervals cluster at ~98–108 µs, ~205 µs, ~303–313 µs → integer multiples of **~104 µs ≈ 1/9600 s**. Hypothesis: ~9600 bit/s.

Speed Up tail intervals (µs): 107, 98, 313, 313, 98, 107, 98, 313, 205, 107, 206, 107 ≈ 1,1,3,3,1,1,1,3,2,1,2,1 bit periods.
Speed Down tail (µs): 98, 117, 293, 313, 117, 98, 98, 313, 195, 117, 196, 117 — essentially the same, suggesting a common trailer; command-specific bytes likely precede the captured window.

Speed Up CH1 edge times (ms): −11.972 F, −11.865 R, −11.767 F, −11.454 R, −11.141 F, −11.043 R, −10.936 F, −10.838 R, −10.525 F, −10.320 R, −10.213 F, −10.007 R, −9.900 F. CH2 shows the opposite edge at each point.

**Discarded:** an earlier tentative UART reading of 0x47 / 0x6C — packet start is missing, so byte alignment is unknown.

## Captures

[`captures/2026-09-early-clipped/`](../captures/2026-09-early-clipped/) — Labrador Desktop_Interface `C`/`V` snapshot exports (`t, v`; time order may be reversed). **Beginnings are clipped**: these exports contain only the on-screen window decimated to the graph sample count. Do not infer packet bytes from them.

## Unknowns

UART vs custom NRZ; bits per packet; start/stop framing; parity; checksum; command IDs; repetition; press vs release messages; whether speed is embedded in movement commands; whether the head ever transmits.

## Hypothesis confidence

- High: Tip = GND, Sleeve = remote power, Ring 1/Ring 2 = complementary digital signals, ~104 µs fundamental.
- Medium/high: ~9600 bit/s.
