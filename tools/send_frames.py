#!/usr/bin/env python3
"""Send Remote-style Frames to the Head from a serial port (first Controller experiments).

Builds `ff 01 00 <cmd2> <pan> <tilt> <chk>` (sum checksum of bytes 1..5), repeats it every
49.7 ms like the Remote for --seconds, then sends 20 stop frames (release), also on Ctrl+C.
Defaults to the lowest speed level (0x17) and a short duration so the Head moves gently.

Usage:
  python tools/send_frames.py COM3 up --seconds 1
  python tools/send_frames.py COM3 up_left --speed 0x2f --seconds 2
  python tools/send_frames.py COM3 stop --count 5
"""
import argparse
import time

import serial

CMD2 = {"up": 0x10, "down": 0x08, "left": 0x02, "right": 0x04,
        "up_left": 0x12, "up_right": 0x14, "down_left": 0x0A, "down_right": 0x0C, "stop": 0x00}
PERIOD_S = 0.0497


def frame(cmd2, speed):
    pan = speed if cmd2 & 0x06 else 0
    tilt = speed if cmd2 & 0x18 else 0
    body = [0x01, 0x00, cmd2, pan, tilt]
    return bytes([0xFF, *body, sum(body) & 0xFF])


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("port")
    ap.add_argument("direction", choices=sorted(CMD2))
    ap.add_argument("--speed", type=lambda s: int(s, 0), default=0x17, help="speed level 0x17..0x5f")
    ap.add_argument("--seconds", type=float, default=1.0, help="how long to send the direction frame")
    ap.add_argument("--count", type=int, default=20, help="frames to send for 'stop'")
    args = ap.parse_args()
    if not 0x17 <= args.speed <= 0x5F:
        ap.error("speed must be 0x17..0x5f")

    port = serial.Serial(args.port, 9600, 8, "N", 1)
    stop = frame(0, 0)

    def burst(data, duration=None, count=None):
        start, n = time.perf_counter(), 0
        while (count is None or n < count) and (duration is None or time.perf_counter() - start < duration):
            port.write(data)
            port.flush()
            n += 1
            time.sleep(max(0.0, start + n * PERIOD_S - time.perf_counter()))
        return n

    try:
        if args.direction == "stop":
            print(f"sent {burst(stop, count=args.count)} x {stop.hex(' ')}")
        else:
            data = frame(CMD2[args.direction], args.speed)
            print(f"sending {data.hex(' ')} for {args.seconds} s")
            print(f"sent {burst(data, duration=args.seconds)} frames")
    finally:
        if args.direction != "stop":
            print(f"release: sent {burst(stop, count=20)} x {stop.hex(' ')}")
        port.close()


if __name__ == "__main__":
    main()
