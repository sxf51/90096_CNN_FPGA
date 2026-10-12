import hashlib
import math
import struct
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gen_rom_weights import encode_weight, tensors, transform_kernel
from run_exp import ROOT


class RomTests(unittest.TestCase):
    def test_convergent_halfway_and_saturation(self):
        for scaled, expected in ((.5, 0), (1.5, 2), (2.5, 2), (-.5, 0), (-1.5, -2),
                                 (-2.5, -2), (511.5, 511), (-512.5, -512), (1000, 511)):
            self.assertEqual(encode_weight(scaled / 512), expected)
        with self.assertRaises(ValueError):
            encode_weight(math.nan)

    def test_independent_integer_g2_matches_existing_archived_tensor(self):
        values, provenance = tensors(ROOT / "src/weights")
        packed = struct.pack("<9216h", *values["W1"])
        existing = ROOT / "experiments/W21_subkernel_raw_cache_T8/offline_G2_w10_i16.bin"
        self.assertEqual(packed, existing.read_bytes())
        self.assertEqual(hashlib.sha256(packed).hexdigest(),
                         "5a988be2c01584bb22fe38af7137606a28a7fb0e516fda5c149c29b5a91a5dac")
        self.assertEqual(len(provenance), 6)
        self.assertEqual(sum(map(len, values.values())), 12161)

    def test_corner_impulse_transform_preserves_integer_scale(self):
        self.assertEqual(transform_kernel([1, 0, 0, 0, 0, 0, 0, 0, 0]),
                         [4, 2, 2, 0, 2, 1, 1, 0, 2, 1, 1, 0, 0, 0, 0, 0])


if __name__ == "__main__":
    unittest.main()
