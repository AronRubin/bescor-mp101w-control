# Research: the Remote's ICs and what they imply electrically

Resolves [Identify the Remote ICs and what they imply electrically](https://github.com/AronRubin/bescor-mp101w-control/issues/3). Inputs: the teardown ([resolution](https://github.com/AronRubin/bescor-mp101w-control/issues/2#issuecomment-5895786080), photos in `docs/teardown/`) and [findings.md](../docs/findings.md).

Evidence labels: **[M]** measured on our hardware · **[D]** datasheet fact · **[I]** inference (confidence given).

## Sources

- **S1**: Shanghai Belling, *BL3085(I47) datasheet* V1.1 (Belling document, mirrored at <https://evelta.com/content/datasheets/359-BL3085(I47).pdf>). This is the exact part: the marking `BL3085` / `I474200T` matches the ordering format `BL3085` / `I47SSSSS` on S1 p.2.
- **S2**: Shanghai Belling, *BL3085B datasheet* V1.3, <https://www.belling.com.cn/media/file_object/bel_product/BL3085B/datasheet/BL3085B_V1.3_en.pdf>. A sibling part, used for cross-checking only.
- **S3**: LCSC listing for BL3085 (I47), C2960453, <https://www.lcsc.com/product-detail/RS-485-RS-422-ICs_BL-Shanghai-Belling-BL3085-I47_C2960453.html>.
- **S4**: Beken BK2461 product page, <https://www.bekencorp.com/en/goods/detail/cid/6.html>. "RF SOC chip, which embedded the newest FLIP51 processor". The full datasheet was not retrievable from a first-party source.

## 1. BL3085 (I47): the part at the jack

| Parameter | Value | Source |
|---|---|---|
| Type | Half-duplex RS-485 transceiver, 1 driver + 1 receiver, slew-limited, true fail-safe receiver | [D] S1 p.1 |
| Pinout | 1 RO, 2 /RE, 3 DE, 4 DI, 5 GND, 6 **A** (non-inv), 7 **B** (inv), 8 VCC | [D] S1 p.2 |
| Recommended VCC | **4.5–5.5 V** ("+5V working voltage") | [D] S1 p.1, p.5 |
| Absolute max VCC | **+7 V** | [D] S1 p.4 |
| A/B abs max (driver out / receiver in) | ±13 V | [D] S1 p.4 |
| Differential output, no load (VOD1) | = VCC | [D] S1 p.5 |
| Differential output, 27 Ω load (VOD2) | ≥ 1.5 V | [D] S1 p.5 |
| Driver short-circuit current (A shorted to B) | ±100 mA max | [D] S1 p.5 |
| DI/DE//RE logic thresholds | VIH 2.0 V, VIL 0.8 V | [D] S1 p.5 |
| Receiver threshold | −200 to −50 mV; open/shorted inputs → RO = 1 | [D] S1 p.4–5 |
| Receiver input resistance | **96 kΩ** (1/8 unit load); input current 125 µA at 12 V with VCC = 0 or 5.25 V | [D] S1 p.5–6 |
| Max data rate | 500 kbps; driver rise/fall 420–900 ns | [D] S1 p.7 |
| ESD | ±15 kV IEC 61000-4-2 contact | [D] S1 p.1 |

The BL3085**B** (S2) is a different, 250 kbps part. Everything above applies to the I47 part actually fitted.

## 2. What the observed voltages imply

- **The transceiver runs from the Sleeve, above its rating.** [I, high]
  - [M] With the Remote connected at idle, Ring 2 (A) sits at ~6.0–6.2 V and Ring 1 (B) at ~0 V.
  - [M] The Head alone pulls both lines up to only ~5.6 V, so the Head cannot be what lifts Ring 2 above 6 V. The Remote's driver must be sourcing it.
  - [D] An unloaded driver output swings up to about VCC.
  - So the BL3085's VCC is at least ~6.0 V, which is essentially the Sleeve (~6.1 V) with at most a very small drop.
  - That is above the 5.5 V recommended maximum but under the 7 V absolute maximum. A Head supply surge could approach the limit. **Verify**: measure pin 8 relative to pin 5 while the Remote is plugged in (belongs on [Characterise the wired link electrically](https://github.com/AronRubin/bescor-mp101w-control/issues/8)).
- **The Ring 2 dips (~6 V → ~5.7 V) are probably Sleeve sag, not the Head signalling.** [I, medium]
  - If VCC is the Sleeve, the driven-high level on A follows VCC.
  - Periodic loads in the Remote would pull the Sleeve down, and Ring 2 with it. Candidates: 2.4 GHz TX bursts, LED multiplexing, the DC-DC converter.
  - **Test**: scope the Sleeve and Ring 2 together. If both dip in step, it's supply sag.
- **The Head side** [I, medium]
  - Both lines sit at ~5.6 V with the Remote absent. That fits pull-up resistors on A and B to a rail about 0.5 V below the Sleeve (e.g. through a diode).
  - Equal pull-ups give A − B ≈ 0. A true fail-safe RS-485 receiver would read that as idle (1), so the Head sees "no traffic" when nothing is plugged in.
  - This suggests the Head contains an RS-485 receiver with pull-up bias. The pull-up value is unknown and belongs on the electrical-characterisation ticket.
- **Idle polarity** [M + D, high]
  - A (Ring 2) above B (Ring 1) gives A − B > 0, so the receiver outputs 1. That is UART mark/idle.
  - The data therefore follows standard polarity: DI = UART TX, a 1 drives Ring 2 high, and the start bit (0) pulls Ring 1 high and Ring 2 low.

## 3. The matched 19.85 kΩ Tip→Ring paths

- [M] Unpowered, Tip→Ring 1 = Tip→Ring 2 = 19.85 kΩ.
- [D] The transceiver's own input path is ~96 kΩ, with VCC = 0 as well. It cannot account for 19.85 kΩ alone.
- [I, medium] So there are external resistors from each line to GND (Tip), in parallel with the transceiver's 96 kΩ.
  - 96 kΩ ∥ R = 19.85 kΩ gives R ≈ 25 kΩ, e.g. 24 kΩ (→ 19.2 kΩ) or 24.9 kΩ (→ 19.8 kΩ).
  - Alternatively, the path could be a resistor to VCC plus the Remote's supply network to GND. But the reading was stable, and the Tip→Sleeve reading drifted as the supply charged, so a direct pull-down is more likely.
  - The candidates are among R3/R5–R9 near the BL3085 (codes not legible in the photos).
- [I, low–medium] **Purpose**: the RO pin is unconnected, so these are not receive-side fail-safe bias.
  - Most likely they hold both lines at a defined level whenever the driver is disabled or the Remote is unpowered.
  - Against the Head's pull-ups they form a divider. The Head could use that to detect that a Remote is plugged in, but this is speculative.
  - **Check**: read the resistor codes, or measure each candidate resistor out of circuit.

## 4. Direction control: the Remote is transmit-only

- [M] /RE (pin 2) and DE (pin 3) are tied; RO (pin 1) is unconnected.
- [D] With DE = 1, the driver is on and the receiver is off. With DE = 0, the driver is Hi-Z and the receiver is on, but its output goes nowhere.
- [I, high] **The Remote never listens to the wire.** Nothing in the protocol can depend on a Head→Remote reply, acknowledgement, or state report.
- [I, medium–high] **DE is held high at idle.**
  - At idle the lines sit at the full rails (~0 V and ~6 V) rather than the Head's 5.6/5.6 V pull-up level, so the driver is on.
  - The Remote probably keeps its driver enabled permanently, or at least whenever it's awake. A Controller can do the same: keep the driver enabled and idle at mark.

## 5. BK2461 and the rest of the board

- [D, S4] The BK2461 is a Beken 2.4 GHz RF SoC with an embedded 8051-class (FLIP51) processor.
  - [secondary; not verified against a first-party datasheet] 1.9–3.6 V supply, 8 KB OTP program memory, UART and I2C, a built-in debugger.
- [I, medium] **It serves the wireless path.** It sits on its own module with a 16 MHz crystal and a 6-pin header (P1) to the main board.
  - Its ≤3.6 V supply fits U1 (`PW33`, SOT-23-5 with an inductor): very likely a 3.3 V DC-DC converter for the battery rail.
- [I, medium] **U2 (TSSOP-20, marking removed) is probably the main MCU.** It would scan the buttons, drive the 12 LEDs, feed the BL3085's DI/DE, and talk to the RF module over P1.
  - This board may not be the only possible layout: the BK2461 could be the only MCU, with U2 as an LED/key driver.
- [I, medium] **`V T R G`** reads as VCC / TX / RX / GND, a 3.3 V UART header, probably U2's or the module's UART.
  - If its TX carries the same byte stream as the BL3085's DI, it gives a **logic-level tap** on the protocol (a 3.3 V USB-serial adapter can read it directly).
  - It might also be a factory programming port.
  - **Check**: continuity from `T` to BL3085 pin 4 (DI).
- The wired interface is RS-485 physically; the wireless protocol is out of scope.

## 6. Implications for the Controller's TRRS drive circuit

These are inputs to the later drive-circuit decision, not the decision itself.

- **A standard RS-485 transceiver on 5 V should be accepted by the Head.** [I, medium–high]
  - Candidates: BL3085 (I47), MAX485, MAX3085, SN75176.
  - It would drive ~0 V and ~5 V, versus the Remote's ~0 V and ~6 V. |A − B| of about 5 V is far above the ±200 mV receiver threshold.
  - Common mode sits at ~2.5 V, well inside −7 to +12 V.
  - Idle: DE = 1, DI = 1, giving Ring 2 high and Ring 1 low, as the Remote does.
- **The Controller can be powered from the Sleeve.** A 5 V LDO from the ~6.1 V Sleeve keeps the transceiver inside its 4.5–5.5 V rating. The Remote itself runs above its rating.
  - Sleeve current budget: the Remote draws some unknown current. Measure it on the electrical-characterisation ticket.
- **The Controller needs no receiver.** The Remote has none. Even so, fitting one (RO wired to the MCU) is cheap and would reveal whether the Head ever transmits.
- **Safety** (map Notes)
  - Don't drive Ring 1/Ring 2 until the Head's pull-ups and the transceiver VCC have been measured.
  - The first injection should go through series resistors of a few hundred Ω.
  - The BL3085's ±100 mA short-circuit limit is not a protection plan for the Head.

## Open items handed on

1. BL3085 pin 8 voltage while plugged in (VCC ≈ Sleeve?) → electrical characterisation.
2. Do the Sleeve and Ring 2 dip together? → electrical characterisation.
3. The Head's pull-up resistance on each line → electrical characterisation.
4. Which resistors make the 19.85 kΩ, and their values → needs a closer look at the board. Low priority.
5. Does `T` on the `V T R G` header connect to BL3085 DI? If yes, it is a logic-level capture tap → Capture method decision.
