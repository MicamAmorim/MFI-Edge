#!/usr/bin/env python3
"""Synthetic-only unit test of cache hash function."""
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from run_paper_a_prefreeze_one_shot import hash_npy

class CacheHashTests(unittest.TestCase):
    def test_hash_fake_npy_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / "f" / "any.npy"
            p.parent.mkdir()
            contents = b"\x93NUMPY" + b"Z" * 200
            p.write_bytes(contents)
            actual, size = hash_npy(p)
            self.assertEqual(actual, hashlib.sha256(contents).hexdigest())
            self.assertEqual(size, len(contents))
    def test_refuse_wrong_extension(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / "any.json"
            p.write_bytes(b"X" * 256)
            with self.assertRaises(ValueError):
                hash_npy(p)
    def test_refuse_truncated(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / "any.npy"
            p.write_bytes(b"Y" * 10)
            with self.assertRaises(ValueError):
                hash_npy(p)

if __name__ == "__main__":
    unittest.main()
