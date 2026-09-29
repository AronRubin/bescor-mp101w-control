# Prior-art protocols vs. the MP101W wired link

Research for issue #4. Question: does any published protocol match the Ring 1 / Ring 2 traffic in [docs/findings.md](../docs/findings.md)? Research only; no Capture was taken as part of this. Date of search: 2026-09-29.

## Bottom line

- **No published protocol matches, and no MP101W-specific protocol, teardown, patent or FCC filing was found.** Every candidate below is either ruled out by the tail or unverifiable. Confidence in "nothing public exists": medium (search engines only; FCC aggregators returned HTTP 403, so the FCC negative is unverified).
- **Pelco-D, Pelco-P and VISCA are all inconsistent with the observed tail** (a 12-interval, 20-bit window). Pelco-P and VISCA need a fixed last-two-byte pattern (`AF xx`, `.. FF`) that cannot be produced by these bits under either polarity. Pelco-D cannot be excluded arithmetically, but two facts count against it (below). Confidence: high for Pelco-P and VISCA, medium for Pelco-D.
- **The tail decodes as two back-to-back valid 8N1 bytes under the polarity that matches the observed idle level: `0x47 0x6C`** (Ring 1 low = mark, Ring 2 high = mark). This reproduces the byte pair the findings file discarded, and it now has a stated alignment argument. It is a hypothesis: byte alignment rests on the assumption that the last edge ends the frame and the line then idles. Confidence that it is really 8N1 at ~9600: low to medium (coincidence probability about 1 in 8, see working).
- **Speed Up and Speed Down have identical tails.** If the last byte were a checksum over the command bytes it would differ between the two. So `0x6C` is unlikely to be a sum/XOR checksum over a frame whose command bytes differ; it looks more like a constant trailer, ID or address bytes, or a checksum that happens to cancel. Confidence: medium.
- The older MP-101 / MP-360 are passive contact closures (a direction line per axis plus a speed line); there is no protocol there to reuse. The wireless side is a Beken BK2461-family 2.4 GHz UART transparent link, whose datasheet governs the RF hop, not the wired bytes.

Candidate worth testing first: **the 8N1 `0x47 0x6C` hypothesis itself**, by capturing a full burst with idle before and after (issue's Capture definition) and checking for a leading byte pattern at 9600 8N1 (Pelco-D would show a `0xFF` sync as a 1-bit start pulse followed by at least 9 bit periods of mark). Second, test whether the two trailing bytes are constant across all commands.

## Working: decoding the tail

Input (findings.md, Speed Up tail, in bit periods, time order): `1,1,3,3,1,1,1,3,2,1,2,1`. Thirteen edges, first is a fall on Ring 1 and the last is a fall on Ring 1 (edge list in findings.md). Sum of intervals is 20 bit periods (2.072 ms at 104.17 µs, matching the 2.072 ms measured from -11.972 to -9.900 ms).

Levels: after each edge Ring 1 alternates; after the last edge Ring 1 is low and stays low (idle, per the Ring 1 row of the idle table in findings.md). So the intervals, in order, have Ring 1 level `L,H,L,H,L,H,L,H,L,H,L,H`, then idle L.

Assumptions (state them, they are not proven): the last edge ends the frame; the line then idles for at least one bit; UART framing is start = 0, 8 data bits LSB first, stop = 1, idle = 1; the Speed Down tail (same intervals) behaves the same.

**Polarity P1: Ring 1 low = mark (1).** This matches the observed idle (Ring 1 low, Ring 2 high) and a non-inverting transceiver driver where DI = 1 gives A high / B low (the A/B naming used by most transceiver vendors; see the RS-485 note below).

```
bit periods:  1  1  3    3    1  1  1  3    2   1  2   1  | idle
Ring 1:       L  H  L    H    L  H  L  H    L   H  L   H  | L...
P1 bit:       1  0  111  000  1  0  1  000  11  0  11  0  | 1 1 1
position:     1  2  3-5  6-8  9  10 11 12-14 15-16 17 18-19 20 | 21+
```

Bit string (positions 1 to 20, then idle): `1 0 1 1 1 0 0 0 1 0 1 0 0 0 1 1 0 1 1 0` then `1...`

- Final character: start at position 12 (0, valid), data at positions 13 to 20 LSB first = `0 0 1 1 0 1 1 0` = **0x6C**, stop at position 21 = first idle bit (1, valid, merged into idle).
- Preceding character: start at position 2 (0, valid), data at positions 3 to 10 = `1 1 1 0 0 0 1 0` = **0x47**, stop at position 11 (1, valid), immediately followed by the next start bit with no gap.
- Position 1 (`1`) is the previous character's stop bit or idle.
- If the UART were MSB-first (unusual), the bytes would be `0xE2 0x36`.
- Coincidence check: the independent framing constraints are start(2)=0, stop(11)=1, start(12)=0 (the final stop is satisfied by construction because the line idles). That is 3 constraints, so about a 1 in 8 chance a random 20-bit window frames cleanly. Weak to moderate evidence, not proof.

**Polarity P2: Ring 1 high = mark (1)** (bit inverted): bit string `0 1 0 0 0 1 1 1 0 1 0 1 1 1 0 0 1 0 0 1`, then the line rests at Ring 1 low = space.

- Also frames cleanly as 8N1: start(1)=0, data(2 to 9) = `1 0 0 0 1 1 1 0` = **0x71**, stop(10)=1; start(11)=0, data(12 to 19) = `1 1 1 0 0 1 0 0` = **0x27**, stop(20)=1.
- But then the idle level after the frame is space (0), which is not a UART idle. It is only plausible if the driver is released (tri-stated) after the last stop bit and the line's bias resistors pull Ring 1 low. The findings say the Remote actively drives both rings at idle, which argues against this. P2 is a fallback, not the favourite. Confidence P1 over P2: medium.

**Parity/stop variants (P1).** 8E1/8O1 (11-bit characters) would require position 11 to be a start bit; it is 1, so no. 8N2 would need two stop bits between the two characters; position 12 is a start bit, so no. 8N1 is the only simple framing that fits. (This says nothing about 9-bit multiprocessor framing or software bit-banging with different rules.)

**A/B note.** TIA-485 labels binary 1 (mark) as A negative relative to B, but most transceiver datasheets (Maxim, Intersil, ADI, TI, Linear) use the opposite naming, so "A" is the non-inverting pin that goes high for a UART mark ([Wikipedia: RS-485](https://en.wikipedia.org/wiki/RS-485), Signals section). CONTEXT.md labels Ring 2 as A (non-inverting) and Ring 1 as B, and the observed idle (Ring 2 high, Ring 1 low) then equals a UART idle-high through a vendor-convention transceiver. This is consistent with P1. (Confidence that the Remote uses a real RS-485 transceiver is a separate question; the ~19.85 kΩ matched paths and 0 V/6 V levels in findings.md are not standard 5 V RS-485 levels.)

## Candidate: Pelco-D

Format ([CommFront Pelco-D tutorial](https://www.commfront.com/pages/pelco-d-protocol-tutorial)): 7 bytes, no parity, 8 data bits, 1 stop bit, baud rate set per camera. `FF | address | cmd1 | cmd2 | data1 (pan speed 00..3F, FF = turbo) | data2 (tilt speed 00..3F) | checksum = (sum of bytes 2..6) mod 256`. Example from the same page: pan left, full speed, address 1 = `FF 01 00 04 3F 00 44`. Cameras do not reply.

Bit-level signature at 9600 8N1, mark = idle:
- Sync `FF` = start 0, eight 1s, stop 1: a 1-bit-wide space pulse followed by at least 9 bit periods (about 938 µs) of continuous mark before the next start bit. Look for this at the beginning of every burst.
- Frame length: 7 x 10 bits = 70 bit periods = 7.29 ms, back-to-back.
- Last byte = checksum, any value.

Tail test: if the tail is Pelco-D, the last byte is the checksum and the previous byte is data2. Under P1 that is checksum 0x6C, data2 0x47. Against Pelco-D:
1. Data2 (tilt speed) is specified as 00..3F in the CommFront page, and 0x47 is outside that range. (Some devices may tolerate it; this is the published range only.)
2. Speed Up and Speed Down give the same tail; a mod-256 sum changes whenever any covered byte changes, so the checksum would be expected to differ.
3. Nothing about speed up/down, 0/45/90/340 degree modes or continuous spin maps onto Pelco-D pan/tilt/zoom bits (the Remote sets a mode and a speed, not a camera zoom).
Arithmetic cannot exclude it (0x6C is a reachable checksum). Verdict: **unlikely, cannot be fully excluded until the bytes before the tail are captured.** Confidence: medium.

## Candidate: Pelco-P

Format ([CommFront Pelco-P tutorial](https://www.commfront.com/pages/pelco-p-protocol-tutorial)): 8 bytes: `A0 (STX) | address | data1 | data2 | data3 (pan speed) | data4 (tilt speed) | AF (ETX) | checksum = XOR of bytes 1..7`. Example: `A0 00 00 04 20 00 AF 2B`. The camera answers with an acknowledgement.

Bit-level signature: `AF` = start 0, then bits LSB first `1 1 1 1 0 1 0 1`, stop 1, i.e. the string `0 1 1 1 1 0 1 0 1 1` (a run of four marks, a space, a mark, a space, then mark/stop). The last two bytes must be `AF` followed by a checksum.

Tail test: the tail's longest run of marks is 3 (P1) or 3 (P2), so no 4-mark run exists, and neither candidate byte pair has `AF` in the penultimate position (P1: 0x47, P2: 0x71). **Ruled out for the tail.** Confidence: high.

## Candidate: VISCA (Sony)

Format ([Wikipedia: VISCA](https://en.wikipedia.org/wiki/VISCA_(protocol))): 9600 bit/s, 8N1, no flow control; packet = header byte (bit 7 = 1, source and destination addresses) + 1 to 14 information bytes + terminator `0xFF`. The Sony RS-232C spec text quoted in a search snippet says "9600 bps, 8 bits data, 1 start bit, 1 stop bit and non parity" ([ptzprotocols.com copy of the VISCA/RS-232C document](https://ptzprotocols.com/2%20Misc%20Protocols/Sony/ViscaProtocol.215092792.pdf); only the search snippet was read, the PDF itself did not open here).

Bit-level signature: every packet ends with a `0xFF` byte, i.e. start 0, eight marks, stop mark = a 1-bit space then at least 9 bit periods of mark. A typical Pan-tilt Drive command is 9 bytes (`8x 01 06 01 VV WW 0p 0q FF`, about 90 bit periods = 9.4 ms), recalled from general knowledge, not fetched here.

Tail test: the final character under P1 is 0x6C and under P2 is 0x27, not 0xFF; the tail also contains no run of 9 marks. **Ruled out for the tail.** Also the header (bit 7 set) plus the 0x0X hierarchy do not map onto a two-key remote. Confidence: high.

## Candidate: earlier Bescor heads (MP-101, MP-360) and CamRanger PT Hub

- The original MP-101 remote is a wired four-button switch ([frozentime.se](http://frozentime.se/cam_trig/bescor_remote.html)): a 7-pin DIN with a pin per direction plus a speed pin plus power and ground; the author drives it from a 5 V RF receiver and an Arduino by pulling direction pins. A commenter on protechy.com also says the original controller "simply tied each direction button to GND (through a resistor)" and that a PWM speed input exists ([protechy.com comments](https://protechy.com/bescor-mp-101-and-arduino-tutorial/)). **No protocol; electrically different from the MP101W link.** Confidence: high (matches the findings.md note).
- MP-360 is "an MP-101 motorized tripod head modified to rotate 360 degrees" and is driven wirelessly via the CamRanger PT Hub ([CamRanger](https://camranger.com/product/camranger-pt-hub-mp-360/)). The CamRanger to head interface is not documented in what was found; it is presumed contact-closure like the MP-101 (unverified).
- A wireless-nRF24L01 + Raspberry Pi project ([AndruePeters/bescor_mp101_controller](https://github.com/AndruePeters/bescor_mp101_controller)) and a Wii-nunchuk Arduino sketch ([theotherraycole/LANC-and-Bescor-Arduino-Control](https://github.com/theotherraycole/LANC-and-Bescor-Arduino-Control)) both drive the motor lines directly ("Only the 4 directional wires are used"); their packet format is private to that project's RF link. **Not applicable.**
- MP101W: Bescor's own product page only states it is wireless with a 200 ft range, a remote that "supports hardline operation with a wire", a 340 degree pan and +/-15 degree tilt, with a "newly designed speed control" and "digital construction" ([Bescor MP101W](https://www.bescor.com/product-page/mp101w-wirelessly-controlled-motorized-pan-head)). No protocol, connector pinout or teardown was found. No model named "MP-101WL" turned up in searches.

## Candidate: the wireless link (BK2461)

The remote's UART TX also feeds a Beken BK2461 RF module (findings.md / issue brief). What the datasheets show:

- BK2461 is a 2.4 GHz RF SoC with an embedded FLIP51 8051-compatible MCU ([BK2461 datasheet listing on alldatasheet](https://www.alldatasheet.com/html-pdf/1132247/ETC2/BK2461/1046/9/BK2461.html), search snippet). So a module using it may carry its own firmware.
- Off-the-shelf BK2461 modules are transparent UART links, half duplex, "UART communication rate 0.6 kbps to 38.4 kbps" set by AT command ([M-BK2461U datasheet on Sekorm](https://en.sekorm.com/doc/2483406.html); [H2-BK2461 manual, Scribd copy](https://www.scribd.com/document/899680532/H2-BK2461)). 9600 bit/s falls in that range. "There is no packet size limit" is stated for the H2 module.
- Implication: the RF hop is transparent, so whatever bytes the MCU emits on the wired pair are probably the same bytes sent over the air. The module datasheets define no application framing, so they do not supply the byte format. Confidence: medium (assumes the Remote uses a standard module rather than a custom firmware; the module identity is not confirmed).

## Candidate: generic Chinese RS-485 pan-tilt / OEM heads

- The ptzprotocols.com index lists Pelco (D, P, G, M, ASCII), plus TXB families and a "Chinese" section, Kalatel, Sensormatic, Vicon, Videolarm, Sony, Panasonic and others ([index](https://ptzprotocols.com/)). Only Pelco-D/P/VISCA were checked in detail here; the other protocol pages were not opened, so **those are not ruled out**, only unchecked. Most CCTV protocols start with a distinctive sync/header byte and a checksum, which the observed bits (max run of 3 marks) do not obviously show, but that is only true for the 20-bit tail.
- Searches for generic motorized pan-tilt head remotes with RS-485 and 2.4 GHz plus wired option turned up consumer and camera-slider products but no protocol documentation.

## Patents, FCC, forums (negative results)

- **FCC:** fccid.io and fcc.report returned HTTP 403 to the fetch tool, so a direct database lookup did not happen. A search-engine summary claimed no FCC ID record exists for the MP101W, but that is an unverifiable auto-generated summary and not evidence. **Unresolved.** Next step: look up the FCC ID label on the MP101W remote (or Bescor's FCC grantee code) by hand at apps.fcc.gov; if it exists, the internal photos exhibit could name the MCU and the RF module.
- **Patents:** searching for Bescor pan head remote patents returned only US 4,728,839 (Remotec, 1987, a hazardous-area pan/tilt head with potentiometer feedback; [Google Patents](https://patents.google.com/patent/US4728839A/en)), which is unrelated. No Bescor patent describing the remote protocol was found.
- **Forums / GitHub / teardowns:** searched for MP101W plus teardown, protocol, reverse engineer, TRRS, reddit, hackaday, EEVblog, diyaudio. Nothing MP101W-specific; results were the older MP-101 projects above and the DPReview thread on Bescor heads. The search for `"Bescor MP101W teardown" OR "reverse engineer" OR protocol OR TRRS` returned zero results on DuckDuckGo. No teardown of the MP101W or its Remote was found.
- The search engines used were DuckDuckGo HTML and Bing via a fetch tool; coverage of forum posts and YouTube is limited.

## What would settle it

1. Take a proper Capture (idle, full burst, idle) of Speed Up, Speed Down and at least two other buttons at 104.17 µs/bit, then run the 8N1 decode from both ends of the burst.
2. Check whether the first byte is `FF` (Pelco-D/VISCA end/sync), `A0` (Pelco-P), or something else, and whether the last two bytes are constant across buttons.
3. If the last two bytes stay `47 6C` for every button, treat them as a fixed trailer and look for the checksum earlier in the frame; if they change with the button, test sum, XOR and CRC-8 over the preceding bytes.
4. Look up the FCC ID from the Remote label.

## Sources

- Bescor MP101W product page: https://www.bescor.com/product-page/mp101w-wirelessly-controlled-motorized-pan-head
- Pelco-D format and examples (CommFront): https://www.commfront.com/pages/pelco-d-protocol-tutorial
- Pelco-P format and examples (CommFront): https://www.commfront.com/pages/pelco-p-protocol-tutorial
- VISCA overview (Wikipedia): https://en.wikipedia.org/wiki/VISCA_(protocol)
- VISCA/RS-232C control protocol (search-snippet only): https://ptzprotocols.com/2%20Misc%20Protocols/Sony/ViscaProtocol.215092792.pdf
- RS-485 A/B polarity conventions (Wikipedia): https://en.wikipedia.org/wiki/RS-485
- MP-101 remote hack (frozentime): http://frozentime.se/cam_trig/bescor_remote.html
- MP-101 and Arduino tutorial and comments (protechy): https://protechy.com/bescor-mp-101-and-arduino-tutorial/
- CamRanger PT Hub and MP-360: https://camranger.com/product/camranger-pt-hub-mp-360/
- AndruePeters/bescor_mp101_controller: https://github.com/AndruePeters/bescor_mp101_controller
- theotherraycole/LANC-and-Bescor-Arduino-Control: https://github.com/theotherraycole/LANC-and-Bescor-Arduino-Control
- M-BK2461U UART module datasheet (Sekorm): https://en.sekorm.com/doc/2483406.html
- H2-BK2461 module manual (Scribd): https://www.scribd.com/document/899680532/H2-BK2461
- BK2461 SoC datasheet listing: https://www.alldatasheet.com/html-pdf/1132247/ETC2/BK2461/1046/9/BK2461.html
- PTZ protocol collection index (ptzprotocols.com): https://ptzprotocols.com/
- US 4,728,839 (unrelated Remotec patent, negative result): https://patents.google.com/patent/US4728839A/en
- Not reachable (HTTP 403): https://fccid.io/search?q=bescor, https://fcc.report/company/Bescor-Video-Accessories-Ltd
- Standard UART framing (idle high, start low, LSB first) is used as background knowledge and was not separately fetched.
