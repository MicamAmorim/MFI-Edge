"""Synthetic-only prospective three-domain analysis checks."""
import unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.paper_a_three_domain_inference import aggregate_domain_rho,permutation_test,holm2,rho,partition_primary_secondary

class ThreeDomain(unittest.TestCase):
    def rows(self):
        return [dict(dataset=d,X1=float(i+shift),Y1=float(-i+shift),X2=float(i+shift),Y2=float(i-shift)) for d,n,shift in [('NYUDv2',5,0),('MultiCue',6,100),('VSB100',7,-100)] for i in range(n)]
    def test_rank_weights_and_domain_shifts(self):
        rows=self.rows();r,detail=aggregate_domain_rho(rows,'X1','Y1');self.assertAlmostEqual(r,-1);self.assertEqual({d:v['n'] for d,v in detail.items()},{'NYUDv2':5,'MultiCue':6,'VSB100':7})
        self.assertGreater(rho([r['X1'] for r in rows],[r['Y1'] for r in rows]),0.)
    def test_exact_domain_contract(self):
        with self.assertRaises(ValueError):aggregate_domain_rho([r for r in self.rows() if r['dataset']!='VSB100'],'X1','Y1')
    def test_directionality_reproducibility_and_holm(self):
        rows=self.rows();a=permutation_test(rows,'H1',999,20261115);b=permutation_test(rows,'H2',999,20261116)
        self.assertEqual(a,permutation_test(rows,'H1',999,20261115));self.assertLess(a['p_one_sided'],.01);self.assertLess(b['p_one_sided'],.01);self.assertEqual(holm2(.01,.04),(.02,.04))
    def test_invalid_hypothesis_and_constant_fail(self):
        with self.assertRaises(ValueError):permutation_test(self.rows(),'H3',10,1)
        rows=self.rows()
        for r in rows:r['X1']=0.
        with self.assertRaises(ValueError):aggregate_domain_rho(rows,'X1','Y1')
    def test_secondary_biped_cannot_enter_primary_test(self):
        records=[{'dataset':d,'image_id':d} for d in ('BIPED','MultiCue','NYUDv2','VSB100')]
        cohort=[{**r,'analysis_role':'secondary_exploratory' if r['dataset']=='BIPED' else 'primary'} for r in records]
        primary,secondary=partition_primary_secondary(records,cohort)
        self.assertEqual({r['dataset'] for r in primary},{'MultiCue','NYUDv2','VSB100'});self.assertEqual(len(secondary),1)
        cohort[0]['analysis_role']='primary'
        with self.assertRaises(ValueError):partition_primary_secondary(records,cohort)
if __name__=='__main__':unittest.main()
