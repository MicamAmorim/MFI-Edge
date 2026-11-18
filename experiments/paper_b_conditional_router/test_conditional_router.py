"""Synthetic development fixtures only, never current confirmation outcomes."""
import unittest,sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
from conditional_router import ConditionalRewardRouter,TrainingIdentity
class Router(unittest.TestCase):
    def data(self):
        x=np.tile(np.array([[0,0],[0,1],[1,0],[1,1]],float),(2,1));y=np.column_stack((x[:,0],1-x[:,0],x[:,1],1-x[:,1]));ids=[TrainingIdentity('synthetic'+str(i),f'{i:064x}','synthetic_scene'+str(i),'development_train') for i in range(8)];return x,y,ids
    def test_training_gate_and_protected_scenes(self):
        x,y,ids=self.data();m=ConditionalRewardRouter(blocked_original_hashes=[],blocked_scenes=[])
        with self.assertRaises(PermissionError):m.fit(x,y,ids)
        m=ConditionalRewardRouter(blocked_original_hashes=[ids[0].original_sha256],blocked_scenes=[])
        with self.assertRaises(PermissionError):m.fit(x,y,ids,confirmation_analysis_completed=True)
    def test_fit_and_deterministic_head_order(self):
        x,y,ids=self.data();m=ConditionalRewardRouter(blocked_original_hashes=[],blocked_scenes=[]).fit(x,y,ids,confirmation_analysis_completed=True)
        self.assertEqual(m.select(x).shape,(8,));self.assertEqual(m.artifact()['status'],'DEVELOPMENT_ONLY_NOT_EXTERNALLY_VALIDATED');self.assertEqual(m.select([[1,0]])[0],'H1_equal_mean')
    def test_no_fitting_on_heldout_or_duplicate_scenes(self):
        x,y,ids=self.data();m=ConditionalRewardRouter(blocked_original_hashes=[],blocked_scenes=[]);ids[0]=TrainingIdentity('protected',ids[0].original_sha256,'s','test')
        with self.assertRaises(PermissionError):m.fit(x,y,ids,confirmation_analysis_completed=True)
    def test_inference_needs_model_and_finite_features(self):
        m=ConditionalRewardRouter(blocked_original_hashes=[],blocked_scenes=[])
        with self.assertRaises(RuntimeError):m.select([[0,0]])
        x,y,ids=self.data();m.fit(x,y,ids,confirmation_analysis_completed=True)
        with self.assertRaises(ValueError):m.select([[np.nan,0]])
if __name__=='__main__':unittest.main()
