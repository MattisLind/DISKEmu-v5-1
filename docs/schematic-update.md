# USB programming and capacitor revision

This revision changes the schematic only. J8 has been removed from the PCB; the remaining PCB still has the original component placement and routing; it needs an update from the schematic followed by placement, routing and DRC. A rendered copy is available in [schematic-usb-programming.pdf](schematic-usb-programming.pdf).

## Capacitors

| References | Specification | Purpose |
| --- | --- | --- |
| C17 | 22 µF, 16 V tantalum; EIA-3528-21 / Kemet B footprint | Bulk capacitance at the incoming board 5 V supply |
| C20 | 22 µF, 16 V tantalum; same footprint | LM1117 output capacitor; place directly beside U14 with a short ground return |
| C18, C21–C30, C44 | 4.7 µF, 50 V X7R ceramic, 1206 (Basic C29823) | Existing distributed supply bypass locations |
| C19, C45 | 4.7 µF, 50 V X7R ceramic, 1206 (Basic C29823) | Repurposed for FT2232H core and 3.3 V bulk bypass |
| C60, C61 | Same 4.7 µF, 50 V X7R 1206 specification | Filtered FT2232H PHY and PLL supplies |

U14 remains the LM1117MP-3.3. Select a conventional tantalum for C20 whose capacitance and ESR satisfy the regulator specification over operating conditions: at least 10 µF effective capacitance and ESR from 0.3 to 22 Ω. A very-low-ESR polymer capacitor is not an automatic substitute. Check the revised rail's stability and transient response on hardware, including the effect of the distributed ceramic capacitors.

Retain the existing local 100 nF decouplers. Check DC-bias characteristics when selecting the 4.7 µF ceramics; C19 must provide at least 3.3 µF effective capacitance at 1.8 V. The 50 V and X7R ceramic specifications are recorded as component fields as well as schematic notes.

## USB interface

U18 changes from FT230XS to FT2232HL in an LQFP-64 package. The ADuM1201 isolator is removed and USB ground is connected to board ground. The interface sheet is expanded to A2 to accommodate the additional circuitry.

The FT2232H runs from the board's existing 3.3 V rail. Its internal 1.8 V regulator feeds all three VCORE pins. Added circuitry includes:

- A 12 MHz crystal with grounded case pads and two 30 pF C0G load capacitors. Select a parallel-resonant crystal with an 20 pF load rating and suitable frequency tolerance; confirm loading against PCB stray capacitance.
- A 12 kΩ, 1% reference resistor.
- Individual supply bypass capacitors and ferrite-filtered PHY/PLL supplies.
- A 93LC46B-I/SN EEPROM, organized as 64 × 16 bits, for USB configuration and identity.
- U22, a 74LVC1G07 open-drain buffer, sensing USB VBUS and holding U18 in reset when the cable is absent. Its 5.5 V-tolerant input and partial-power-down protection keep VBUS out of the unpowered FTDI supply domain.

USB VBUS does not feed the board's 5 V or 3.3 V rails. The board must be powered to use USB. Check U14's thermal margin with the additional FT2232H load during PCB and hardware validation.

The old FT230X USB series resistors are removed; the FT2232H has integrated USB termination. R11 and R12 are reused for the reference resistor and VBUS pull-down respectively. Route D+/D− as a short, matched 90 Ω differential pair.

## Channel A: CPLD JTAG

| FT2232H signal | Function |
| --- | --- |
| ADBUS0, pin 16 | TCK, through JP2 pins 1–2 |
| ADBUS1, pin 17 | TDI, through JP2 pins 3–4 |
| ADBUS2, pin 18 | TDO input |
| ADBUS3, pin 19 | TMS, through JP2 pins 5–6 |

Fit all three JP2 shunts for onboard USB JTAG. Remove all three before attaching an external programmer to J3. TDO remains connected to the FTDI input.

The existing chain remains J3 TDI → U15 ATF1508 → U16 ATF1504 → J3 TDO. The AVR is programmed separately through UPDI. JTAG host software must support ATF15xx programming and the complete two-device chain; the schematic update does not provide or validate that software or programming vectors.

## Channel B: console / AVR UPDI

JP1 is a 2 × 3 header with its middle row as the common contacts:

```text
              TX path       RX path
Console          1             2
FTDI common      3             4
UPDI             5             6
```

| Mode | Two shunts |
| --- | --- |
| Console | 1–3 and 2–4 |
| AVR programming | 3–5 and 4–6 |
| External UPDI programmer on J4 | Remove both shunts |

Move both shunts together. They run along the columns; do not fit shunts across the numbered rows.

The console connections retain AVR PC1/RXD and PC0/TXD in the existing 3.3 V Port C supply domain. Disable UART hardware flow control.

For programming, U19 is now a 74LVC1G07 powered at 3.3 V. Its open-drain output drives UPDI through R16 (330 Ω), with R17 (2.2 kΩ) pulling UPDI up to the AVR's 5 V supply. R18 holds the buffer input high when JP1 is disconnected, releasing UPDI for an external programmer. Channel B RX senses UPDI directly through its 5 V-tolerant input and receives local echo and target replies.

Use host software with SerialUPDI support, such as AVRDUDE or pymcuprog. No AVR bootloader or additional programmer MCU is required. The firmware submodule and its existing Atmel-ICE programming target are unchanged. This UART-based interface provides programming, not an Atmel-ICE-equivalent source debugger.

## USB EEPROM setup

A blank EEPROM allows initial USB enumeration. Use FT_PROG to configure:

- Self-powered operation and a unique serial number.
- Channel A's D2XX driver; the JTAG application selects MPSSE at runtime.
- Channel B's UART interface and VCP driver.
- Suspend pull-downs disabled, to avoid pulling programming signals low during USB suspend.

VBUS detection uses RESET rather than the channel-B BCBUS7 suspend option. Channel B stays in UART mode for both console and UPDI.

## Verification

KiCad 10 successfully exports the schematic netlist and PDF. ERC reports the 38 existing missing-library diagnostics for the custom `cbscpe` library; the connector library replacements remove four of the original 42 diagnostics. There are no additional ERC violations. All newly assigned standard footprints resolve in the installed KiCad libraries.

A pin-by-pin netlist comparison confirms that existing non-connector connections are preserved. The new SD and USB connector pin assignments were checked separately. Additional checks cover FTDI supply connections, USB VBUS separation, common ground, the JTAG chain, selector wiring, UPDI driver/receiver wiring, and exactly two remaining tantalum capacitors.

Electrical and programming operation have not been tested on hardware. The exported PDF and ERC check the schematic; they do not validate the existing PCB against this revision.

## References

- [FT2232H datasheet](https://www.ftdichip.cn/Support/Documents/DataSheets/ICs/DS_FT2232H.pdf)
- [74LVC1G07 datasheet](https://www.ti.com/lit/ds/symlink/sn74lvc1g07.pdf)
- [LM1117 datasheet](https://www.ti.com/lit/ds/symlink/lm1117.pdf)
- [Microchip UART-to-UPDI programming documentation](https://github.com/microchip-pic-avr-tools/pymcuprog)

## Sourced component revision

See [the purchasing BOM and sourcing notes](../bom/README.md) for verified JLCPCB part numbers, Basic/Extended classifications, reset-circuit rationale, resistor consolidation, the reused full-size SD socket, the replacement HRO USB connector and the selected narrow-body SN74F38DR drivers (C2878705). J8 is removed. The selected crystal uses a 20 pF load, with 30 pF capacitors per leg as a layout-dependent starting value.

All ordinary pull-ups/pull-downs now use the same 12 kΩ Basic part as R11. R19 retains the recommended 2.2 kΩ EEPROM series resistor. R17 uses the same 2.2 kΩ part as a stronger UPDI pull-up for faster rising edges. USB-C CC resistors remain 5.1 kΩ. All nine SN74F38DR drivers are included in the JLCPCB SMT BOM.
