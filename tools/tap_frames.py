#!/usr/bin/env python3
"""Turn a raw Tap log (tap_log.py CSV) into frames and bursts.

Resyncs on 0xFF, checks the Pelco-D style checksum (sum of bytes 1..5 mod 256),
groups identical consecutive frames into runs, and groups runs into bursts
separated by a gap (default 0.4 s).

Usage:
  python tools/tap_frames.py captures/2026-09-29-tap/raw.csv
"""
import argparse
import csv

FRAME_LEN = 7


def load_bytes(path):
    rows = []
    with open(path, newline="") as f:
        for row in csv.reader(f):
            if not row or row[0].startswith("#") or row[0] == "host_s":
                continue
            rows.append((float(row[0]), int(row[1], 16)))
    return rows


def parse_frames(rows):
    frames, bad, i = [], [], 0
    while i < len(rows):
        if rows[i][1] != 0xFF:
            bad.append(rows[i])
            i += 1
            continue
        chunk = rows[i:i + FRAME_LEN]
        if len(chunk) < FRAME_LEN:
            bad.extend(chunk)
            break
        b = [x[1] for x in chunk]
        if sum(b[1:6]) & 0xFF == b[6]:
            frames.append((chunk[-1][0], bytes(b)))
            i += FRAME_LEN
        else:
            bad.append(rows[i])
            i += 1
    return frames, bad


def runs(frames):
    out = []
    for t, f in frames:
        if out and out[-1]["frame"] == f:
            out[-1]["n"] += 1
            out[-1]["t_end"] = t
        else:
            out.append({"frame": f, "n": 1, "t_start": t, "t_end": t})
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("raw")
    ap.add_argument("--gap", type=float, default=0.4)
    args = ap.parse_args()

    frames, bad = parse_frames(load_bytes(args.raw))
    print(f"{len(frames)} frames, {len(bad)} stray/bad bytes")
    prev_end = None
    burst = 0
    for r in runs(frames):
        if prev_end is None or r["t_start"] - prev_end > args.gap:
            burst += 1
            print(f"--- burst {burst} @ {r['t_start']:.3f}s")
        prev_end = r["t_end"]
        print(f"  {r['t_start']:9.3f}s  {r['n']:3d} x {r['frame'].hex(' ')}")
    for t, b in bad[:20]:
        print(f"  bad byte {b:02x} @ {t:.3f}s")


if __name__ == "__main__":
    main()
