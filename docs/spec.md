# Bescor MP101W wired link specification

How a **Controller** replaces the **Remote** on the MP101W **Head**'s TRRS jack: electrical layer, framing, command table and Head behaviour, with the evidence behind each claim. Terms (Head, Remote, Controller, Host, Tip, Ring 1, Ring 2, Sleeve, Capture, Tap log, Wire log, Frame) are defined in [CONTEXT.md](../CONTEXT.md).

This is a reverse-engineered description, not a vendor document. Bescor has published no protocol for the MP101W.

## 1. Scope, conformance and evidence tags

**Status: Normative.**

**In scope.** Everything a Controller needs to command the Head over the TRRS jack. **Out of scope.** The Host-facing API, Controller hardware, the MP101W wireless protocol, the older MP-101, and camera zoom.

**Remote profile.** A Controller that emits exactly what the Remote emits (the byte sequences, timings and frame counts in sections 3 to 5) is known to work. Sections tagged *Normative* define that profile. Sections tagged *Informative* describe what the Head tolerates beyond the profile and what was measured; they are observations about one Head, not guarantees. Nothing in this document uses MUST / SHOULD in the RFC 2119 sense.

**Evidence tags.** Behavioural claims carry one of three tags:

| Tag | Meaning |
|---|---|
| `[wire]` | Bytes recorded from the Remote's link: a Wire log, or a Tap log whose agreement with the wire was cross-checked (the wire carried exactly the Tap log's Frames; the tap adds stray bytes the wire lacks, so the wire wins). Appendix B says which actions were checked on the wire. |
| `[observed]` | The operator watched the Head do it. Nothing was instrumented, so speed and distance differences too small to see by eye are not captured. |
| `[untested]` | Not tried. Written down so a builder does not assume it works. Collected in section 8. |

Most untagged text is definitional (a layout, a table) and follows from the tagged evidence beside it.

## 2. Electrical layer

**Status: Normative for the line states; Informative for measurements.**

### 2.1 Conductors

The link is a 3.5 mm TRRS plug into the Head's jack.

| Conductor | Role |
|---|---|
| Tip | Ground. |
| Ring 1 | RS-485 **B** (inverting). Idles low when the Remote drives it. |
| Ring 2 | RS-485 **A** (non-inverting). Idles high when the Remote drives it. |
| Sleeve | About 6 V from the Head, powering the Remote. |

`[wire]` Ring 1 and Ring 2 carry one bit stream as a complementary pair, bit-identical on the two lines. The Remote's transceiver is a BL3085 (RS-485) with its receive output unconnected, so the Remote is transmit-only.

### 2.2 Line states

| State | Ring 1 | Ring 2 |
|---|---|---|
| Idle mark (Remote connected, driving) | about 0 V | about 5.8 to 6.0 V |
| Start bit / space | high | low |
| Head alone (nobody driving) | about 5.6 V | about 5.6 V |

- `[wire]` With the Remote driving, both lines swing rail to rail (0 to about 6 V, the Sleeve level) with the driver always enabled (DE held high). Edges are faster than the 2.7 µs sample period of the Capture, with overshoot on both rings (Ring 1 about -1.3 to 6.9 V, Ring 2 about -2.6 to 7.5 V; probing may exaggerate it).
- `[wire]` The Head pulls both signal lines up through about 9 to 9.4 kΩ from about 5.6 V (Thevenin figures). With nobody driving, the differential is about 0 V.
- `[wire]` The Head never transmits unprompted (Head alone: 60 s idle, power-up, power-off, A/M switch flip; Remote connected: silent at idle).
- `[observed]` The Head never replied to any of 56 probe steps (section 6.3), so a Controller needs no receive path.

### 2.3 Sleeve

- `[wire]` The Sleeve measures about 5.98 V to Tip; the Remote's transceiver runs from it at about 5.97 V, slightly above the BL3085's 5.5 V rating.
- `[wire]` The Remote draws about 38 mA at plug-in and 12 mA steady, idle or jogging.
- `[observed]` A Controller worked with the Sleeve unconnected.
- `[untested]` Powering a Controller from the Sleeve beyond the Remote's 12 mA.

### 2.4 Head mode switch

The Head has an A (auto) / M (manual) switch. Wire control needs **M**. Per the Remote's user manual (not in this repository): in M the Head is controlled one-to-one by the plugged-in Remote, powered by the Head, and unplugging returns it to wireless mode. `[observed]` Controller frames moved the Head on M with the Remote unplugged. `[untested]` Controller frames with the Head on A.

## 3. Framing

**Status: Normative.**

Standard asynchronous serial, RS-485 differential: **9600 baud, 8 data bits, no parity, 1 stop bit**, least significant bit first, idle = mark. Ring 1 high is the start bit. `[wire]` (Wire log decoded on both rings, no framing errors, about 104 µs bit period.)

A **Frame** is seven bytes:

```
ff  01  cmd1  cmd2  data1  data2  chk
```

| Byte | Meaning |
|---|---|
| `ff` | Sync. |
| `01` | Address. The Remote always sends `01`. |
| `cmd1`, `cmd2` | Command (section 4). |
| `data1`, `data2` | Command data (section 4). |
| `chk` | Checksum: (address + cmd1 + cmd2 + data1 + data2) mod 256. The sync byte is not summed. |

`[wire]` More than 2700 Frames in the Tap log corpus all verify. A 7-byte Frame lasts about 7 ms.

**Worked example.** Jog Right at speed level `4f`:

```
ff 01 00 04 4f 00 54      chk = 01 + 00 + 04 + 4f + 00 = 0x54
```

## 4. Commands

**Status: Normative (the Remote's command set); Head tolerances are in section 6.**

`<lvl>` is a speed level. The Remote has ten, `17` to `5f` in steps of 8: `17 1f 27 2f 37 3f 47 4f 57 5f`. `<chk>` is computed as in section 3.

| Action | Frame | Tag |
|---|---|---|
| Jog Up | `ff 01 00 10 00 <lvl> <chk>` | `[wire]` |
| Jog Down | `ff 01 00 08 00 <lvl> <chk>` | `[wire]` |
| Jog Left | `ff 01 00 02 <lvl> 00 <chk>` | `[wire]` |
| Jog Right | `ff 01 00 04 <lvl> 00 <chk>` | `[wire]` |
| Diagonal Up-Left | `ff 01 00 12 <lvl> <lvl> <chk>` | `[wire]` |
| Diagonal Up-Right | `ff 01 00 14 <lvl> <lvl> <chk>` | `[wire]` |
| Diagonal Down-Left | `ff 01 00 0a <lvl> <lvl> <chk>` | `[wire]` |
| Diagonal Down-Right | `ff 01 00 0c <lvl> <lvl> <chk>` | `[wire]` |
| Stop (sent on release) | `ff 01 00 00 00 00 01` | `[wire]` |
| Speed Up / Speed Down | `ff 01 08 1c 00 <newlvl> <chk>` | `[wire]` |
| Go to 0 degrees | `ff 01 08 03 00 00 0c` | `[wire]` |
| Sweep 45 degrees | `ff 01 08 03 00 2d 39` | `[wire]` |
| Sweep 90 degrees | `ff 01 08 03 00 5a 66` | `[wire]` |
| Sweep 340 degrees | `ff 01 08 03 01 54 61` | `[wire]` |
| Spin Left (infinite rotation) | `ff 01 08 03 01 69 76` | `[wire]` |
| Spin Right (infinite rotation) | `ff 01 08 03 01 6a 77` | `[wire]` |

Notes.

- **Direction bits** in `cmd2`: Left `02`, Right `04`, Down `08`, Up `10`. The Head moves as the Remote's buttons are labelled (`[observed]`). Combine bits for diagonals.
- **Speed bytes.** `data1` is the pan (Left/Right) speed, `data2` the tilt (Up/Down) speed. Each carries the current level when that axis is active and `00` when it is not. In a diagonal both carry the level.
- **Joystick.** The Remote's joystick is digital in effect: a quarter, half and full deflection send the same Frame, so a Controller has no analog deflection to reproduce (`[wire]`, Tap log). A slow ramp to a diagonal sends the cardinal Frame first, then the diagonal (`[wire]`, Tap log).
- **`08 03 <hi> <lo>`** carries a 16-bit number in degrees: `0000` = 0, `002d` = 45, `005a` = 90, `0154` = 340, `0169` / `016a` = 361 / 362 (Spin Left / Right; values above 360 are modes). Only these values are known to do anything (section 6.2). The 45 / 90 / 340 Frames start a **sweep**: the Head oscillates back and forth on its own after the Frames stop (`[observed]`, about that angular range; the sweep's centre is `[untested]`). They are not go-to positions.
- **Go to 0 degrees** turns until the Head's physical 0 degree mark lines up with its housing tick mark (`[observed]` from the Remote). From a Controller it ended a sweep (`[observed]`); a stand-alone Controller zero was not observed to move the Head.
- **Speed-set `08 1c 00 <newlvl>`** is what the Remote sends when its speed level changes. Its effect on the Head is not established: from a Controller no change was visible (`[observed]`). The level that matters for motion is the one in the jog Frames' speed bytes.
- Pressing Speed Down at `17` or Speed Up at `5f` still sends the Frame with the same level (`[wire]`).

## 5. Controller send procedure

**Status: Normative (the Remote's timing); tolerances in section 6.**

| Situation | What the Remote sends | Tag |
|---|---|---|
| Idle | Nothing. No power-up, plug-in or keep-alive traffic. | `[wire]` |
| Jog or diagonal held | The same Frame every about 49.7 ms for as long as it is held. A tap is 2 to 6 Frames. | `[wire]` |
| Release | 20 Stop Frames, every about 49.7 ms, then silence. | `[wire]` |
| Direction change through the stick's centre | 20 Stop Frames between the two directions. | `[wire]` |
| Direction change around the stick's edge (no centre crossing) | Cardinal Frames switch directly with no Stop and no diagonal Frames. | `[wire]` |
| Speed Up / Down, Spin, Go to 0 degrees | 20 Frames at the same spacing, no Stop Frame after. Presses closer together than 20 Frames queue and send 40 or 60 back to back. | `[wire]` |
| Sweep (45 / 90 / 340) | 40 Frames, then silence. A repeat press sends nothing. | `[wire]` |

The Remote keeps its speed level across an unplug of at least 10 s (`[wire]`), so a Controller must hold the level itself.

A Controller that drives the Head as the Remote does:

1. Idle silently.
2. While a movement is requested, send its Frame every 49.7 ms.
3. On release, send 20 Stop Frames at the same spacing.
4. For `08 03` commands, send 20 Frames (40 for a sweep), then go silent.
5. To end a sweep or Spin, send the Go to 0 degrees Frame (or a jog); Stop Frames do not end them (section 6.2).

## 6. Head behaviour

**Status: Informative.** These are tolerances of one Head, observed by a Controller in the probe of 2026-10-01 (56 steps, `captures/2026-10-01-probe`). The Controller was the isolated RS-485 port of section 7, Head on M, Remote unplugged, Frames repeating every 49.7 ms. Motion was judged by the operator by eye.

### 6.1 Frames and addressing

- `[observed]` The Head acts only on address `01`. Address `02` produced no motion. Other addresses (`00`, `ff`) are `[untested]`.
- `[observed]` Speed values outside the Remote's levels move the Head (`10`, `1c`, `4f`, `6f`). Speed `00` does not move it. Whether a given value is faster or slower than another was too hard to judge by eye, so speed to angular rate is `[untested]`.
- `[observed]` Jog Frames from a Controller moved the Head with no Sleeve load, no bias resistor, no Remote ever plugged in, no keep-alive, and after a Head power-cycle and 30 s of silence. All four diagonals moved the Head, tilt subtly at level `4f`. The Remote's own diagonals looked inconsistent to the operator (not instrumented).

### 6.2 Stopping

- `[observed]` **The Head has its own dead-man.** In 12-frame and 30-frame jogs it moved while Frames arrived and stopped by itself about a second after they ceased. A 3-frame jog at the lowest speed (`17`) showed no visible motion.
- `[observed]` **One Stop Frame is enough** to stop a jog.
- `[observed]` **Sweeps and Spin are ended by the Go to 0 degrees Frame or by a jog. Stop Frames do not end them.** A repeat press of a sweep button on the Remote neither sends anything nor stops the sweep.
- `[observed]` The `08 03` command accepts only 0, 45, 90, 340 and Spin 361. 5, 30, 180 and 363 were ignored: **there is no arbitrary go-to-angle.** `[untested]` Other values above 360 beyond 363.
- `[observed]` Sweeps (45 / 90 / 340) and Spin Left worked from a Controller with 40 and 20 Frames respectively. `[untested]` Fewer Frames; Spin Right from a Controller.

### 6.3 Replies and unknown commands

- `[observed]` No Head reply at any time across all 56 probe steps (driver released after each burst), and no echo. A transmit-only Controller fits.
- `[observed]` Pelco position queries (`51`, `53`) and Set Pan Position at zero (`4b`) produced no motion and no reply. See Appendix A.

## 7. Drive-circuit guidance

**Status: Informative.** No circuit is specified. This section records what was measured and what was proven.

**The one proven configuration.** The isolated Waveshare USB TO RS232/485/TTL adapter's RS-485 port, bare: A+ to Ring 2, B- to Ring 1, GND to Tip, hardware automatic direction control, Head on M, no Sleeve load, no bias, no keep-alive. `[observed]` The Head moved and took no damage. `[wire]` At the Head the idle levels were about 4.9 V (Ring 1) and 6.2 V (Ring 2) with the driver released, and a driven swing of about 1.1 V to over 7.5 V (the Capture's clip), differential about -6.4 V to +5.7 V (`captures/2026-09-30-inject`).

**Requirements implied by the measurements.**

- The Head pulls each line up through about 9 kΩ from about 5.6 V, so a driver must hold the lines and any series resistor must be well under 1 kΩ. A driver must not push a line above about 5.6 V unless it is the only driver on that line.
- The Remote drives rail to rail from the Sleeve level with the driver always on; the proven Controller releases the bus between bytes (hardware auto-direction) and still worked.
- A Controller needs only to transmit.

**Bring-up caution.** For a first connection of a different design, limit current with a series resistor per signal line and keep a hand on the Head's power. The proven configuration used none; the value is a suggestion.

**Untested.** Sleeve power; a 3.3 V transceiver; a non-isolated transceiver; DE held high on a custom board; series resistance; a plug that actuates no jack switch; Head on A. A 1 kΩ from Ring 1 to Tip and a 470 Ω Sleeve load were tried with the Head tilt at its upper limit, so those runs showed no motion and prove nothing either way.

## 8. Not covered

Gathered `[untested]` items, so a builder does not assume them:

- Speed level to angular rate; whether a speed-set Frame affects the Head.
- Head on A; Controller power from the Sleeve beyond 12 mA; 3.3 V, non-isolated, custom DE-held-high and series-resistance drives; a plug that actuates no jack switch.
- Addresses other than `01` and `02`.
- Sweep centre (0 or current position); `08 03` values above 363; fewer than 20 / 40 Frames for `08 03`; Spin Right from a Controller; a stand-alone Go to 0 degrees from a Controller.
- A Speed press mid-jog; two buttons at once; the Head's response to Remote-sent diagonals (inconsistent, not instrumented).
- Pelco absolute pan to a non-zero angle, presets and the other Pelco commands (Appendix A); the Head's behaviour at its travel limits.
- How the Remote ends a Spin, and whether it sends anything when the Head stops (not characterised, by decision).

## Appendix A. Pelco-D divergence

**Status: Informative.** The Frame looks like Pelco-D: `ff` sync, address, two command bytes, two data bytes, sum checksum. The framing is wire-compatible with Pelco-D; **the commands are not**. Do not assume a Pelco-D library works unmodified.

| Item | Pelco-D | MP101W |
|---|---|---|
| Serial settings | device dependent | 9600 8N1 |
| Checksum | sum of bytes 2..6 mod 256 | same |
| Direction bits in `cmd2` | Up `08`, Down `10`, Left `04`, Right `02` | Up `10`, Down `08`, Left `02`, Right `04` (both axes' bits swapped) |
| Speed bytes | `00` to `3f` (`40` turbo pan); `00` is very slow | Remote uses `17` to `5f` in steps of 8; `00` does not move the Head; `4f` and `6f` accepted |
| Diagonals | combined bits, `data1` pan speed, `data2` tilt speed | same layout |
| Extended / special commands | `cmd2` odd, `cmd1` a sub-opcode (`03` preset, `4b` pan position, `51` query) | `cmd1 = 08`; `cmd2 = 03` (odd) and `1c` (even); the angle / mode / speed-set family has no Pelco counterpart |
| Replies | defined by the standard (4-, 7-, 18-byte) | none, ever |
| Address | selects one of many devices | `01` only (`02` ignored) |
| Dead-man | about 15 s runaway protect | Head stops about 1 s after Frames cease |
| Stop | direction bits off | `ff 01 00 00 00 00 01`; does not end sweeps or Spin |

**Pelco commands tried.** Position queries `ff 01 00 51 00 00 52` and `ff 01 00 53 00 00 54`: no motion, no reply. Set Pan Position zero `ff 01 00 4b 00 00 4c`: no motion reported (the Head was not at its zero mark). `[observed]`.

**Pelco commands untested.** Set Pan Position to a non-zero angle (`4b`, hundredths of a degree; moderate risk, as its bits resemble Down+Left under the MP101W's bit convention), Set Tilt Position `4d`, presets `03` / `05` / `07`, Query `45`, Magnification `61`, Device Type `6b`, pattern / zone / scan. The Head ignores Pelco position queries and set-pan-zero, so these are unlikely to help.

**Do not send** Pelco commands that change device configuration or enter firmware modes (`57`, `69`, `67`, `65`, `29`, and presets `5a` to `5e`). A write here could change the link or persistent limits with no way to read state back. Background and sources: [docs/research/go-to-angle-candidates.md](research/go-to-angle-candidates.md).

## Appendix B. Evidence

**Status: Informative.** Each manifest lists the files, wiring and method. Capture directories are in [captures/](../captures/).

| Spec section | Evidence |
|---|---|
| 2.1 to 2.3 conductors, levels, Sleeve | `captures/2026-09-30-electrical` (Head alone and Remote-connected Captures, pull-up, Sleeve and Remote current measurements; recorded in the electrical-characterisation ticket) |
| 3 framing; 4 commands (jogs, Stop, Speed Up / Down, Spin, Go to 0) | `captures/2026-09-29-tap/manifest.md` (Tap log corpus, 2700+ Frames), checked against the wire in `captures/2026-09-30-cross-check` for Speed Up, Speed Down, Jog Right tap, Jog Up hold, Spin Left and Go to 0 degrees (identical Frames, 49.7 ms spacing, stray tap-side bytes only on the tap) |
| 4 diagonals; 5 stick behaviour | `captures/2026-09-30-joystick/manifest.md` (Tap log only; not cross-checked on the wire) |
| 4 sweeps; 5 sweep Frame counts | `captures/2026-10-01-sweeps/manifest.md` (Wire log, 180 Frames, 0 stray bytes) |
| 2.4, 6, 7 Controller behaviour | `captures/2026-09-30-inject/manifest.md` (first Controller injection, bare RS-485), `captures/2026-10-01-probe/manifest.md` (56 probe steps) |
| Superseded | `captures/2026-09-early-clipped/` contains clipped Labrador snapshots; the beginnings are cut off and the bytes cannot be decoded from them. [docs/findings.md](findings.md) is the starting snapshot and is superseded by this spec. |

Tap-side frames were checked against the wire for six actions; the tap showed 1 to 5 stray bytes at the start of 5 of 6 bursts that the wire did not, so the wire is authoritative where they differ.

## Appendix C. Demonstration tools

**Status: Informative.** The scripts in [tools/](../tools/) demonstrate the protocol; they are **not a supported library** and are not needed to read this spec.

| Script | Purpose |
|---|---|
| `send_frames.py`, `probe_frames.py`, `run_probe_plan.py` | Send Remote-style Frames from a Controller; probe the Head with scripted plans. |
| `tap_log.py`, `tap_frames.py` | Record a Tap log or Wire log; parse it into Frames and bursts. |
| `analyze_capture.py`, `cross_check.py`, `compare_capture.py` | Analyse Labrador Captures; compare a Capture against a Tap log. |
