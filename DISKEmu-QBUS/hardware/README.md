# Local connector libraries

`HP21xx_Connectors.pretty/SD_SHOUHAN_SD-CARD-11P.kicad_mod` is copied unchanged from the same footprint in `hp21xx_papertape_emulator`. It is the full-size SHOU HAN SD-CARD 11P socket, LCSC C7529393. The project-local `fp-lib-table` makes it available without installing the other repository.

The signal pads and mounting features were checked against manufacturer drawing FP-100090 A/0. Pad 10 is WP, pad 11 is CD, and the shell is their grounded common. The local `DISKEmu_Connectors.kicad_sym` symbol matches those numbers. See [the sourcing notes](../../bom/README.md#sd-connector-and-verified-footprint) for the pin mapping, drawing link and footprint hash.

Retain solder mask/insulation under the shaded area in the manufacturer's drawing. The copied footprint's body outline is approximate; check card stop, card entry and enclosure clearances against a physical sample when updating the PCB.

J2 uses the standard KiCad `Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12` footprint for LCSC C165948. The remaining `cbscpe` symbols and Q-bus card-edge footprint are inherited from the original project and have not been replaced by these connector libraries.
