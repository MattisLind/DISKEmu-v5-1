# Component sourcing / JLCPCB BOM

Inventory checked **2026-11-07** against JLCPCB's public component-detail API. The clean snapshot in [inventory-2026-11-07.json](inventory-2026-11-07.json) records each exact manufacturer part number, package, Basic/Extended class, available order quantity, price and source URL. Numbers are a snapshot, not a stock reservation.

## Files

- [bom.csv](bom.csv): complete purchasing BOM, including all nine 74F38 drivers and five removable jumper shunts.
- [jlcpcb-bom.csv](jlcpcb-bom.csv): **110 SMT components, 11 unique Basic parts and 12 unique Extended parts**. This upload BOM includes all nine SN74F38DR drivers and excludes through-hole connectors/accessories. It is not a complete assembled-board order by itself.
- [hand-assembly.csv](hand-assembly.csv): six through-hole headers/connectors and five removable shunts.
- [pcb-features.csv](pcb-features.csv): J1's Q-bus card edge and H1/H2 mounting holes. These are PCB fabrication features, not components to purchase.

There are 121 purchased items per board including accessories: 110 on the JLCPCB SMT list and 11 on the completion list. Every fitted schematic component is represented exactly once. J8 has been removed.

**The PCB still needs the previous FT2232H revision and the new footprint changes applied and routed.** Only the unused J8 footprint was removed directly from the PCB in this task. No placement/CPL file is provided, because the existing PCB placements would be wrong for the revised circuit. Check the assembly preview and connector body clearances after updating the PCB.

## Driver selection and limited stock

| References | Selection | LCSC | Available order quantity at check | Action |
| --- | --- | --- | ---: | --- |
| U6–U13, U20 | SN74F38DR, narrow SOIC-14, nine devices | [C2878705](https://jlcpcb.com/partdetail/C2878705) | 308 | Included in JLC upload BOM |
| U16 | ATF1504AS-10AU44 | [C219301](https://jlcpcb.com/partdetail/C219301) | 1 | Check/pre-order before planning a batch |
| U15 | ATF1508AS-10AU100 | [C31179](https://jlcpcb.com/partdetail/C31179) | 7 | Limited stock |
| U17 | AVR128DB48-I/PT | [C1019766](https://jlcpcb.com/partdetail/C1019766) | 14 | Limited stock |

All fitted parts now have verified LCSC numbers. The selected **SN74F38DR, C2878705**, is a 64 mA open-collector driver in TI’s 3.9 mm-wide D package, matching the existing SOIC-14 footprint. **C2878808 is SN74F38NSR**, in the wider approximately 5.3 mm NS package; it would need a different footprint. Both are actual 74F38 devices, but they are not mechanically interchangeable. The alternative is recorded separately in the inventory snapshot.

U16's generic ASL-labelled symbol has been assigned an actual standard-power **ATF1504AS-10AU44**. This is the 5 V, 10 ns, TQFP-44 AS family specified in the original project's build instructions; it is not a 3.3 V ASV part. Allow for standard-power consumption and select the matching CPLD device in the programming tool. The BOM does not substitute the slower low-power ASL variant merely because a similarly named part exists.

## Basic parts and value consolidation

All resistors are 0603, 1% Basic parts. The five values are 330 Ω, 680 Ω, 2.2 kΩ, 5.1 kΩ and 12 kΩ.

| References / selection | Purpose |
| --- | --- |
| R8–R15, R18, R20, R21: 12 kΩ, [C22790](https://jlcpcb.com/partdetail/C22790) | Common part for ordinary pull-ups/pull-downs and the FTDI reference. R11 needs the specified 12 kΩ, 1% accuracy. |
| R8/R9/R10: 12 kΩ | SD DAT1/DAT2/CMD idle bias; SPI outputs drive the actual transitions. A 12 kΩ bias lies in the usual SD 10–100 kΩ range. |
| R19: 2.2 kΩ, [C4190](https://jlcpcb.com/partdetail/C4190) | Series resistor from EEPROM Q to shared FTDI EEDATA, not a pull-up. Retains FTDI’s recommended value for contention limiting and read timing. |
| R17: 2.2 kΩ, same C4190 | Stronger UPDI pull-up for faster rising edges; reuses the required EEPROM resistor part. |
| R16: 330 Ω | UPDI series protection. |
| R5: 330 Ω | Approximately 6–8 mA through the selected green LED. |
| D1: 1206 → 0805 | Selects Basic [KT-0805G, C2297](https://jlcpcb.com/partdetail/C2297) |
| All 100 nF capacitors → 0603 | One Basic [Yageo 50 V X7R part, C14663](https://jlcpcb.com/partdetail/C14663), instead of separate 0603/0805 feeders |
| All 4.7 µF ceramics → 1206, 50 V X7R | Basic [1206B475K500NT, C29823](https://jlcpcb.com/partdetail/C29823), also used in the HP21xx project; higher voltage and larger package improve capacitance retention |
| Y1 → 12 MHz, 20 pF load crystal | Basic [X322512MSB4SI, C9002](https://jlcpcb.com/partdetail/C9002) |
| C46/C47: 27 pF → 30 pF C0G | Basic [0603CG300J500NT, C1658](https://jlcpcb.com/partdetail/C1658), matched to the selected crystal's load |

For the crystal, 30 pF per leg gives a nominal 20 pF load with approximately 5 pF effective stray capacitance. Final load-capacitor tuning depends on the routed layout and crystal/FTDI input capacitance. The crystal is passive, not a powered oscillator, despite JLC's category wording.

The USB-C CC resistors R6/R7 remain 5.1 kΩ; these are not generic bias resistors. The Q-bus 330 Ω/680 Ω network is unchanged. R20 and R21 now use 12 kΩ. R19 remains 2.2 kΩ because increasing this series resistor would slow EEPROM reads and, with R20, raise the low level seen by EEDATA. Use the reference-design value rather than treating it as an arbitrary pull-up. See the [FT2232H datasheet](https://www.ftdichip.cn/Support/Documents/DataSheets/ICs/DS_FT2232H.pdf), EEPROM interface description.

The LM1117 stays a genuine TI **LM1117MPX-3.3/NOPB**, [C9662](https://jlcpcb.com/partdetail/C9662), in the existing SOT-223 footprint. Its reel suffix does not change the circuit. It is Extended; it was not silently replaced with a Basic AMS1117 clone.

C17 and C20 use the same **22 µF, 16 V conventional tantalum, TAJB226K016RNJ, [C8020](https://jlcpcb.com/partdetail/C8020)**. This is one Extended part type for both locations. The Basic 10 µF tantalum alternative does not provide the requested 22 µF input bulk. C20 remains the LM1117 output capacitor; the selected series is listed at 2.3 Ω ESR at 100 kHz. Check regulator stability with the complete output network on hardware.

Both U19 and U22 use **SN74LVC1G07DBVR, [C7829](https://jlcpcb.com/partdetail/C7829)**. Retaining U22 therefore adds one device but no additional Extended feeder type.

## UPDI speed and ferrite beads

R17 uses 2.2 kΩ for faster open-drain rising edges, sharing the same Basic part as R19. Its low level with R16 = 330 Ω should be checked on the prototype, along with edge timing at the chosen baud rate. A 12 kΩ pull-up can work at moderate baud rates on short connections, but provides less timing margin; it is unnecessary here because 2.2 kΩ is already required. No fixed maximum baud rate is claimed without the routed board’s capacitance and measurements.

The component labelled **600R@100MHz**, between VDD and USB_PHY_3V3, is **FB1, a ferrite bead**. FB2 similarly filters the PLL supply. Their selected Basic part is Sunlord GZ2012D601TF, [C1017](https://jlcpcb.com/partdetail/C1017). The 600 Ω rating is its high-frequency impedance at 100 MHz, not its DC resistance. Its DC resistance is listed at 0.3 Ω maximum. Together with the local bypass capacitors, it attenuates supply noise reaching and leaving the USB PHY/PLL.

For a crystal, the two external capacitors contribute approximately their series combination:

```text
CL ≈ C1*C2/(C1+C2) + Cstray
```

Thus two 27 pF capacitors give 13.5 pF plus stray capacitance; with 4.5 pF stray this is an 18 pF crystal load. The earlier 27 pF / 18 pF pairing was therefore consistent. The currently sourced revision uses a 20 pF crystal and two 30 pF capacitors (15 pF + approximately 5 pF stray). Confirm the final loading against the actual routed layout.

## Why VBUS drives U22 and USB_RESET_N

U18 is self-powered from the board's 3.3 V rail. U22 senses **USB_VBUS**:

- Cable present: U22 releases RESET; R13 pulls RESET high to board 3.3 V.
- Cable absent: R12 pulls the input low; U22 holds the FT2232H in reset.
- Board unpowered with a USB cable attached: the buffer's 5.5 V-tolerant input and partial-power-down protection keep VBUS from feeding an unpowered FTDI reset/supply pin.

An RC network would only provide a startup delay. It would release RESET even when no USB host is connected and would not assert reset when a cable is unplugged while the Q-bus board remains powered. It is therefore not equivalent to this VBUS detector. U22 is retained. R12's 12 kΩ value draws approximately 0.42 mA from a nominal 5 V VBUS.

## SD connector and verified footprint

J5 is **SHOU HAN SD-CARD 11P, [C7529393](https://jlcpcb.com/partdetail/C7529393)**, a full-size push-pull SD socket. The footprint was copied byte-for-byte from:

```text
/Users/mattis_lind/hp21xx_papertape_emulator/kicad/hp21xx_papertape_emulator/
  HP21xx_Connectors.pretty/SD_SHOUHAN_SD-CARD-11P.kicad_mod
```

The copy is in `hardware/HP21xx_Connectors.pretty/` and is registered in this project's `fp-lib-table`; it has no dependency on the other repository at edit time. Its signal-pad coordinates and pin numbers were checked against SHOU HAN drawing **FP-100090 A/0**, pages 1–2 of the [manufacturer datasheet](https://datasheet.lcsc.com/datasheet/pdf/205c75655f9098343d6dd157d86292c5.pdf?productCode=C7529393).

| Pad | Connection |
| --- | --- |
| 1 | DAT3 / SPI chip select |
| 2 | CMD / MOSI |
| 3 | Ground |
| 4 | Board 3.3 V |
| 5 | Clock |
| 6 | Ground |
| 7 | DAT0 / MISO |
| 8, 9 | DAT1, DAT2, with existing pull-ups |
| 10 | Write protect → AVR PC3 |
| 11 | Card detect → AVR PC2 |
| SH, four mounting pads | Ground and switch common |

The old Hirose connector's pad 10 was CD, pad 11 was the common and pad 18 was WP. The new symbol deliberately remaps those connections. The firmware already enables internal pull-ups for PC2/PC3, so no firmware change is needed for those inputs.

Footprint SHA-256:

```text
729971344a932b04b2968b7b7a1f022dcb681cff3efc6d367c941e033577dd22  hardware/HP21xx_Connectors.pretty/SD_SHOUHAN_SD-CARD-11P.kicad_mod
```

The copied drawing's overall body envelope is approximate and retains its original notes about insulating the shaded region and checking the card stop/board edge. Signal pads and mounting features have been checked against the drawing; a physical sample remains useful for enclosure clearance.

## USB connector

The original **GCT USB4215-03-A, C37616412**, had **zero available order quantity** at the inventory check. J2 now uses **HRO TYPE-C-31-M-12, [C165948](https://jlcpcb.com/partdetail/C165948)**, also used in the HP project. The schematic uses KiCad's standard 16-contact USB2 symbol and the matching standard HRO footprint, including both CC resistors and both D+/D− contact pairs. This is a footprint change, not a drop-in replacement on the old PCB.

## Verification and regeneration

Run:

```sh
python3 scripts/generate_bom.py
```

The generator exports a temporary KiCad XML netlist, reads component sourcing fields, checks them against the snapshot, groups exact parts and writes the CSVs. It uses Python's standard library and KiCad CLI. Set `KICAD_CLI` or pass `--kicad-cli` if the executable is installed elsewhere. It does not refresh or reserve inventory; update the inventory evidence and schematic fields together before an order.

Validation performed:

- Every purchased schematic component appears once in the purchasing BOM; PCB fabrication features are separate.
- All JLC upload rows have verified part numbers, matching MPNs and sufficient available quantity for one board before assembly attrition requirements.
- Original non-connector pin-to-pin connections are preserved. SD and USB connector pin mappings were checked separately.
- J8 is absent from both schematic and PCB, and had only unconnected nets with no routed tracks.
- KiCad ERC reports 38 existing missing `cbscpe` library diagnostics and no new electrical violations. The count is lower than the previous 42 because the old USB/SD custom connectors have been replaced with available local/standard libraries.
