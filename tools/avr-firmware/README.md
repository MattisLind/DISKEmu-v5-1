# AVR firmware build container

Builds both firmware personalities for the **AVR128DB48** on the DISKEmu Q-bus
board: MSCP and RLV12. The firmware is AVRASM2 assembly, so this container uses
Microchip AVRASM2 under Wine rather than converting the source to GNU assembler.
The firmware checkout is mounted as input; assembly uses a temporary copy and
writes artifacts under the hardware repository's ignored `build/` directory.
The container does not connect to or program hardware.

## Build

From the hardware repository root, with Docker running:

```sh
make firmware-toolchain
make firmware
make firmware-test
make firmware-repro
```

`firmware-toolchain` builds `diskemu-avr:1`; `firmware` assembles both variants.
`firmware-mscp` and `firmware-rlv12` build individual variants. `firmware-test`
runs the Intel HEX validation tests. `firmware-repro` builds both variants twice
and requires byte-identical HEX and BIN files, checking their manifest hashes.

Host prerequisites: Docker, Bash, Python 3 and curl. The container is Linux/amd64
because the assembler is a Windows x86 executable; Docker Desktop handles amd64
emulation on Apple Silicon. The AVR image is independent of the CPLD image.
Override its tag with `AVR_FIRMWARE_IMAGE` for both building and running.

## Programming images

| Variant | Intel HEX for flash programming | Raw flash binary |
| --- | --- | --- |
| MSCP | `build/firmware/mscp/diskemu-mscp.hex` | `build/firmware/mscp/diskemu-mscp.bin` |
| RLV12 | `build/firmware/rlv12/diskemu-rlv12.hex` | `build/firmware/rlv12/diskemu-rlv12.bin` |

Use the HEX file for the selected emulation when programming the AVR flash.
The BIN file starts at flash byte address zero and is exactly 131,072 bytes,
with unused addresses filled with erased-flash `0xff`. The HEX file preserves
the assembler's sparse addressing, including constant tables above 64 KiB.

Each variant directory also contains an assembly log, map (`.map`), listing
(`.lss`), AVRASM debug files (`.obj`, `.tmp`) and a JSON build manifest. The `.obj`
is AVRASM debug information, not an ELF executable. The current firmware defines
no EEPROM image, so no `.eep` is produced; EEPROM and USERROW contents are not
invented or bundled into the flash image. There are no fuse-programming commands.
Failed builds remove previous programming files for the affected variant.

## Pinned dependencies

`sources.lock.json` records immutable source revisions, URLs and SHA-256 hashes.
`fetch-tools.py` caches downloads; `prepare.py` verifies them again inside Docker.

| Dependency | Pinned input |
| --- | --- |
| AVRASM2 | Microchip assembler 2.2.8, build 80; executable mirrored by [GreatCowBASIC/AVRASM2](https://github.com/GreatCowBASIC/AVRASM2/tree/be677ade639ab64ffd05d3c625f5a4e24633e6df), revision `be677ade639ab64ffd05d3c625f5a4e24633e6df` |
| Shared assembly/FAT source | Firmware author's [cbscpe/include](https://github.com/cbscpe/include/tree/e708e195414fb9bfb84f029500fe39d9b80f01f4), revision `e708e195414fb9bfb84f029500fe39d9b80f01f4`, including its bundled FAT directory |
| AVR128DB48 definitions | Official [Microchip AVR-Dx DFP 2.8.343](https://packs.download.microchip.com/Microchip.AVR-Dx_DFP.2.8.343.atpack); device include is extracted unchanged |

The shared include repository already contains the FAT sources. A separate,
newer FAT checkout is deliberately not overlaid on that coherent snapshot.
Downloads and vendor binaries are not committed into this repository. Retain
vendor license terms; the shared source's LICENSE and device-pack license are
kept in the image. The Ubuntu base is pinned by digest; its Wine/runtime packages
are distribution-managed rather than pinned to an immutable package snapshot.

The original [firmware author's build notes](https://www.5volts.ch/pages/mscpemulator/070-downloadsandlinks/)
and [Microchip AVRASM2 command-line documentation](https://onlinedocs.microchip.com/oxy/GUID-E06F3258-483F-4A7B-B1F8-69933E029363-en-US-2/GUID-EA460BF0-F9E7-4A8D-A624-047DFB8CC4AF.html)
provide background for the assembler and dependency layout.

## Source correction and reproducibility

The checked-out firmware referenced `CLKCTRL_FREQSEL_24M_gc`, which is absent
from the official device headers. The single spelling correction in
`MSCPEmu-v4-0/diskemu.inc` uses `CLKCTRL_FRQSEL_24M_gc`, the official 24 MHz setting
(`0x24`). No replacement device registers or guessed constants are supplied.
The original firmware Makefile remains available; the new container bypasses
its host-specific executable paths and missing sibling include directories.

The original Makefile expects a Git tag, but this firmware fork currently has
none. The container uses a tag when available, otherwise an explicit Git commit
version; modified checkouts carry `-dirty`. `--version` can override this banner.
Exact source-file hashes, firmware revision, dependency lock, device-header hash,
assembler/Wine versions, clock settings, memory usage and image hashes are
recorded in the manifest.

The firmware embeds `__DATE__` and `__TIME__`. A generated include overrides these
only in the build copy, using the firmware commit time in UTC. Set
`SOURCE_DATE_EPOCH` on the host or pass `--epoch SECONDS` to choose another fixed
timestamp. The tracked source files are not rewritten for this purpose.

```sh
SOURCE_DATE_EPOCH=1786447336 tools/avr-firmware/build-in-docker.sh
# Or, with an explicit version and timestamp:
tools/avr-firmware/build-in-docker.sh --variant mscp \
    --version test-1 --epoch 1786447336 --output /src/build/firmware-test
```

HEX/BIN repeatability applies to the same sources, dependencies, version and
build timestamp. Committing a source change or adding a release tag changes
embedded version/date data as expected. Listings, maps and debug files contain
assembler wall-clock timestamps and are not claimed to be byte-reproducible.

## Verification performed

Both personalities assemble successfully with **zero errors and zero warnings**.

| Variant | Used flash bytes | Static SRAM bytes |
| --- | ---: | ---: |
| MSCP | 65,104 / 131,072 | 3,876 / 16,384 |
| RLV12 | 57,244 / 131,072 | 3,669 / 16,384 |

These numbers describe the current source/version banner; future changes can
change them. The build checks Intel HEX record lengths/checksums, EOF, overlap
and target address limits; it cross-checks programmed-byte count with the
assembler's memory summary. It also checks:

- AVR128DB48 signature definitions and 24 MHz clock setting.
- Reset vector is a JMP to the map's `start` symbol.
- Constant tables exist in the mapped flash region starting at byte `0x10000`.
- Static SRAM stays below `0x5000`, preserving the source's monitor, heap and
  logging regions.
- The binary contains the requested version/timestamp and erased-flash padding.

These establish a reproducible, structurally checked build. There is no matching
known-good binary comparison, emulator run or physical-board test. They do not
prove disk-controller behavior, peripheral timing or runtime memory safety.

## Script reference

| File | Usage |
| --- | --- |
| `build-docker.sh` | Host: downloads dependencies, then builds the image. Additional arguments go to `docker build`. |
| `fetch-tools.py` | Host: `python3 tools/avr-firmware/fetch-tools.py`; verifies/downloads locked inputs into `downloads/`. No arguments. |
| `prepare.py` | Container build: `python3 /opt/avr/prepare.py DOWNLOAD_DIRECTORY`; verifies hashes and extracts the assembler/library/device files. |
| `build-in-docker.sh` | Host: locates the hardware repository automatically and runs the image, forwarding arguments to `build.py`. Caller directory does not matter. |
| `build.py` | Container entry point: `--variant all\|mscp\|rlv12`, `--source DIRECTORY`, `--output DIRECTORY`, `--version LABEL`, `--epoch SECONDS`. Defaults: both variants, `/src/MSCPEmu-v4-0`, `/src/build/firmware`, Git-derived version/time. `--help` lists options. |
| `ihex.py` | Internal Python library; no CLI. Parses HEX, builds a full flash binary and decodes the reset JMP for validation. |
| `check-reproducible.py` | Host: `python3 tools/avr-firmware/check-reproducible.py FIRST_DIRECTORY SECOND_DIRECTORY`; compares both variants' HEX/BIN files and validates manifest hashes. |
| `tests/test_ihex.py` | Host: `python3 -m unittest discover -s tools/avr-firmware/tests -v`; covers damaged checksums, address bounds, EOF, overlaps, reset vectors and binary padding. |

Source/output paths supplied to the container use `/src/...`, where `/src` is
the hardware repository. Only that directory is mounted; dependency sources are
installed in the image under `/opt/avr`.
