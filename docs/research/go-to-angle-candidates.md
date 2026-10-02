# Go-to-angle, preset and absolute-position candidates for the MP101W

Research only. Nothing here was sent to hardware. Every protocol claim is tied to a source in [Sources](#sources); anything I inferred is labelled **(inference)**. Frame notation: `ff 01 cmd1 cmd2 d1 d2 chk`, `chk` = sum of bytes 1..5 mod 256 (all checksums below were recomputed by script; the three Remote frames `08 03 00 00 → 0c`, `08 03 01 69 → 76`, `08 03 01 6a → 77` reproduce the observed values).

## Bottom line

1. **Nothing public describes `cmd1 = 0x08`, `cmd2 = 0x03` or `0x1c`.** I found no Pelco document, Pelco-D variant, open-source library or MP-101 project that uses them. The "go-to-angle in `08 03 <hi> <lo>`" idea therefore rests only on your own captures; no external source confirms or contradicts it.
2. **The Pelco-D extended set does define absolute position (set `4B`/`4D`, query `51`/`53`) and presets (`03`/`05`/`07`)**, but its angle unit is **hundredths of a degree (0..35999)**, not whole degrees, and it puts the opcode in `cmd2` with `cmd1 = 0x00`. Your `08 03` frame has opcode `03` in `cmd2` with `cmd1 = 0x08`, and Pelco's `03` is *Set Preset*. If the Head follows Pelco numbering at all, `08 03` is not a Pelco command, so Pelco's extended set is a separate guess, not a corollary of the angle hypothesis.
3. **The best first bench step is not a probe.** Capture the Remote's own 45 / 90 / 340 buttons. That is zero-risk and settles whether the angle hypothesis (`00 2d`, `00 5a`, `01 54`) holds.
4. **Main hazard for every Pelco probe (inference):** the Remote's jog frames show `cmd2` is a bit-flag field on this Head (Up `10`, Down `08`, Left `02`, Right `04`). Pelco's extended opcodes are odd numbers that mostly have one or more of those bits set. If the Head decodes `cmd1 = 00` frames as bit flags without a "bit 0 means extended" rule, a Pelco probe can be read as a **jog**. Always follow a probe with `ff 01 00 00 00 00 01` (Stop) and keep the first injection current-limited, per `AGENTS.md`.

## 1. Pelco-D (official manual v5.2.2)

### Frame layout and conventions

Standard: `ff addr cmnd1 cmnd2 data1 data2 cksm`, checksum = 8-bit sum of bytes 2..6. Motion commands are bit-encoded in `cmnd2` (bit 0 = 0, Right, Left, Up, Down, Zoom Tele, Zoom Wide, Focus Far; Pelco numbers bit1 = Right, bit2 = Left, bit3 = Up, bit4 = Down). **Extended commands are numerically encoded: `cmnd2` always has bit 0 set (odd), `cmnd1` is a sub-opcode.** Speed: `00..3F`, `40` = turbo for pan. [S1]

Differences from the MP101W frame (from your captures):

| Item | Pelco-D | MP101W |
|---|---|---|
| Checksum | sum of bytes 2..6 mod 256 | same |
| Direction bits (`cmd2`) | Up `08`, Down `10`, Left `04`, Right `02` | Up `10`, Down `08`, Left `02`, Right `04` (both axes swapped) |
| Speed bytes | `00..3F` (+`40` turbo pan) | `17..5f` step 8 (10 levels), outside Pelco's range |
| Non-motion commands | `cmd1` is sub-opcode, `cmd2` odd | `cmd1 = 08`, `cmd2` = `03` (odd) and `1c` (**even**, so not Pelco-style numeric encoding) |
| Reply | defined (see below) | unknown |

**(inference)** Because `1c` is even, the `cmd1 = 08` family is probably decoded by `cmd1`, not by Pelco's odd/even rule. That is why I treat Pelco extended opcodes as untested on this Head, not as the same protocol with a different prefix.

### Extended commands relevant to you

All with `cmnd1 = 00` unless stated. "MP101W-layout" is the same bytes (I have no basis to change them) with the MP101W direction-bit risk noted in the last column. Frames use address `01`.

| Command | `cmnd2` | `d1 d2` | Frame (checksum worked) | Reply per spec | If Head decodes `cmd2` as MP101W flags **(inference)** |
|---|---|---|---|---|---|
| Set Preset n | `03` | `00 n` | `ff 01 00 03 00 01 05` (n=1; 01+00+03+00+01=05) | General (4 B) | Left |
| Clear Preset n | `05` | `00 n` | `ff 01 00 05 00 01 07` | General | Right |
| Call Preset n | `07` | `00 n` | `ff 01 00 07 00 01 09` | General | Left+Right (illegal combo) |
| Flip 180° (preset 33) | `07` | `00 21` | `ff 01 00 07 00 21 29` | General | as above |
| Go to Zero Pan (preset 34) | `07` | `00 22` | `ff 01 00 07 00 22 2a` | General | as above |
| Remote Reset | `0F` | `00 00` | `ff 01 00 0f 00 00 10` | General | Down+Right+Left |
| Dummy | `0D` | `00 00` | `ff 01 00 0d 00 00 0e` | General (nothing else happens) | Down+Right |
| Set Zero Position | `49` | `00 00` | `ff 01 00 49 00 00 4a` | General | Down |
| **Set Pan Position** | `4B` | pan msb, lsb | 0°: `ff 01 00 4b 00 00 4c`; 45° (4500 = `11 94`): `ff 01 00 4b 11 94 f1`; 90° (9000 = `23 28`): `ff 01 00 4b 23 28 97` | General | Down+Left |
| **Set Tilt Position** | `4D` | tilt msb, lsb | 0°: `ff 01 00 4d 00 00 4e` | General | Down+Right |
| **Query Pan Position** | `51` | `00 00` | `ff 01 00 51 00 00 52` | Extended (7 B), opcode `59` | Up |
| **Query Tilt Position** | `53` | `00 00` | `ff 01 00 53 00 00 54` | Extended (7 B), opcode `5B` | Up+Left |
| Query (model string) | `45` | `00 00` | `ff 01 00 45 00 00 46` | 18 B Query Response (ASCII model); sub-op details not read | Right |
| Query Magnification | `61` | `00 00` | `ff 01 00 61 00 00 62` | Extended, opcode `63` | **none** |
| Query Device Type | `6B` | `00 00` | `ff 01 00 6b 00 00 6c` | Extended, opcode `6D` | Down+Left |
| Pattern / zone / scan | `1F`,`21`,`23`,`1B`,`1D`,`11`,`13`, `47` | various | not worth building: no hardware reason to expect them | General | various |

Units and examples from the manual: pan/tilt value = **hundredths of a degree, 0..35999** ("hungrees"); 45° = 4500; tilt 0° = horizon, 90° = straight down, 45° above horizon = 31500. [S1]

### Reply formats (Pelco-D)

- **General response, 4 bytes:** `ff addr alarms cksm`; `cksm` = command's checksum + alarms. Manual capture: command `ff 01 00 20 00 00 21` → `ff 01 00 21`. Goto Preset 34 `ff 01 00 07 00 22 2a` → `ff 01 00 2a`. [S1]
- **Extended response, 7 bytes:** `ff addr resp1 resp2 data1 data2 cksm`, `cksm` = sum of all bytes except sync and itself. Manual capture: `Get Pan Position` `ff 01 00 51 00 00 52` → `ff 01 00 59 00 00 5a` (pan 0°). So a position reply to your `ff 01 00 51 00 00 52` would be `ff 01 00 59 <hi> <lo> <chk>` with `<hi><lo>` in hundredths of a degree. [S1]
- **Query response, 18 bytes** for `45`. [S1]
- Pelco says "all D protocol commands get replies" [S1]. A widely read tutorial says there is **no response** in Pelco-D [S2]. The two disagree; replies are device-dependent. Treat "no reply" as the expected outcome on a consumer head.

### Do not send (Pelco-D)

Verified in the command table [S1]: `57` Prepare For Download (puts a device into firmware-update state and forces 2400 baud), `69` Start Download, `67` Set Remote Baud Rate, `65` Activate Echo Mode, `29` Reset Camera Defaults, and in the preset space: set preset `5C`/`5D` (92/93, limit stops) and `5E` (94, remote reset) per the Pelco-P preset table [S3]; the D manual's Appendix E also reserves limit-stop presets near `5A` (90) [S1], so avoid the whole `5A`-`5E` range. A bad write here could change baud, set persistent limits or brick the link, with no way to read state back.

### Other notes

- Pelco equipment applies a "runaway protect" (motion commands time out in about 15 s, so continuous motion needs a refresh about every 5 s). [S1] Your Remote repeats frames every 49.7 ms during a hold (cross-check manifest), which suggests the Head may stop when frames cease **(inference)**; test that before relying on it.
- Pelco-D speed `00` means "very slow", not stop; stop is direction bits off. [S1] The Head's lowest Remote speed is `17`, so `00` may mean slow, stop, or invalid. Unknown.

## 2. Pelco-P

Frame: `A0 addr d1 d2 d3 d4 AF xor`, address is zero-indexed (camera 1 = `00`), `xor` = XOR of bytes 1..7, STX `A0` / ETX `AF`. Direction bits and speed bytes (`d3` pan, `d4` tilt) as in D; the extended table is the same opcode list in `d2` (`03` set, `05` clear, `07` go to preset; `07 00 21` flip; `07 00 22` zero pan; `09`/`0B` aux; `0F` reset; ...). Receiver replies with an ACK. [S3, S4]

Where it differs meaningfully: **the P documents I read list no absolute-position or position-query commands** (the table ends at `27`). I did not open Pelco's CM97xx P protocol manuals, so I cannot say whether a full P extension set has them. P's framing (`A0`/`AF`, XOR checksum, 8 bytes) cannot be the MP101W's; no further P work is useful. Sample-checksum caveat: the example `A0 01 00 03 00 20 AF 17` in the ADT8097 copy [S3] does not verify (I compute `2d`, or `2c` for address 00); CommFront's examples do verify. [S4]

## 3. Other protocols and projects

| Candidate | What it is | Relevance |
|---|---|---|
| **VISCA absolute position** (reference only) | Not the MP101W frame shape. `8x 01 06 02 VV WW 0Y 0Y 0Y 0Y 0Z 0Z 0Z 0Z FF`: command, category pan-tilter, absolute opcode, pan speed, tilt speed, 4 nibbles pan, 4 nibbles tilt, `FF` terminator; position inquiry returns 4+4 nibbles. | Verified only through the structure of `VISCA_set_pantilt_absolute_position` / `VISCA_get_pantilt_position` in libvisca [S5]. The numeric opcode values (`06 02`, `09 06 12`) are from memory and not checked in the sources I read. No overlap with `ff 01 .. chk`. |
| **OpenIPC "anjoy-motor"** | A "Pelco-D-style" camera motor MCU: standard direction bits (Up `08`, Down `10`, Left `04`, Right `02`), `FF 01 00 08 00 14 1D` head up, stop `FF 01 00 00 00 00 01`, plus **MCU position reports** (17 B). The MCU **ignored bare commands until a live 16-byte state stream** ran for several seconds. [S6] | Evidence that "Pelco-D-style" devices can deviate (session handshake, decimal-digit position fields). It uses standard direction bits, so it is **not** the MP101W family. Takeaway: if probes get no response, a missing handshake is a possible reason **(inference)**. |
| **OpenIPC "xm-uart"** | "XM Pelco-D variant" `C5 addr c1 c2 d1 d2 ck 5C`, ignores checksum/address, focus bits reversed vs Pelco-D names. [S6] | Shows vendor variants invert bit meanings, as the MP101W does. No `08 03` or `1c`. |
| **Bescor MP-101 (older)** | Wired remote is a four-contact DIN switch (search snippet: pin 2 right, 3 up, 5 down, 6 left, 7 ground); community projects drive the motor lines directly with PWM. [S7, S8] | Electrically different; no protocol to borrow. Your `docs/findings.md` already says this. I read only search snippets of the protechy and frozentime pages, plus the AndruePeters README (RF24 packets are its own, unrelated to the Head). |
| Kupo, other "Chinese Pelco-D variants" | Not found. The ptzprotocols.com "Chinese" folder (ADT8097, NStar, PRO22 manuals) lists only standard Pelco-P/D and mux manuals; I opened only its Pelco-P page. | Nothing with `cmd1 = 08`, `cmd2 = 03/1c`, or 16-bit angle in `d1:d2`. |

**Not found:** any protocol I could verify that uses `cmd1 = 0x08` with `cmd2 = 0x03` or `0x1c`, or any other 16-bit-angle-in-`d1:d2` scheme (Pelco's `4B`/`4D`/`59`/`5B` use that field shape, but in hundredths of a degree).

## 4. Ranked bench candidates

"Likely" = my estimate of how probable a useful result is. "Risk" covers the Head, not the host. All sequences assume the Head is unloaded, mid-travel, powered from a current-limited supply, with Stop `ff 01 00 00 00 00 01` queued after each probe and a listening window (driver released) of at least 100 ms after each frame (my suggestion; the manual's reply timing was not extracted). Check for a reply by releasing the Controller's driver immediately after the last stop bit so the Head's reply is not fought.

| # | Candidate | Frame(s) | Expected Head behaviour | Reply | Likely | Risk |
|---|---|---|---|---|---|---|
| 0 | **Capture the Remote's 45 / 90 / 340 buttons** (not a probe) | none sent | Predicted if the hypothesis holds: `ff 01 08 03 00 2d 39`, `ff 01 08 03 00 5a 66`, `ff 01 08 03 01 54 61` | n/a | n/a | **None.** Do this first. If the frames differ, rewrite candidates 1 and 2. |
| 1 | **`08 03` angle, replay of the Remote's own `0°` then one extrapolated small angle** | `ff 01 08 03 00 00 0c` (observed; from an off-zero pose, confirms it is a go-to/seek and not a jog), then `ff 01 08 03 00 05 11` (5°), then the captured 45/90 frames or `…00 2d 39` | Head seeks 0°, then moves about 5° if the field is degrees; if it moves about 0.05° (hundredths) the unit is wrong | none expected | Medium-high | **Low.** Same opcode as a Remote command. Residual: unknown travel limits, so keep to ≤ 90° first. Avoid `00 b4 c0` (180°) and `01 68 75` (360°) until limits are known. |
| 2 | **`08 03` above 360**: neighbours of the Spin pair | `ff 01 08 03 01 6b 78` (363), `ff 01 08 03 01 6c 79` (364) | **(inference)** values ≥ 361 may be mode codes (Spin Left = 361, Spin Right = 362) rather than angles; the next codes might be other modes, or ignored | none expected | Low-medium | **Low-moderate.** May start a spin; Stop ends it (the Remote's stop is the only known way). |
| 3 | **Pelco Query Pan / Tilt Position** | `ff 01 00 51 00 00 52`, then `ff 01 00 53 00 00 54`, each followed by Stop | No motion on a true Pelco head. A head with feedback replies `ff 01 00 59 hh ll cc` / `ff 01 00 5b hh ll cc`, 0.01° units | Defined (7 B) | Low-medium | **Low-moderate.** Read-only per spec, but `51` has the Up bit and `53` the Up+Left bits under the MP101W flag convention **(inference)**: a flag decoder may jog slowly until Stop. |
| 4 | **Pelco Set Pan Position (absolute)** | `ff 01 00 4b 00 00 4c` (0°) first, then `ff 01 00 4b 11 94 f1` (45°) | If honoured, pan to 45° and General reply `ff 01 00 <chk>`; unit differs from candidate 1 (hundredths vs degrees) | General | Low | **Moderate.** Flag decoder sees Down+Left and may drive diagonally; Pelco semantics also reference tilt/pan sign conventions that the MP101W inverts. |
| 5 | **Pelco presets**: Set/Call preset 1 | `ff 01 00 03 00 01 05` then move, then `ff 01 00 07 00 01 09` | Head stores and returns to a pose, if it has presets; consumer head unlikely | General | Low | **Moderate.** Writes a stored state (possibly persistent); Call has an illegal Left+Right flag combination. Never use presets 92-94 (limits / reset). |
| 6 | Pelco "does anything answer": Query Magnification | `ff 01 00 61 00 00 62` | No direction bits, so no motion under either decoder; no lens, so a reply is improbable | `ff 01 00 63 hh ll cc` if answered | Very low | **Lowest of the Pelco list.** Its only value is detecting that the Head transmits at all. |

Rank 1 is first because it is the one hypothesis your own data supports; the Pelco rows are ordered by how little they could do wrong, then by how useful a hit would be. Rows 1, 3 and 6 are the low-risk ones; row 3's risk is bounded by Stop and the stalled-motor protections you already plan.

## 5. What I could not find or verify

- **No source** for `08 03 <hi><lo>` as go-to-angle, for `08 1c` as speed-set, or for any `cmd1 = 08` usage in Pelco-D/P or a variant. The angle hypothesis, the "mode code above 360" idea and the "cmd1 selects decoding" idea are all **inference**.
- **Whether the Head transmits at all.** The Remote's receive pin is unconnected and the Remote may drive the bus continuously, so Head replies may have been masked in your existing captures **(inference)**. No source says either way for this model.
- **Pelco-P absolute position / query commands:** not in the P pages I read; I did not open Pelco's CM97xx P manuals.
- **Pelco `45` Query sub-opcode specifics** (which `cmnd1` selects model vs serial) were not read.
- **VISCA numeric opcodes** not verified from a source I opened (structure only).
- **MP101W manual** (45 / 90 / 340 sweep semantics, travel limits, speed, whether there is a limit switch or encoder): not obtained. Angle-unit and limit risks above come from that gap.
- **Pelco sample checksums in the ADT8097 copy are wrong**; I verified CommFront's and Pelco's own captures instead.
- A search-engine AI summary I saw while looking up `0x51` / `0x59` mislabelled them as `cmd1` opcodes ("zero pan position = `59`"); it contradicts the manual (query pan `51`, reply `59`, zero position `49`). I did not use it.
- The ptzprotocols.com host is a third-party archive of Pelco documents; I treated the PDF as Pelco's v5.2.2 external manual because its text carries Pelco's copyright and version, but I did not verify provenance beyond that.

## Sources

- **S1** Pelco "D" Protocol Manual, External Version 5.2.2 (20 Feb 2012), hosted at `https://www.ptzprotocols.com/1%20Pelco%20PTZ%20Protocols/D/DPProtoE.pdf` (index: `https://www.ptzprotocols.com/1%20Pelco%20PTZ%20Protocols/D/02%20Start.html`). Read: command table, §3.1-3.2, §4 responses, §5.2-5.8, §5.35, §5.37-5.47, Appendix E. Full text read via converter.
- **S2** CommFront, Pelco-D Protocol Tutorial, `https://www.commfront.com/pages/pelco-d-protocol-tutorial` (format, examples, "no response" note).
- **S3** Pelco-P intercept-dome sheet from the ADT8097 manual set, `https://www.ptzprotocols.com/2%20Misc%20Protocols/Chinese/Pelco-P.pdf` and `.../Chinese/PELCO%20P%20PROTOCOL.htm` (frame, extended table, special presets 92-99, 33, 34).
- **S4** CommFront, Pelco-P Protocol Tutorial, `https://www.commfront.com/pages/pelco-p-protocol-tutorial` (XOR checksum, verified examples, ACK note).
- **S5** libvisca (norihiro/libvisca-ip), `https://github.com/norihiro/libvisca-ip/blob/main/visca/libvisca.c` (absolute-position command structure).
- **S6** OpenIPC/motors, `https://github.com/OpenIPC/motors` and `https://raw.githubusercontent.com/OpenIPC/motors/master/anjoy-motor/Readme.md` (Anjoy frames and position reports; XM variant described in the repo's `CLAUDE.md`/`xm-uart` text via search excerpt).
- **S7** Bescor MP-101 community pages (search snippets only): `https://protechy.com/bescor-mp-101-hack-part-1/`, `http://frozentime.se/cam_trig/bescor_remote.html`.
- **S8** `https://github.com/AndruePeters/bescor_mp101_controller` (README) and Arduino forum thread `https://forum.arduino.cc/t/need-help-to-complete-project-nunchuck-bescor-mp-101-over-rs-485/407139` (Nunchuk drives MP-101 direction pins directly with PWM; RS-485 there is the poster's own link between two Nanos, not the Head's).
