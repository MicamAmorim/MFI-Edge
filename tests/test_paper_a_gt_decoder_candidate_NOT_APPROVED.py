#!/usr/bin/env python3
"""Synthetic-only tests of an UNAPPROVED pre-freeze GT policy draft."""
import importlib.util
from pathlib import Path
import unittest
import numpy as np

SOURCE = (Path(__file__).resolve().parents[1] /
          "scripts/paper_a_gt_decoder_candidate_NOT_APPROVED.py")
spec = importlib.util.spec_from_file_location("paper_a_draft_gt", SOURCE)
draft = importlib.util.module_from_spec(spec)
spec.loader.exec_module(draft)


class DraftGTDecoderTests(unittest.TestCase):
    def test_biped_254_is_explicitly_preserved_as_edge_in_draft(self):
        raw = np.array([[0,254,255],[0,0,255]],dtype=np.uint8)
        expected = np.array([[0,1,1],[0,0,1]],dtype=bool)
        np.testing.assert_array_equal(draft.decode_gt_candidate(
            raw,dataset="BIPED",native_shape=(2,3)),expected)

    def test_multicue_uint16_max_is_explicitly_mapped_in_draft(self):
        raw = np.array([[0,65535],[65535,0]],dtype=np.uint16)
        expected = np.array([[0,1],[1,0]],dtype=bool)
        np.testing.assert_array_equal(draft.decode_gt_candidate(
            raw,dataset="MultiCue",native_shape=(2,2)),expected)

    def test_reject_other_values_and_bit_depth(self):
        cases = [
            ("BIPED",np.array([[0,128]],dtype=np.uint8)),
            ("BIPED",np.array([[0,255]],dtype=np.uint16)),
            ("MultiCue",np.array([[0,255]],dtype=np.uint8)),
            ("MultiCue",np.array([[0,65280]],dtype=np.uint16)),
        ]
        for dataset,raw in cases:
            with self.subTest(dataset=dataset,dtype=str(raw.dtype)):
                with self.assertRaises(ValueError):
                    draft.decode_gt_candidate(
                        raw,dataset=dataset,native_shape=raw.shape)

    def test_reject_constant_and_non_native_geometry(self):
        valid=np.array([[0,255],[255,0]],dtype=np.uint8)
        for raw in (np.zeros((2,2),dtype=np.uint8),
                    np.full((2,2),255,dtype=np.uint8)):
            with self.assertRaises(ValueError):
                draft.decode_gt_candidate(raw,dataset="BIPED",
                                         native_shape=(2,2))
        with self.assertRaises(ValueError):
            draft.decode_gt_candidate(valid,dataset="BIPED",
                                     native_shape=(3,3))
        with self.assertRaises(ValueError):
            draft.decode_gt_candidate(np.zeros((2,2,3),dtype=np.uint8),
                                     dataset="BIPED",native_shape=(2,2))

    def test_draft_policy_label_cannot_be_mistaken_for_approved_contract(self):
        self.assertIn("NOT_APPROVED",draft.POLICY_ID)


if __name__=="__main__":
    unittest.main()
