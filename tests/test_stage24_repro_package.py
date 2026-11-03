"""Synthetic regression of complete scientific archiving (no datasets needed)."""
from pathlib import Path
import json
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))
from scripts import build_stage24gl_repro_package as pack
from scripts import verify_stage24gl_repro as verify


class ReproductionBundleTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        root=Path(self.temp.name)
        self.root=root
        self.source=root/"results/local_dev/stage24_paper_a_recertification"
        self.official=root/"results/official_eval/stage24_paper_a_recertification"
        self.dest=root/"results/paper_a_evidence/stage24gl"
        self.bin=root/"results/local_dev/stage24gl_binary_publication"
        self.cache=root/"cache/local_dev/stage24"
        self.pred=root/"automation/runtime/official_eval_cache/experiments/stage24_paper_a_recertification"
        self.patches=[
            patch.object(pack,"ROOT",root),patch.object(pack,"SOURCE",self.source),
            patch.object(pack,"OFFICIAL",self.official),patch.object(pack,"DEST",self.dest),
            patch.object(pack,"BINARY_DEST",self.bin),patch.object(pack,"CACHE",self.cache),
            patch.object(pack,"PRED",self.pred),
            patch.object(verify,"GIT",self.dest/"reproducibility"),
            patch.object(verify,"BINARY",self.bin),
        ]
        for p in self.patches:p.start()
        for repeat in range(1,6):
            for fold in range(1,4):
                path=self.source/"folds"/f"r{repeat}_f{fold}"/"pair_screen.json"
                path.parent.mkdir(parents=True,exist_ok=True)
                path.write_text('{"example":1}',encoding="utf-8")
        src=self.official/"matlab"/"method_a"/"x_ev1.txt"
        src.parent.mkdir(parents=True,exist_ok=True)
        src.write_text("0.01 1 2 3 4\n",encoding="utf-8")
        (self.official/"summary.json").write_text('{"status":"completed"}',encoding="utf-8")
        desc=self.cache/"descriptors"/"scharr"/"score.npy"
        desc.parent.mkdir(parents=True,exist_ok=True)
        desc.write_bytes(b"scientific float fixture")
        output=self.pred/"method_a"/"x.png"
        output.parent.mkdir(parents=True,exist_ok=True)
        output.write_bytes(b"derived score png fixture")

    def tearDown(self):
        for p in reversed(self.patches):p.stop()
        self.temp.cleanup()

    def test_git_and_binary_archives_are_independently_verifiable(self):
        report=pack.prepare(require_complete=True,build_binary=True)
        self.assertEqual(report["git_numeric_evidence"]["status"],"complete")
        self.assertGreaterEqual(report["external_binary_deposit"]["parts"],1)
        self.assertEqual(verify.verify_git()["verified_files"],16)
        self.assertEqual(verify.verify_binary()["verified_files"],2)
        src=self.dest/"reproducibility"/"external_data_reference.json"
        self.assertFalse(json.loads(src.read_text(encoding="utf-8"))["uploaded"])

    def test_corrupted_zip_is_detected(self):
        pack.prepare(require_complete=True,build_binary=False)
        part=next((self.dest/"reproducibility").glob("cv_part_*.zip"))
        with part.open("ab") as handle:handle.write(b"tampered")
        with self.assertRaises(RuntimeError):
            verify.verify_git()

    def test_missing_fold_blocks_complete_archive(self):
        (self.source/"folds"/"r5_f3"/"pair_screen.json").unlink()
        with self.assertRaisesRegex(RuntimeError,"15"):
            pack.prepare(require_complete=True,build_binary=False)

    def test_binary_bundle_disabled_is_explicit(self):
        result=pack.prepare(require_complete=True,build_binary=False)
        self.assertEqual(result["external_binary_deposit"]["status"],"SKIPPED")
        ref=json.loads((self.dest/"reproducibility"/"external_data_reference.json").read_text(encoding="utf-8"))
        self.assertFalse(ref["prepared_locally"])


if __name__=="__main__":
    unittest.main(verbosity=2)
