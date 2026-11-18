"""Synthetic persisted-map recovery and corruption checks."""
import unittest,tempfile,sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from execute_paper_a_vsb100_successor import persist_map_cache,verify_map_cache
class CacheIntegrity(unittest.TestCase):
    def test_resume_preserves_identical_cache(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'maps.npz';a={'cue':np.arange(30,dtype=np.float32).reshape(5,6),'prediction':np.eye(5,6,dtype=bool)}
            first=persist_map_cache(p,a);second=persist_map_cache(p,a)
            self.assertEqual(first,second);self.assertEqual(first['arrays']['cue']['dtype'],'<f4')
    def test_corruption_and_changed_inference_fail_closed(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'maps.npz';a={'cue':np.arange(30,dtype=np.float32).reshape(5,6)};record=persist_map_cache(p,a)
            with self.assertRaisesRegex(ValueError,'differs'):persist_map_cache(p,{'cue':a['cue']+1})
            p.write_bytes(p.read_bytes()+b'corruption')
            with self.assertRaisesRegex(ValueError,'hash mismatch'):verify_map_cache(p,record)
if __name__=='__main__':unittest.main()
