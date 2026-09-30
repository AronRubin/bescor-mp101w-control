#!/usr/bin/env python3
"""Compare wire Captures (Ring 1 / Ring 2) with the Tap log from tools/cross_check.py.

Decodes each <label>.csv at 9600 8N1 from Ring 1 (start bit = Ring 1 high) and from
Ring 2 (start bit = Ring 2 low), checks they agree, splits the bytes into frames, and
looks for the same frame sequence in tap.csv between that action's armed and done events.

Usage:
  python tools/compare_capture.py captures/2026-09-30-cross-check
"""
import csv
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from tap_frames import load_bytes, parse_frames  # noqa: E402

BIT_S = 1 / 9600


def decode(t, v, start_high, thr):
    """Return [(start_time, byte)] and the count of framing errors."""
    logic = (v > thr) if start_high else (v < thr)  # True = start-bit level
    # the idle level is the stop/mark level; start bit is the opposite
    out, errs, i, n = [], 0, 0, len(t)
    edges = np.flatnonzero(logic[1:] & ~logic[:-1]) + 1
    k = 0
    while k < len(edges):
        ts = t[edges[k]]
        bits = []
        for b in range(1, 10):
            j = np.searchsorted(t, ts + (b + 0.5) * BIT_S)
            if j >= n:
                bits = None
                break
            bits.append(0 if logic[j] else 1)  # 1 = mark
        if bits is None:
            break
        if bits[8] != 1:
            errs += 1
        out.append((ts, sum(bit << i for i, bit in enumerate(bits[:8]))))
        end = ts + 9.5 * BIT_S
        k = np.searchsorted(t[edges], end, side="left")
    return out, errs


def frames_of(pairs):
    rows = [(ts, b) for ts, b in pairs]
    frames, bad = parse_frames(rows)
    return frames, bad


def main():
    d = sys.argv[1]
    events = {}
    with open(os.path.join(d, "events.csv"), newline="") as f:
        for r in csv.DictReader(f):
            events.setdefault(r["label"], {})[r["event"].split()[0]] = (float(r["host_s"]), r["event"])
    tap, _ = parse_frames(load_bytes(os.path.join(d, "tap.csv")))
    for label, ev in events.items():
        path = os.path.join(d, label + ".csv")
        print(f"=== {label}")
        lo, hi = ev["armed"][0] - 0.2, ev["done"][0] + 0.5
        window = [(t, f) for t, f in tap if lo <= t <= hi]
        print(f"  tap: {len(window)} frames in window" + (f", first {window[0][1].hex(' ')}" if window else ""))
        if not os.path.exists(path):
            print(f"  wire: no Capture ({ev['done'][1]})")
            continue
        data = np.genfromtxt(path, delimiter=",", names=True)
        t, r1, r2 = data["t"], data["CH1"], data["CH2"]
        p1, e1 = decode(t, r1, True, 3.0)
        p2, e2 = decode(t, r2, False, 3.0)
        f1, bad1 = frames_of(p1)
        f2, bad2 = frames_of(p2)
        print(f"  wire Ring 1: {len(p1)} bytes, {e1} framing errors, {len(f1)} frames, {len(bad1)} stray")
        print(f"  wire Ring 2: {len(p2)} bytes, {e2} framing errors, {len(f2)} frames, {len(bad2)} stray")
        print(f"  Ring 1 == Ring 2 bytes: {[b for _, b in p1] == [b for _, b in p2]}")
        seq = [f for _, f in f1]
        print("  frames:", sorted({f.hex(' ') for f in seq}), f"x{len(seq)}")
        tseq = [f for _, f in window]
        pos = next((i for i in range(len(tseq) - len(seq) + 1) if tseq[i:i + len(seq)] == seq), None)
        if seq and pos is None:
            print("  tap match: NONE (wire sequence not found in tap window)")
        elif seq:
            print(f"  tap match: wire sequence found at tap frame {pos} of {len(tseq)}")
        wt = np.diff([ts for ts, _ in p1[6::7]]) * 1e3 if len(p1) >= 14 else []
        if len(wt):
            print(f"  wire frame spacing (ms, end-to-end): mean {np.mean(wt):.1f} min {np.min(wt):.1f} max {np.max(wt):.1f}")
        tt = np.diff([ft for ft, _ in window]) * 1e3
        if len(tt):
            print(f"  tap frame spacing (ms): mean {np.mean(tt):.1f} (per-chunk stamps, ~2 ms resolution)")


if __name__ == "__main__":
    main()
