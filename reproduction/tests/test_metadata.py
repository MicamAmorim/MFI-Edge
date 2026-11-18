"""Small community contract tests, not end-to-end reproduction tests."""
import json
import unittest
from reproduction.context import ROOT,CONFIRMATION

class MetadataTest(unittest.TestCase):
    def test_sources(self):
        cfg=json.loads((ROOT/"reproduction/datasets.json").read_text(encoding="utf-8"))
        self.assertEqual(set(cfg["datasets"]),{"UDED","BSDS500","MultiCue","NYUDv2","VSB100","BIPED"})
    def test_frozen_metadata(self):
        d=json.loads((CONFIRMATION/"EXECUTION_RESULTS.json").read_text(encoding="utf-8"))
        self.assertEqual((d["N_primary"],d["N_secondary_BIPED"]),(312,48))
        self.assertEqual([x["hypothesis"] for x in d["analyses"]],["H1","H2"])

if __name__=="__main__":
    unittest.main()
