import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import analyze_stage24_image_groups as a
import numpy as np
class GroupAuditTests(unittest.TestCase):
 def test_explicit_aliases(self):
  self.assertEqual(a.canonical('x|y|z::owa_median'),'x|y|z::median')
  self.assertEqual(a.canonical('x|y::median'),'x|y::equal_mean')
  self.assertEqual(a.canonical('x|y::owa_pessimistic'),'x|y::minimum')
 def test_complete_universe_only(self):
  rows=[{'model':'A','image_id':'i','fold':'f','F1':.5},{'model':'A','image_id':'j','fold':'g','F1':.6},{'model':'B','image_id':'i','fold':'f','F1':.9}]
  self.assertEqual(set(a.common_models(rows,{('i','f'),('j','g')})),{'A'})
  with self.assertRaises(ValueError):a.common_models(rows+[rows[0]],{('i','f')})
 def test_features_finite_on_flat_map(self):
  self.assertTrue(np.isfinite(a.features(np.zeros((5,7),np.float32))).all())
 def test_ari_label_invariant(self):
  self.assertEqual(a.ari([1,1,2,2],[2,2,1,1]),1.)
 def test_clusters_are_deterministic(self):
  x=np.array([[0,0,0],[0,.1,0],[9,9,9],[9,9.1,9]])
  np.testing.assert_array_equal(a.clusters(x,2),[1,1,2,2])
if __name__=='__main__':unittest.main()
