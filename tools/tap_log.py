#!/usr/bin/env python3
"""Continuous Tap log recorder: every byte from the DI tap with a host timestamp.

Writes CSV rows "host_s,byte" (byte as two hex digits). host_s is seconds since
start on a monotonic clock; the first line is a comment with the wall-clock start.
Never stops between actions; stop with Ctrl+C or --seconds.

--cues FILE runs an operator script: lines "label|wait_s|instruction". Each cue is
printed and spoken (Windows speech) at its time and logged to <out>.events.csv as
"host_s,label"; wait_s is the time until the next cue. The log ends after the last cue.

Usage:
  python tools/tap_log.py COM3 captures/2026-09-29-tap/raw.csv --seconds 600
  python tools/tap_log.py COM3 out.csv --cues captures/2026-09-29-tap/cues2.txt
"""
import argparse
import subprocess
import time

import serial

SPEAKER = (
    "Add-Type -AssemblyName System.Speech;"
    "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer;"
    "while (($l = [Console]::In.ReadLine()) -ne $null) { $s.Speak($l) }"
)


def start_speaker():
    return subprocess.Popen(
        ["powershell", "-NoProfile", "-Command", SPEAKER],
        stdin=subprocess.PIPE,
        text=True,
    )


def load_cues(path):
    cues, at = [], 2.0
    with open(path) as f:
        for line in f:
            if not line.strip() or line.startswith("#"):
                continue
            label, wait, text = (p.strip() for p in line.split("|", 2))
            cues.append((at, label, text))
            at += float(wait)
    return cues, at


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("port")
    ap.add_argument("out")
    ap.add_argument("--baud", type=int, default=9600)
    ap.add_argument("--seconds", type=float, default=0, help="0 = until Ctrl+C")
    ap.add_argument("--cues", help="operator cue script (see module doc)")
    args = ap.parse_args()

    cues, cue_end = load_cues(args.cues) if args.cues else ([], 0)
    if args.cues:
        args.seconds = cue_end
    events = open(args.out + ".events.csv", "w", newline="") if cues else None
    speaker = start_speaker() if cues else None
    if events:
        events.write("host_s,label\n")

    port = serial.Serial(args.port, args.baud, 8, "N", 1, timeout=0.002)
    t0 = time.perf_counter()
    count = 0
    with open(args.out, "w", newline="") as f:
        f.write(f"# wall_start={time.strftime('%Y-%m-%dT%H:%M:%S%z')} port={args.port} baud={args.baud} 8N1\n")
        f.write("host_s,byte\n")
        print("logging; first cue in 2 s", flush=True)
        try:
            while not args.seconds or time.perf_counter() - t0 < args.seconds:
                while cues and time.perf_counter() - t0 >= cues[0][0]:
                    _, label, text = cues.pop(0)
                    events.write(f"{time.perf_counter() - t0:.4f},{label}\n")
                    events.flush()
                    print(f">>> {text}", flush=True)
                    speaker.stdin.write(text + "\n")
                    speaker.stdin.flush()
                data = port.read(max(1, port.in_waiting))
                if not data:
                    continue
                now = time.perf_counter() - t0
                for b in data:
                    f.write(f"{now:.4f},{b:02x}\n")
                f.flush()
                count += len(data)
        except KeyboardInterrupt:
            pass
    if events:
        events.close()
        speaker.stdin.close()
    print(f"wrote {count} bytes to {args.out}")


if __name__ == "__main__":
    main()
