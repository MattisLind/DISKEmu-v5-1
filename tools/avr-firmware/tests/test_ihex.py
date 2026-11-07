from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ihex import read_hex, flash_binary, reset_target, FLASH_SIZE


def record(kind, data=b'', address=0):
    raw = bytes([len(data), address >> 8, address & 255, kind]) + data
    return ':' + (raw + bytes([-sum(raw) & 255])).hex().upper()


class HexTests(unittest.TestCase):
    def parse(self, lines, **kwargs):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'test.hex'
            path.write_text('\n'.join(lines) + '\n')
            return read_hex(path, **kwargs)

    def test_segment_and_linear_addressing(self):
        memory = self.parse([record(2, b'\x10\x00'), record(0, b'AB', 2),
                             record(4, b'\x00\x01'), record(0, b'CD', 4), record(1)])
        self.assertEqual(memory, {0x10002: 65, 0x10003: 66, 0x10004: 67, 0x10005: 68})

    def test_bad_checksum_rejected(self):
        with self.assertRaisesRegex(ValueError, 'checksum'):
            self.parse([':010000004100', record(1)])

    def test_address_outside_flash_rejected(self):
        with self.assertRaisesRegex(ValueError, 'outside target'):
            self.parse([record(4, b'\x00\x02'), record(0, b'A'), record(1)])

    def test_missing_eof_rejected(self):
        with self.assertRaisesRegex(ValueError, 'EOF'):
            self.parse([record(0, b'A')])

    def test_data_after_eof_rejected(self):
        with self.assertRaisesRegex(ValueError, 'after EOF'):
            self.parse([record(0, b'A'), record(1), record(0, b'B')])

    def test_overlapping_data_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Overlapping'):
            self.parse([record(0, b'A'), record(0, b'B'), record(1)])

    def test_reset_vector_and_erased_padding(self):
        memory = self.parse([record(0, b'\x0c\x94\x02\x00\x00\x00'), record(1)])
        self.assertEqual(reset_target(memory), 2)
        binary = flash_binary(memory)
        self.assertEqual(len(binary), FLASH_SIZE)
        self.assertEqual(binary[6:], b'\xff' * (FLASH_SIZE - 6))

    def test_wrong_reset_instruction_rejected(self):
        with self.assertRaisesRegex(ValueError, 'not an AVR JMP'):
            reset_target({0: 0, 1: 0, 2: 0, 3: 0})
