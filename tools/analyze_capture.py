#!/usr/bin/env python3
"""Exploratory analyzer for Labrador scope CSVs (Ring 1 / Ring 2 Captures).

Turns one or two channels into edges, a fitted bit period, quantized runs, a
bitstream, and candidate async-serial decodes at every bit offset, for both
polarities. It never assumes byte boundaries.

Input: CSV with a time column then one or more voltage columns ("t, v" or
"t, CH1, CH2"). Each positional file contributes its voltage columns as
channels. Time may be reversed; it is sorted. Ring 1 = CH1 = RS-485 B,
Ring 2 = CH2 = RS-485 A.

Usage:
  python tools/analyze_capture.py captures/2026-09-early-clipped/bescor_sp_up_ch1.csv \
      captures/2026-09-early-clipped/bescor_sp_up_ch2.csv
"""
import argparse
import csv
import statistics
import sys
from dataclasses import dataclass


@dataclass
class Channel:
    name: str
    t: list
    v: list


def load_channels(path, name_prefix):
    rows = []
    with open(path, newline="") as f:
        for row in csv.reader(f):
            cells = [c.strip() for c in row if c.strip() != ""]
            try:
                rows.append([float(c) for c in cells])
            except ValueError:
                continue  # header
    if not rows:
        raise SystemExit(f"{path}: no numeric rows")
    rows.sort(key=lambda r: r[0])
    ncols = len(rows[0]) - 1
    t = [r[0] for r in rows]
    return [
        Channel(f"{name_prefix}" if ncols == 1 else f"{name_prefix}.{i + 1}", t, [r[i + 1] for r in rows])
        for i in range(ncols)
    ]


def find_edges(ch, threshold):
    """Threshold crossings as (time, rising) with linear interpolation."""
    edges = []
    state = ch.v[0] > threshold
    for i in range(1, len(ch.t)):
        now = ch.v[i] > threshold
        if now != state:
            v0, v1 = ch.v[i - 1], ch.v[i]
            frac = (threshold - v0) / (v1 - v0) if v1 != v0 else 0.5
            edges.append((ch.t[i - 1] + frac * (ch.t[i] - ch.t[i - 1]), now))
            state = now
    return edges


def fit_bit_period(durations, lo, hi):
    """Bit period (s) minimizing distance of durations to integer multiples."""
    best = None
    steps = int((hi - lo) / 0.1e-6) + 1
    for k in range(steps):
        period = lo + k * 0.1e-6
        cost = 0.0
        n = 0
        for d in durations:
            r = d / period
            if r < 0.5 or r > 12:
                continue
            cost += (r - round(r)) ** 2
            n += 1
        if n and (best is None or cost / n < best[1]):
            best = (period, cost / n)
    return best


def build_bits(edges, t_end, period, max_idle_bits):
    """Runs between edges, plus the trailing idle run to the end of the window.

    Returns (runs, bits): runs = [(level_after_edge, n_bits)], bits = [level].
    The leading partial run (before the first edge) is dropped.
    """
    runs = []
    for i in range(len(edges) - 1):
        n = max(1, round((edges[i + 1][0] - edges[i][0]) / period))
        runs.append((edges[i][1], n))
    tail = round((t_end - edges[-1][0]) / period)
    trailing = (edges[-1][1], min(max(tail, 0), max_idle_bits))
    bits = []
    for level, n in runs + [trailing]:
        bits.extend([level] * n)
    return runs, trailing, bits


def decode_frames(bits, mark, parity):
    """Greedy 8-data-bit LSB-first frames; parity in (None, 'E', 'O'); 1 stop bit."""
    seq = [1 if b == mark else 0 for b in bits]
    length = 1 + 8 + (1 if parity else 0) + 1
    results = []
    for offset in range(length):
        i, frames, errors = offset, [], 0
        while i + length <= len(seq):
            if seq[i] != 0:
                i += 1
                continue
            data = seq[i + 1:i + 9]
            ok = seq[i + length - 1] == 1
            if parity:
                ones = sum(data) + seq[i + 9]
                ok = ok and (ones % 2 == (0 if parity == "E" else 1))
            if ok:
                frames.append(sum(b << k for k, b in enumerate(data)))
                i += length
            else:
                errors += 1
                i += 1
        results.append((offset, frames, errors))
    return results


def complementarity(edges_a, edges_b, tolerance):
    """Fraction of edges in A with an opposite-direction edge in B within tolerance."""
    if not edges_a:
        return 0, 0, 0.0
    matched, offsets = 0, []
    for ta, ra in edges_a:
        nearest = min(edges_b, key=lambda e: abs(e[0] - ta), default=None)
        if nearest and nearest[1] != ra and abs(nearest[0] - ta) <= tolerance:
            matched += 1
            offsets.append(nearest[0] - ta)
    return matched, len(edges_a), (max(abs(o) for o in offsets) if offsets else 0.0)


def analyze_channel(ch, args):
    print(f"\n=== {ch.name} ===")
    print(f"samples {len(ch.t)}, window {ch.t[0] * 1e3:.3f} .. {ch.t[-1] * 1e3:.3f} ms, "
          f"sample step ~{statistics.median(b - a for a, b in zip(ch.t, ch.t[1:])) * 1e6:.1f} us, "
          f"V {min(ch.v):.2f} .. {max(ch.v):.2f}")
    edges = find_edges(ch, args.threshold)
    print(f"edges: {len(edges)} (threshold {args.threshold} V)")
    if len(edges) < 2:
        print("not enough edges")
        return edges, None
    durations = [b[0] - a[0] for a, b in zip(edges, edges[1:])]
    if args.baud:
        period, resid = 1.0 / args.baud, None
    else:
        period, resid = fit_bit_period(durations, args.bit_min_us * 1e-6, args.bit_max_us * 1e-6)
    print(f"bit period {period * 1e6:.2f} us (~{1 / period:.0f} baud)"
          + (f", rms residual {resid ** 0.5:.3f} bit" if resid is not None else " (given)"))
    runs, trailing, bits = build_bits(edges, ch.t[-1], period, args.max_idle_bits)
    print("edge-to-edge durations (us):", ", ".join(f"{d * 1e6:.0f}" for d in durations[-args.show:]))
    print("runs (bit periods):", ",".join(str(n) for _, n in runs[-args.show:]),
          f"| trailing {'high' if trailing[0] else 'low'} idle {trailing[1]} bits (window-limited)")
    for mark_name, mark in (("mark=low", False), ("mark=high", True)):
        print(f"-- polarity {mark_name}")
        stream = "".join("1" if b == mark else "0" for b in bits)
        print(f"   bits (1=mark): {stream}")
        for label, parity in (("8N1", None), ("8E1", "E"), ("8O1", "O")):
            for offset, frames, errors in decode_frames(bits, mark, parity):
                if frames and errors <= args.max_errors:
                    hexes = " ".join(f"{b:02X}" for b in frames)
                    print(f"   {label} offset {offset}: {len(frames)} frame(s), {errors} framing error(s): {hexes}")
    return edges, period


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="+", help="Labrador CSV files; each voltage column is one channel")
    ap.add_argument("--threshold", type=float, default=3.0, help="logic threshold in volts")
    ap.add_argument("--baud", type=float, help="fix the baud rate instead of fitting the bit period")
    ap.add_argument("--bit-min-us", type=float, default=80.0)
    ap.add_argument("--bit-max-us", type=float, default=130.0)
    ap.add_argument("--max-idle-bits", type=int, default=20, help="cap on trailing idle bits added")
    ap.add_argument("--max-errors", type=int, default=0, help="show decodes with at most this many framing errors")
    ap.add_argument("--show", type=int, default=24, help="how many trailing runs/durations to print")
    args = ap.parse_args()

    channels = []
    for n, path in enumerate(args.files, 1):
        channels.extend(load_channels(path, f"CH{n}" if len(args.files) > 1 else "CH"))
        channels[-1].name = f"{channels[-1].name} ({path})"

    results = [analyze_channel(ch, args) for ch in channels]

    if len(channels) >= 2 and results[0][1] and results[1][1]:
        (ea, pa), (eb, _) = results[0], results[1]
        tol = 0.5 * pa
        m1, n1, worst1 = complementarity(ea, eb, tol)
        m2, n2, worst2 = complementarity(eb, ea, tol)
        print(f"\n=== complementarity (opposite edge within {tol * 1e6:.0f} us) ===")
        print(f"{channels[0].name}: {m1}/{n1} edges matched, worst offset {worst1 * 1e6:.1f} us")
        print(f"{channels[1].name}: {m2}/{n2} edges matched, worst offset {worst2 * 1e6:.1f} us")


if __name__ == "__main__":
    sys.exit(main())
