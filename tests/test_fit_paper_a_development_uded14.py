#!/usr/bin/env python3
"""Synthetic-only tests of UDED-14 training export; GT not opened."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from fit_paper_a_development_uded14 import training_ids_hash, fill_fit_proofs_unattested

class DevelopmentFitSafetyTests(unittest.TestCase):
    def test_ids_hash_deterministic(self):
        a=[{"id":"1","source_sha256":"a"*64},
           {"id":"2","source_sha256":"b"*64}]
        self.assertEqual(training_ids_hash(a),training_ids_hash(list(reversed(a))))

    def test_provenance_cannot_fake_overlap_approval(self):
        recipe={"hypotheses":[
          {"id":"H1","membership":{"fit_provenance":{}},
           "candidate":{"threshold_fit_provenance":{}},
           "control":{"threshold_fit_provenance":{}}},
          {"id":"H2","membership":{"fit_provenance":{}},
           "candidate":{"capacity_fit_provenance":{},"threshold_fit_provenance":{}},
           "control":{"threshold_fit_provenance":{}}}]}
        fit=fill_fit_proofs_unattested(recipe,"c"*64,"d"*40,"e"*64)
        for h in fit["hypotheses"]:
            self.assertIsNone(h["membership"]["fit_provenance"]["no_confirmatory_overlap_attested"])
        self.assertIsNone(fit["hypotheses"][1]["candidate"]["capacity_fit_provenance"]["no_confirmatory_overlap_attested"])

if __name__=="__main__":
    unittest.main()
