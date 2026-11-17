#!/usr/bin/env python3
"""Fast synthetic tests for the A219 statistical engine; no protected outcomes."""
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import testar_motor_estatistico_a219_sintetico as candidate


class StatisticalEngineA219Tests(unittest.TestCase):
    def test_exact_counts_and_fictional_ids(self):
        rows=candidate.make_synthetic_rows()
        self.assertEqual(len(rows),219)
        self.assertEqual(sum(x["dataset"]=="BIPED" for x in rows),125)
        self.assertEqual(sum(x["dataset"]=="MultiCue" for x in rows),94)
        self.assertTrue(all(x["image_id"].startswith("SYNTHETIC_ONLY_") for x in rows))
        self.assertTrue(all(x["X1"]>0 and -1<=x["X2"]<=1
                            and -1<=x["Y1"]<=1 and -1<=x["Y2"]<=1 for x in rows))

    def test_reproducible_gated_free_inference_with_100_permutations(self):
        obj=candidate.exercise(count=100,bootstrap=100)
        obj2=candidate.exercise(count=100,bootstrap=100)
        self.assertEqual(obj,obj2)
        self.assertEqual(obj["sample"]["N"],219)
        self.assertEqual([t["hypothesis"] for t in obj["tests"]],["H1","H2"])
        self.assertTrue(all(t["permutations"]==100 for t in obj["tests"]))
        self.assertTrue(all(0<=t["holm_p_adjusted"]<=1 for t in obj["tests"]))
        self.assertFalse(obj["cohort_confirmatory_outcomes_read"])
        self.assertFalse(obj["H1_H2_confirmatory_executed"])
        self.assertFalse(obj["freeze_authorized"])

    def test_reject_overwrite_and_freeze_path_reference(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"synthetic.json"
            obj=candidate.exercise(count=100,bootstrap=100)
            candidate.save_without_overwrite(path,obj)
            candidate.save_without_overwrite(path,obj)
            with self.assertRaises(PermissionError):
                candidate.save_without_overwrite(path,{"status":"FORGED"})
        import ast
        source=(ROOT/"scripts"/"testar_motor_estatistico_a219_sintetico.py").read_text("utf-8")
        tree=ast.parse(source)
        imported={x.module for x in ast.walk(tree) if isinstance(x,ast.ImportFrom)}
        calls={x.func.id for x in ast.walk(tree) if isinstance(x,ast.Call)
               and isinstance(x.func,ast.Name)}
        self.assertNotIn("execute_paper_a_frozen_cohort",imported)
        self.assertNotIn("src.paper_a_confirmation_paired_f1",imported)
        for prohibited in ("run_confirmation","authorized","attempt_freeze"):
            self.assertNotIn(prohibited,calls)


if __name__=="__main__":
    unittest.main()
