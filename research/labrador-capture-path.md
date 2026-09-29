# Shortest Labrador path to a full-rate triggered Capture

Research for [issue #6](https://github.com/AronRubin/bescor-mp101w-control/issues/6). In this repo's glossary, Ring 1 idles low, Ring 2 idles high and complements Ring 1, and a Capture spans idle before, the whole button-action traffic, and idle after (`CONTEXT.md:29-42`).

## Bottom line

Use **Unified_App DAQ Record to File** today if a human can click after the button action: it can dump both analog channels from the 10 s circular buffer, at 375 kS/s per channel with `Downsample = 1`, in chronological order. It is not trigger-coupled, and its native record file has no time column; use the DAQ replay exporter for a CSV with sample or reconstructed time axis.

The **trigger + scope export** route is not enough: the single-shot trigger machinery can freeze an o1buffer snapshot, but the scope export writes only the plotted vectors, capped/decimated by the plot sampler (2048 max plotted samples), and exports OSC1/OSC2 as separate 2-column rows. The shortest upstream-worthy improvement is therefore an **Export full-rate buffer around trigger** command that reuses the existing trigger, pause, and o1buffer/DAQ writer code.

## Hardware/input range

The requested 0 to ~6.2 V signals are safe on Labrador analog inputs if probed against GND and the hardware gain is set low enough.

Evidence:

- The board docs specify oscilloscope inputs as two channels, -20 V to +20 V, 1 Mohm, 375 kSa/s per channel (`Documentation/README.md:40`; `Documentation/pinout.md:99`).
- Unified docs give the exact gain model: 0.5x..64x and full-scale about `1.65 V +/- 23.65/gain` (`Documentation/llm-guide.md:77-78`), matching the app's code comment and `scopeHalfRange()` (`Unified_App/src/ui/InstrumentFrontend.cpp:29-40`).
- The conversion code uses `frontendGain = 75/1075`, `voltage_ref = 1.65`, and divides by `scope_gain` (`Unified_App/librador/o1buffer.h:56-61`; `Unified_App/librador/o1buffer.cpp:316-325`).
- 6.2 V fits gains <=4x: at 4x, upper full-scale is about 1.65 + 23.65/4 = 7.56 V; at 8x, upper full-scale is about 4.61 V and would clip. Unified_App exposes 0.5x, 1x, 2x, 4x, 8x, 16x, 32x, 64x (`Unified_App/src/instruments/OSCControl.hpp:35-55`).
- The logic analyzer inputs tolerate 3.3/5/12 V logic (`Documentation/pinout.md:100`; `Documentation/llm-guide.md:82`), so the 6.2 V pair is also electrically plausible as logic input, but the logic decoder is not a full analog Capture path.

Recommended capture setting: **CH1 + CH2 oscilloscope**, **HW Gain = 4x or lower** (or Auto only after confirming it does not choose >4x), probes at 1x, offsets 0 V.

## Existing paths

### 1. Unified_App trigger + scope export

**Can it produce the needed file today? No.** It can help view or freeze a triggered event, but its existing export path is a display export, not a full-rate capture export.

What exists:

- Librador has a 10 s, 375 kS/s circular buffer per channel (`Unified_App/librador/o1buffer.h:9`) and a trigger state with rising/falling plus `is_single_shot` (`Unified_App/librador/o1buffer.h:19-24`).
- The Android/tile trigger UI exposes Rising, Falling, Level, and Single shot, then calls `librador_set_trigger_settings()` (`Unified_App/src/ui/android/trigger_ui.cpp:51-94`).
- Trigger search can pause a frozen buffer snapshot when a single-shot trigger is reached (`Unified_App/librador/o1buffer.cpp:390-408`, pause copy at `o1buffer.cpp:419-424`).
- The public API exposes trigger settings (`Unified_App/librador/librador.h:139`) and analog reads by sample count/rate (`librador.h:112-116`).

Blockers:

- The current scope export reads `OSC1Data->GetTime()/GetData()` and `OSC2Data->GetTime()/GetData()` and sends them separately to `DrawExportRow2Col()` (`Unified_App/src/instruments/OSCControl.hpp:414-435`). That is not one two-channel capture file.
- `DrawExportRow2Col()` is a two-column clipboard/CSV helper (`Unified_App/src/instruments/UIComponents.hpp:729-805`), and the CSV implementation just writes those two vectors (`Unified_App/src/instruments/util.cpp:702-750`).
- The plotted vectors are decimated by `OscData::CalculateSampleRate()`: `sample_rate = max_plot_samples / time_window`, with `max_plot_samples = 2048` (`Unified_App/src/instruments/OscData.hpp:1054`, `OscData.hpp:1145-1156`). For a 0.5 s Capture, that is only about 4 kS/s, far below 250 kS/s.
- The frozen single-shot snapshot is not currently wired to a command that dumps a chosen pre/post-trigger range at native sample cadence.

### 2. Unified_App DAQ Record to File / replay CSV

**Can it produce the needed file today? Yes, with a human-timed post-action click, not as an armed trigger.** This is the shortest no-code path.

Why it works:

- The DAQ widget is explicitly a buffer dump: `librador_daq` snapshots the device buffer and writes the last `duration x sample rate` samples (`Unified_App/src/instruments/DAQControl.hpp:9-14`).
- Duration is clamped to 10 s (`DAQControl.hpp:81-89`), matching the 10 s o1buffer depth (`Unified_App/librador/o1buffer.h:9`).
- With CH1+CH2 scope mode, base rate is 375 kSa/s; `numToGet = 1e3 * duration * base_rate_kSa / downsample_factor` (`DAQControl.hpp:98-106`). Set `Downsample = 1` for full-rate 375 kS/s per channel.
- The Start action can record CH1, CH2, or both and calls `librador_daq()` (`DAQControl.hpp:115-140`).
- The writer snapshots the selected o1buffers (`Unified_App/librador/usbcallhandler.cpp:912-924`) and writes CH1 then CH2 (`usbcallhandler.cpp:929-935`).
- Volts/Bits are output oldest-first by iterating `rbegin()` to `rend()` over the DAQ vector (`usbcallhandler.cpp:891-900`); the replay widget documents this as chronological order (`Unified_App/src/instruments/DAQReplay.hpp:25-35`).
- The replay tool can export a trimmed CSV (`DAQReplay.hpp:143-160`, `DAQReplay.hpp:320-350`) and can use a user-supplied time axis in kSa/s, default 375 (`DAQReplay.hpp:96-114`, `DAQReplay.hpp:427-428`).

Exact UI steps:

1. Wire Tip/GND to Labrador GND, Ring 1 to OSC1/CH1, Ring 2 to OSC2/CH2.
2. In **Inputs**, choose **CH1 + CH2 oscilloscope** (documented as both channels at 375 kSa/s in `Documentation/user-manual.md:59-68`).
3. In **Scope**, set **HW Gain** to 4x or lower; leave probe attenuation at 1x unless using a divider.
4. In **DAQ**, enable **CH1** and **CH2**, set both units to **Volts**, set **Duration** long enough for pre-idle + burst + post-idle (for example 0.6 s), and set **Downsample = 1**.
5. Press the Remote button, wait at least 200 ms idle after traffic, then within 10 s click **Start** and choose a `.txt` save path.
6. If a CSV is required, use **Open DAQ recording...**, enable **Time axis**, leave/sample-rate set to **375 kSa/s**, trim if desired, then **Export trimmed CSV...**.

Caveats: the initial DAQ record file is plain text (`CH1` header + one sample line + `CH2` header + one sample line), not CSV and no embedded sample rate/time column (`DAQReplay.hpp:25-45`). The procedure relies on the human click occurring after post-idle but before the 10 s buffer rolls over.

### 3. Desktop_Interface DAQ

**Can it produce the needed file today? No, not as one synchronized triggered two-channel Capture file.** It can record samples, and with averaging = 1 the effective rate is 375 kS/s, but it is not trigger-coupled and it records CH1/CH2 through separate actions/files.

Evidence/blockers:

- `GRAPH_SAMPLES` is only 1024 (`Desktop_Interface/desktop_settings.cpp:9`) and snapshot export writes only `GRAPH_SAMPLES` rows from the current on-screen `x`/`CH1` or `x`/`CH2` vectors (`Desktop_Interface/isodriver.cpp:1296-1325`). That confirms snapshot/export is a decimated screen-window path, not full buffer export.
- DAQ settings compute effective sample rate as `375000 / numberOfPointsSpinBox` (`Desktop_Interface/daqform.cpp:49-61`), so averaging must be set to 1 for full-rate.
- CH1 and CH2 recording are separate menu actions/files: `on_actionRecord_CH1_triggered` enables file I/O on the CH1 buffer (`Desktop_Interface/mainwindow.cpp:1945-1975`); `on_actionRecord_CH2_triggered` separately enables file I/O on CH2 (`mainwindow.cpp:1981-2002`).
- File I/O averages `m_fileIO_sampleCountPerWrite` samples, writes just the average, and has no per-sample time column (`Desktop_Interface/isobuffer.cpp:255-270`; output format at `isobuffer.cpp:240-250`).
- The file header stores averaging and device mode, not a shared trigger timestamp (`Desktop_Interface/isobuffer.cpp:13`, `isobuffer.cpp:290-304`).

Practical blocker: even if you start both recorders manually and set averaging to 1, you get manual, separate, untimestamped channel files, not one full-rate triggered Capture with guaranteed pre/post window and channel alignment.

### 4. Desktop_Interface UART decoder

**Can it produce the needed file today? No.** It may be useful as a sanity check after capture, but it is a decoder console, not a full-rate waveform/capture exporter.

Evidence/blockers:

- The UI offers baud choices 300 through 115200 with 9600 default and parity None/Even/Odd (`Desktop_Interface/mainwindow.cpp:591-626`).
- The decoder samples logic bits according to `m_sampleRate_bit / m_baudRate`, decodes bits/characters, and writes decoded text/errors to a `QPlainTextEdit` console (`Desktop_Interface/uartstyledecoder.cpp:47-66`, `uartstyledecoder.cpp:127-146`, `uartstyledecoder.h:48-53`).
- Parity is checked and can report errors (`Desktop_Interface/uartstyledecoder.cpp:237-271`).
- There is no raw two-channel analog waveform file output in this path; it consumes logic-buffer bits and updates UI text.

Use only after getting a Capture: feed the recorded Ring 1/Ring 2 edges into a separate decoder, or use Desktop UART live to confirm likely 9600-baud framing.

## Librador API / examples / bindings

- Public API exposes analog reads (`librador_get_analog_data`, `_by_rate`, `_sincelast`), DAQ (`librador_daq`), trigger settings, UART decode settings, and UART decoded-string access (`Unified_App/librador/librador.h:112-145`).
- It also exposes `librador_get_paused` / `librador_set_paused` (`librador.h:98-99`) and scope gain (`librador.h:78-81`).
- The shipped C++ demos are GUI/basic examples, not capture CLIs. `basicdemo.cpp` initializes Librador, connects USB, prints firmware info, drives PSU/signal generators, then exits; it never reads or writes capture data (`Librador_API/___librador/basicdemo/basicdemo.cpp:1-69`). `librademo` shows analog reads into a plot using `librador_get_analog_data()` (`Librador_API/___librador/librademo/mainwindow.cpp:76-88`).
- I found no first-party Python bindings in the repo (only unrelated build/helper Python files under vendored SDL/imgui/AVR tooling).

## Upstream issue/PR check

I searched upstream `espotek-org/Labrador` issues and PRs with `gh issue list` / `gh pr list` for trigger, DAQ, capture, export, and UART. Relevant hits were adjacent but not an implementation of a full-rate triggered two-channel export:

- Issues: #224 "Using Single Shot trigger pauses Logic Analyzer indefinitely", #217 "Single shot trigger not working on windows 10", #244 "Recording - where is this?", #105 "DAQ output compatible with LTspice PWL format", #121 "taking samples for both channels simultaniously via librador", #132/#126 Sigrok ideas.
- PRs: #390/#367 trigger-frequency work; #72 UART decoder refactor; #162 export current oscilloscope view as image. No open/merged PR found that adds "export full-rate buffer around trigger" or a headless capture CLI.

## Small upstream-worthy additions

### A. Export full-rate buffer around trigger in Unified_App (smallest UI addition)

Scope: add a command that arms a selected-channel rising/falling trigger, waits for the trigger, waits the requested post-trigger time, then writes one CSV/binary with `t,CH1,CH2` at native cadence from the circular buffers.

Files likely touched:

- `Unified_App/librador/o1buffer.h/.cpp`: add a safe full-rate range-copy/export primitive over `buffer` / `buffer_paused` / `buffer_daq`, preserving chronological order and ring wrap.
- `Unified_App/librador/usbcallhandler.h/.cpp`: add a dual-channel capture writer that can wait post-trigger and then copy both channel buffers atomically under `buffer_read_write_mutex`.
- `Unified_App/librador/librador.h/.cpp`: expose a small API such as `librador_export_trigger_capture(trigger_ch, trigger_type, level, pre_s, post_s, units, path)` or lower-level `librador_copy_analog_window()`.
- `Unified_App/src/instruments/OSCControl.hpp` or `DAQControl.hpp`: add UI controls/buttons for trigger capture export; optionally reuse platform save dialog.

Rough size: 200-400 LOC for robust CSV; +100-200 LOC for binary/metadata options. Risks: off-by-one/wrap ordering; making sure CH1/CH2 share the same time origin; avoiding UI stalls while writing; defining whether trigger level is raw measured volts vs display-transformed volts; not freezing too early before the requested post-trigger idle.

Agent-driven workflow: agent starts the app or a test hook, configures `pre=0.2`, `post=0.3`, `trigger=Ring1 rising/falling`, clicks **Arm capture**, asks the human to press the Remote button, then consumes the saved CSV path.

### B. Headless capture CLI over librador

Scope: a console tool for repeatable reverse engineering: configure input mode/gain, arm trigger, wait, dump CSV/binary. This is more useful for agents than UI export, but likely needs the same low-level range-copy/export API from A.

Files likely touched:

- `Unified_App/tools/labrador_capture_cli.cpp` (or `Librador_API/___librador/capturedemo/`).
- `Unified_App/CMakeLists.txt` / packaging presets to build it.
- The same `librador` API additions listed above if existing `librador_get_analog_data_by_rate()` cannot reliably express "pre N samples, trigger, post M samples".

Rough size: 250-500 LOC CLI plus 150-300 LOC API if not already added by A. Risks: device open/permissions on Windows/macOS/Linux, trigger wait timeouts, ensuring post-trigger wait does not overrun the 10 s buffer, CSV size/performance. Binary with a small JSON sidecar is safer for long captures.

Agent-driven workflow: `labrador-capture --mode scope2 --gain 4 --trigger ch1:rising:3.0 --pre 0.2 --post 0.3 --rate 375000 --out capture.csv`, then the human presses the Remote button. The agent waits for process exit and analyzes the file.

### C. MCP server wrapping the CLI

Scope: wrap B with a local MCP tool such as `arm_labrador_capture`, `capture_status`, `read_capture_metadata`, `decode_uart_candidate`.

Files likely touched:

- A small server under a tools/ or separate integration directory, plus docs/config. No Labrador core changes if B exists.

Rough size: 150-300 LOC wrapper if the CLI is stable. Risks: premature abstraction, local device permissions, long-running process lifecycle, and exposing file paths safely. This should come after a reliable CLI, not before.

Agent-driven workflow: the agent calls MCP `arm_labrador_capture(pre=0.2, post=0.3, trigger=...)`, tells the human to press the button, polls status, then receives a path/metadata for analysis.

## Recommendation

For this issue's immediate capture need, use **Unified_App DAQ Record to File** now. It is full-rate, dual-channel, and requires no code; its only weakness is manual timing. For an upstream contribution, implement **A: export full-rate buffer around trigger** first, and factor the low-level export so **B: headless CLI** can reuse it.
