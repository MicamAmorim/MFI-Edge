import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('official', Path(__file__).resolve().parents[1] / 'evaluation/bsds_official/run_official_bsds.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class ResumeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.images = self.base / 'images'; self.images.mkdir()
        (self.images / 'one.jpg').write_bytes(b'image')
        self.out = self.base / 'out'; self.out.mkdir()
        self.count = self.out / 'one_ev1.txt'
    def valid(self):
        self.count.write_text('0.25 1 2 1 2\n0.5 1 2 1 2\n0.75 1 2 1 2\n')
    def run_eval(self, effect, adopt=False):
        with patch.object(m, '_evaluation_identity', return_value={'fixed':'identity'}), patch.object(m, '_run', side_effect=effect):
            return m._evaluate_one(Path('matlab'), benchmark_dir=self.base, image_dir=self.images, gt_dir=self.base, pred_dir=self.base, out_dir=self.out, cfg={'nthresh':3, 'adopt_existing_evaluation':adopt})
    def collect(self, cmd, **kwargs):
        self.assertIn("'collect'", cmd[-1])
        m._save_json(self.out / 'official_summary.json', {'ODS':.5})
        return subprocess.CompletedProcess(cmd,0,'','')
    def test_complete_legacy_requires_explicit_adoption(self):
        self.valid()
        with self.assertRaisesRegex(RuntimeError,'Legacy counts'):
            self.run_eval(self.collect)
        self.assertTrue(self.count.exists())
    def test_complete_counts_only_collect_and_preserved(self):
        self.valid(); before=self.count.read_bytes()
        self.assertEqual(self.run_eval(self.collect,True)['ODS'],.5)
        self.assertEqual(before,self.count.read_bytes())
        self.assertTrue((self.out/'legacy_adoption.json').exists())
    def test_timeout_after_complete_counts_collects(self):
        def effect(cmd,**kwargs):
            if "'evaluate'" in cmd[-1]:
                self.valid()
                raise subprocess.TimeoutExpired(cmd,14400)
            return self.collect(cmd,**kwargs)
        self.assertEqual(self.run_eval(effect)['ODS'],.5)
    def test_timeout_without_progress_fails(self):
        with self.assertRaisesRegex(RuntimeError,'no resumable progress'):
            self.run_eval(lambda cmd,**kwargs: (_ for _ in ()).throw(subprocess.TimeoutExpired(cmd,14400)))
    def test_changed_identity_rejected(self):
        m._save_json(self.out/'evaluation_identity.json',{'other':1})
        with self.assertRaisesRegex(RuntimeError,'inputs changed'):
            self.run_eval(self.collect)
    def test_truncated_and_nonfinite_counts_rejected(self):
        self.count.write_text('0.25 1 2 1 2\n')
        self.assertFalse(m._valid_counts(self.count,3))
        self.valid(); self.count.write_text(self.count.read_text().replace('0.5','nan'))
        self.assertFalse(m._valid_counts(self.count,3))

if __name__ == '__main__': unittest.main()
