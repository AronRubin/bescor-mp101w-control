# bescor-mp101w-control

Reverse engineering the wired TRRS link between the Bescor MP101W pan/tilt head and its remote, toward a spec and controller design for wired (USB/Ethernet) software control.

## The spec

**[docs/spec.md](docs/spec.md)** is the authoritative description of the link. In short: RS-485 on the TRRS jack (Ring 2 = A, Ring 1 = B, Tip = ground), 9600 8N1, seven-byte frames `ff 01 cmd1 cmd2 data1 data2 chk` (sum checksum), jogs repeating about every 50 ms while held with 20 stop frames on release, plus zero, sweep (45 / 90 / 340 degrees) and Spin frames. The Head never replies, so a Controller only transmits. It looks like Pelco-D but its commands are not Pelco-D.

## Contents

- [docs/findings.md](docs/findings.md) — starting evidence (superseded by the spec)
- [CONTEXT.md](CONTEXT.md) — glossary
- [captures/](captures/) — raw Labrador captures
- [tools/analyze_capture.py](tools/analyze_capture.py) — exploratory analyzer for Labrador CSVs (edges, bit period, bitstream, candidate UART decodes)
- Planning: the GitHub issue labelled `wayfinder:map`
