#!/usr/bin/env python3
"""Record wire Captures and a Tap log of the same Remote actions.

Reads the DI tap on a serial port continuously (same CSV as tap_log.py) while,
for each action in turn, arming `labrador-cli capture` on Ring 1 (CH1) and Ring 2
(CH2), speaking the cue once the trigger is armed, and waiting for the Capture.
Writes <outdir>/<label>.csv (+ .json) per Capture, <outdir>/tap.csv, and
<outdir>/events.csv with host times of "armed" and "done" per action.

Close the Labrador app first (the board opens in one program only).

Usage:
  python tools/cross_check.py COM3 captures/2026-09-30-cross-check
"""
import argparse
import os
import subprocess
import threading
import time

import serial

CLI = os.path.expanduser(r"~\git\Labrador\Unified_App\build\windows\cli\labrador-cli.exe")

# label, spoken instruction, post seconds, timeout seconds (0 = wait forever)
ACTIONS = [
    ("speed_up", "Press Speed Up once", 0.5, 25),
    ("speed_down", "Press Speed Down once", 0.5, 25),
    ("jog_right_tap", "Tap Jog Right once, short", 0.5, 25),
    ("jog_up_hold", "Hold Jog Up for one second, then release", 2.0, 25),
    ("spin_left", "Press Spin Left once", 0.5, 25),
    ("zero_deg", "Press zero degrees once", 0.5, 25),
    ("idle", "Hands off. Do not touch anything for ten seconds", 0.3, 10),
]

SPEAKER = (
    "Add-Type -AssemblyName System.Speech;"
    "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer;"
    "while (($l = [Console]::In.ReadLine()) -ne $null) { $s.Speak($l) }"
)


class Tap:
    def __init__(self, port, out, t0):
        self.port = serial.Serial(port, 9600, 8, "N", 1, timeout=0.002)
        self.out, self.t0, self.last = out, t0, t0
        self.stop = False
        self.thread = threading.Thread(target=self.run, daemon=True)

    def run(self):
        self.out.write("host_s,byte\n")
        while not self.stop:
            data = self.port.read(max(1, self.port.in_waiting))
            if not data:
                continue
            self.last = time.perf_counter()
            for b in data:
                self.out.write(f"{self.last - self.t0:.4f},{b:02x}\n")
            self.out.flush()

    def wait_quiet(self, seconds):
        while time.perf_counter() - self.last < seconds:
            time.sleep(0.05)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("port")
    ap.add_argument("outdir")
    ap.add_argument("--cli", default=CLI)
    ap.add_argument("--gain", default="4")
    ap.add_argument("--level", default="2.5", help="Ring 1 rising trigger level, volts")
    args = ap.parse_args()
    os.makedirs(args.outdir, exist_ok=True)

    speaker = subprocess.Popen(["powershell", "-NoProfile", "-Command", SPEAKER], stdin=subprocess.PIPE, text=True)
    t0 = time.perf_counter()
    tap_file = open(os.path.join(args.outdir, "tap.csv"), "w", newline="")
    tap_file.write(f"# wall_start={time.strftime('%Y-%m-%dT%H:%M:%S%z')} port={args.port} baud=9600 8N1\n")
    tap = Tap(args.port, tap_file, t0)
    tap.thread.start()
    events = open(os.path.join(args.outdir, "events.csv"), "w", newline="")
    events.write("host_s,label,event\n")

    try:
        for label, text, post, timeout in ACTIONS:
            out = os.path.join(args.outdir, label + ".csv")
            cmd = [args.cli, "capture", "--out", out, "--gain", args.gain,
                   "--trigger", f"ch1:rising:{args.level}", "--pre", "0.05", "--post", str(post),
                   "--timeout", str(timeout)]
            proc = subprocess.Popen(cmd, stderr=subprocess.PIPE, text=True)
            for line in proc.stderr:
                if line.startswith("armed"):
                    break
            events.write(f"{time.perf_counter() - t0:.4f},{label},armed\n")
            events.flush()
            print(f">>> {text}", flush=True)
            speaker.stdin.write(text + "\n")
            speaker.stdin.flush()
            rest = proc.stderr.read()
            code = proc.wait()
            events.write(f"{time.perf_counter() - t0:.4f},{label},done exit={code}\n")
            events.flush()
            print(f"    {label}: exit {code} {rest.strip()[-120:]}", flush=True)
            tap.wait_quiet(1.5)
            time.sleep(3)
    finally:
        tap.stop = True
        tap.thread.join()
        tap_file.close()
        events.close()
        speaker.stdin.close()


if __name__ == "__main__":
    main()
