# Bescor MP101W wired control

Reverse engineering the wired link between the Bescor MP101W pan/tilt head and its remote, so a purpose-built controller can command the head from software.

## Devices

**Head**:
The Bescor MP101W motorized pan/tilt unit; it powers the wired link and executes commands.
_Avoid_: PT unit, base, motor unit

**Remote**:
Bescor's own handheld MP101W controller that plugs into the Head over the TRRS cable.
_Avoid_: controller, handset

**Controller**:
The device this project designs to replace the Remote on the TRRS link, commanded by a Host.
_Avoid_: remote, bridge, adapter

**Host**:
The customer software (with camera zoom) that commands the Controller over a wired USB or Ethernet connection.
_Avoid_: PC, client

## Wired link

**Tip**:
The TRRS conductor carrying ground.
_Avoid_: GND pin, sleeve

**Ring 1**:
The TRRS signal conductor next to the Tip; idles low when the Remote is connected.
_Avoid_: CH1, yellow, DATA, line A

**Ring 2**:
The TRRS signal conductor next to the Sleeve; idles high when the Remote is connected; carries the complement of Ring 1 during traffic.
_Avoid_: CH2, cyan, /DATA, line B

**Sleeve**:
The TRRS conductor on which the Head supplies ~6 V power to the Remote.
_Avoid_: VCC, supply ring

**Capture**:
A recording of Ring 1 and/or Ring 2 that spans idle before, the complete traffic of one button action, and idle after.
_Avoid_: snapshot, trace, export
