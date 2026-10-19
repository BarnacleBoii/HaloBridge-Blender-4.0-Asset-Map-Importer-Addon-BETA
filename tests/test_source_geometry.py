import unittest
import zlib
from halo_bridge.source_geometry import unpack, MAX_SOURCE_BYTES


class SourceRecoveryTests(unittest.TestCase):
    def test_exact_source_and_checksum(self):
        raw = b';### HEADER ###\n7\n' * 100
        self.assertEqual(unpack(zlib.compress(raw), len(raw), zlib.crc32(raw) ^ 0xffffffff), raw)

    def test_rejects_corruption_truncation_and_expansion(self):
        raw = b'geometry' * 100
        compressed = zlib.compress(raw)
        for data, size, crc in [(compressed, len(raw), 0),
                (compressed[:-1], len(raw), zlib.crc32(raw)),
                (compressed, 10, zlib.crc32(raw)),
                (compressed + b'extra', len(raw), zlib.crc32(raw)),
                (compressed, MAX_SOURCE_BYTES + 1, zlib.crc32(raw))]:
            with self.subTest(size=size, data_length=len(data)):
                with self.assertRaises(RuntimeError):
                    unpack(data, size, crc)
