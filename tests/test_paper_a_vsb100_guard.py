"""Authorization ordering: synthetic temporary metadata only, no GT I/O."""
import tempfile,unittest,sys,json
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import paper_a_vsb100_freeze_guard as guard
class Guard(unittest.TestCase):
    def test_no_review_cannot_authorize(self):
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaises(FileNotFoundError):guard.authorize(Path(t))
    def test_pending_review_fails_before_recipe_cohort_or_code(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);(p/'INDEPENDENT_REVIEW.json').write_text(json.dumps({'decision':'PENDING','independently_authored':False}))
            with patch.object(guard,'digest',side_effect=AssertionError('Protected next stage reached')):
                with self.assertRaisesRegex(PermissionError,'Independent approval absent'):guard.authorize(p)
    def test_preparer_cannot_claim_independent_review(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);(p/'INDEPENDENT_REVIEW.json').write_text(json.dumps({'decision':'APPROVE_PROSPECTIVE_FREEZE','independently_authored':True,'reviewer_identity':'Codex primary preparer'}))
            with self.assertRaisesRegex(PermissionError,'Accountable independent reviewer'):guard.authorize(p)
if __name__=='__main__':unittest.main()
