import unittest,sys,io
from pathlib import Path
import numpy as np
from scipy.io import savemat
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.paper_a_nyud_contract import decode_nyud_boundaries,evaluate_nyud_paired_binary
def payload(a):
    s=io.BytesIO();savemat(s,{'groundTruth':{'Boundaries':a}});return s.getvalue()
class NYUD(unittest.TestCase):
    def setUp(self):self.g=np.zeros((425,560),dtype=np.uint8);self.g[200,100:120]=1
    def test_exact_supplied_reference(self):
        refs=decode_nyud_boundaries(payload(self.g),self.g.shape)
        self.assertEqual(len(refs),1);self.assertEqual(refs[0].dtype,bool)
        r=evaluate_nyud_paired_binary(refs[0],np.zeros_like(refs[0]),refs)
        self.assertEqual(r.domain,'NYUDv2');self.assertEqual(r.delta_f1,1.)
    def test_wrong_geometry_count_or_encoding_fails(self):
        for a,native in [(self.g,(560,425)),(self.g*255,self.g.shape),(self.g.astype(float),self.g.shape),(self.g[:100],(100,560))]:
            with self.assertRaises(ValueError):decode_nyud_boundaries(payload(a),native)
        with self.assertRaises(ValueError):evaluate_nyud_paired_binary(self.g.astype(bool),self.g.astype(bool),(self.g.astype(bool),)*2)
if __name__=='__main__':unittest.main()
