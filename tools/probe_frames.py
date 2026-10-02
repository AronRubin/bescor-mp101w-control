#!/usr/bin/env python3
"""Send arbitrary Frames to the Head and log anything that comes back (Head probe session).

Builds `ff <addr> <cmd1> <cmd2> <d1> <d2> <chk>` (sum checksum of bytes 1..5) from the four
payload bytes given in hex, repeats it every 49.7 ms like the Remote for --repeat frames,
listens for --listen seconds with the driver released, waits --wait seconds, then sends
--stop stop frames. Everything received (any time after the first frame is written) is logged
with host timestamps to --log. Ctrl+C always sends 5 stop frames before exiting.

Usage:
  python tools/probe_frames.py COM3 "08 03 00 00" --label zero --log captures/x/probe.csv
  python tools/probe_frames.py COM3 "00 10 00 2f" --repeat 3 --wait 6 --stop 20 --label deadman
  python tools/probe_frames.py COM3 "00 51 00 00" --repeat 3 --listen 1 --stop 3 --label pelco_q_pan
"""
import argparse
import csv
import time

import serial

PERIOD_S = 0.0497
STOP_PAYLOAD = (0x00, 0x00, 0x00, 0x00)


def build(addr, payload):
    body = [addr, *payload]
    return bytes([0xFF, *body, sum(body) & 0xFF])


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("port")
    ap.add_argument("payload", help='four hex bytes "cmd1 cmd2 d1 d2"')
    ap.add_argument("--addr", type=lambda s: int(s, 0), default=1)
    ap.add_argument("--repeat", type=int, default=20, help="frames to send")
    ap.add_argument("--listen", type=float, default=0.5, help="seconds to listen after the last frame")
    ap.add_argument("--wait", type=float, default=0.0, help="extra seconds before the stop frames")
    ap.add_argument("--stop", type=int, default=0, help="stop frames to send at the end")
    ap.add_argument("--label", default="")
    ap.add_argument("--log", help="CSV to append: host_s,label,tx,rx_hex,rx_at_s")
    args = ap.parse_args()

    payload = tuple(int(b, 16) for b in args.payload.split())
    if len(payload) != 4:
        ap.error("payload needs exactly four hex bytes")
    data = build(args.addr, payload)
    stop = build(args.addr, STOP_PAYLOAD)

    port = serial.Serial(args.port, 9600, 8, "N", 1, timeout=0)
    t0 = time.perf_counter()
    rx = []

    def pause(seconds):
        end = time.perf_counter() + seconds
        while time.perf_counter() < end:
            got = port.read(port.in_waiting or 1)
            if got:
                rx.append((time.perf_counter() - t0, got))
            time.sleep(0.005)

    def send(frame, count):
        start = time.perf_counter()
        for n in range(1, count + 1):
            port.write(frame)
            port.flush()
            pause(max(0.0, start + n * PERIOD_S - time.perf_counter()))

    try:
        print(f"sending {args.repeat} x {data.hex(' ')}")
        send(data, args.repeat)
        pause(args.listen + args.wait)
        if args.stop:
            print(f"stop: {args.stop} x {stop.hex(' ')}")
            send(stop, args.stop)
            pause(args.listen)
    except KeyboardInterrupt:
        print("interrupted: sending 5 stop frames")
        send(stop, 5)
    finally:
        port.close()

    rx_hex = " ".join(chunk.hex() for _, chunk in rx)
    print(f"received: {rx_hex or 'nothing'}")
    if args.log:
        with open(args.log, "a", newline="") as f:
            first_at = f"{rx[0][0]:.3f}" if rx else ""
            csv.writer(f).writerow([f"{time.time():.3f}", args.label, data.hex(" "), rx_hex, first_at])


if __name__ == "__main__":
    main()
