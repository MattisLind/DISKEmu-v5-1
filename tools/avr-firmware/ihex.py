"""Strict Intel HEX reader and AVR128DB48 flash checks (standard library only)."""
from pathlib import Path

FLASH_SIZE = 128 * 1024
SRAM_START = 0x4000
SRAM_END = 0x8000
EEPROM_SIZE = 512


def read_hex(path, limit=FLASH_SIZE):
    memory, base, eof = {}, 0, False
    for number, line in enumerate(Path(path).read_text().splitlines(), 1):
        if not line: continue
        if eof: raise ValueError(f'HEX data after EOF at line {number}')
        if not line.startswith(':'): raise ValueError(f'Missing HEX record marker at line {number}')
        try: record = bytes.fromhex(line[1:])
        except ValueError as error: raise ValueError(f'Invalid HEX record at line {number}') from error
        if len(record) < 5 or record[0] + 5 != len(record): raise ValueError(f'HEX length mismatch at line {number}')
        if sum(record) & 255: raise ValueError(f'HEX checksum mismatch at line {number}')
        count, address, kind = record[0], int.from_bytes(record[1:3], 'big'), record[3]
        data = record[4:-1]
        if kind == 0:
            if base + address + count > limit: raise ValueError('HEX address outside target memory')
            for offset, value in enumerate(data, base + address):
                if offset in memory: raise ValueError('Overlapping HEX data')
                memory[offset] = value
        elif kind == 1:
            if count or address: raise ValueError('Invalid HEX EOF record')
            eof = True
        elif kind in (2, 4):
            if count != 2 or address: raise ValueError('Invalid HEX address record')
            base = int.from_bytes(data, 'big') << (4 if kind == 2 else 16)
        elif kind in (3, 5):
            if count != 4 or address: raise ValueError('Invalid HEX start record')
        else: raise ValueError(f'Unsupported HEX record type {kind}')
    if not eof or not memory: raise ValueError('Missing HEX EOF or empty image')
    return memory


def flash_binary(memory):
    image = bytearray(b'\xff') * FLASH_SIZE
    for address, value in memory.items(): image[address] = value
    return bytes(image)


def reset_target(memory):
    if not all(address in memory for address in range(4)): raise ValueError('Missing reset vector')
    word = memory[0] | memory[1] << 8
    if word & 0xfe0e != 0x940c: raise ValueError('Reset vector is not an AVR JMP')
    target = ((word & 0x1f0) << 13) | ((word & 1) << 16) | memory[2] | (memory[3] << 8)
    if 2 * target not in memory: raise ValueError('Reset target has no program data')
    return target
