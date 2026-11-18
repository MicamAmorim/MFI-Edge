"""Synthetic contract checks only: no research GT or outcomes."""
import io,unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
from scipy.io import savemat
from src.paper_a_vsb100_contract import decode_vsb100_boundaries,evaluate_vsb100_paired_binary

def payload(refs):
    stream=io.BytesIO();savemat(stream,{'groundTruth':np.array([{'Boundaries':a} for a in refs],dtype=object)});return stream.getvalue()

class VSB100Contract(unittest.TestCase):
    def setUp(self):
        self.gt=np.zeros((32,40),dtype=np.uint8);self.gt[16,5:25]=1
    def test_four_separate_references_one_observation(self):
        refs=decode_vsb100_boundaries(payload([self.gt]*4),self.gt.shape)
        r=evaluate_vsb100_paired_binary(self.gt.astype(bool),np.zeros_like(self.gt,dtype=bool),refs)
        self.assertEqual(r.annotation_count,4);self.assertEqual(r.candidate_f1_mean,1.);self.assertEqual(r.control_f1_mean,0.);self.assertEqual(r.delta_f1,1.)
        self.assertEqual(r.to_dict()['statistical_observation_count'],1)
    def test_reject_geometry_dtype_and_annotation_count(self):
        for refs,native in [([self.gt]*3,self.gt.shape),([self.gt]*4,(40,32)),([self.gt.astype(float)]*4,self.gt.shape),([self.gt*255]*4,self.gt.shape),([np.zeros_like(self.gt)]*4,self.gt.shape)]:
            with self.assertRaises(ValueError):decode_vsb100_boundaries(payload(refs),native)
    def test_never_implicitly_threshold_predictions(self):
        with self.assertRaises(TypeError):evaluate_vsb100_paired_binary(self.gt,self.gt,tuple(self.gt.astype(bool) for _ in range(4)))
    def test_references_are_scored_separately(self):
        shifted=np.roll(self.gt,8,axis=0).astype(bool);g=self.gt.astype(bool)
        r=evaluate_vsb100_paired_binary(g,np.zeros_like(g),(g,g,shifted,shifted))
        self.assertEqual(r.candidate_f1_by_annotation,(1.,1.,0.,0.));self.assertEqual(r.candidate_f1_mean,.5)
if __name__=='__main__':unittest.main()
