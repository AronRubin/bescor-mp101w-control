#!/usr/bin/env python3
"""Run a Head probe plan with spoken prompts so the operator can watch each step.

Plan file lines: "label|probe_frames arguments after the port|spoken text". For each step the
runner speaks "Step n of N. <text>", waits --lead seconds, runs tools/probe_frames.py with the
arguments (plus --label), prints its output, then speaks "Step n finished". Probe results are
appended to --log. Ctrl+C aborts the current step (probe_frames sends 5 stop frames).

Usage:
  python tools/run_probe_plan.py COM3 captures/2026-10-01-probe/plan_2a.txt --log captures/2026-10-01-probe/probe.csv
"""
import argparse
import pathlib
import shlex
import subprocess
import sys
import time

from tap_log import start_speaker

PROBE = pathlib.Path(__file__).with_name("probe_frames.py")


def load_plan(path):
    steps = []
    with open(path) as f:
        for line in f:
            if line.strip() and not line.startswith("#"):
                label, args, text = (p.strip() for p in line.split("|", 2))
                steps.append((label, shlex.split(args), text))
    return steps


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("port")
    ap.add_argument("plan")
    ap.add_argument("--log", required=True)
    ap.add_argument("--lead", type=float, default=4.0, help="seconds between the prompt and the first frame")
    args = ap.parse_args()

    steps = load_plan(args.plan)
    speaker = start_speaker()

    def say(text):
        print(f">>> {text}", flush=True)
        speaker.stdin.write(text + "\n")
        speaker.stdin.flush()

    try:
        for n, (label, probe_args, text) in enumerate(steps, 1):
            say(f"Step {n} of {len(steps)}. {text}")
            time.sleep(args.lead)
            subprocess.run([sys.executable, str(PROBE), args.port, *probe_args, "--label", label, "--log", args.log])
            say(f"Step {n} finished")
            time.sleep(1.0)
        say("Plan finished")
    finally:
        speaker.stdin.close()
        speaker.wait()


if __name__ == "__main__":
    main()
