# Wire vs Tap log cross-check, 2026-09-30

One run of `tools/cross_check.py COM3 captures/2026-09-30-cross-check`: the Tap log (DI net, `tap.csv`) recorded continuously while `labrador-cli capture` (CH1 = Ring 1, CH2 = Ring 2, GND = Sleeve, gain 4, trigger Ring 1 rising 2.5 V, pre 0.05 s) was armed once per spoken action. `events.csv` holds the host times of "armed" and "done". Compare with `python tools/compare_capture.py captures/2026-09-30-cross-check`.

| Capture | Action | Window |
|---|---|---|
| `speed_up.csv` | Speed Up once | 0.55 s |
| `speed_down.csv` | Speed Down once | 0.55 s |
| `jog_right_tap.csv` | Jog Right tap | 0.55 s |
| `jog_up_hold.csv` | Jog Up held about 1 s, released | 2.05 s |
| `spin_left.csv` | Spin Left once | 0.55 s |
| `zero_deg.csv` | 0 deg once | 0.55 s |
| (none) | 10 s hands off: the trigger never fired | |

Result: Ring 1 and Ring 2 both decode at 9600 8N1 (start bit = Ring 1 high / Ring 2 low), are bit-identical, have no framing errors, and every wire frame sequence appears unchanged at the start of the matching Tap log burst. Frame spacing is 49.7 ms on the wire.

Speed level on the Remote at the start of the run: `4f` to `57` (Speed Up), then `4f` again (Speed Down).

Tap artifact: in 5 of 6 bursts the tap also shows 1 to 5 stray bytes (`00`, `0f 3c 8c 8d`, `c0`) right after the first frame; none appear on the wire.
