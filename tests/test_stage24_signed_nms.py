from __future__ import annotations
"""Regression for the Stage 4 NMS diagonal sign bug, fixed for Stage 24G-L.

Image rows increase downward. scipy.ndimage.sobel(axis=0) returns a positive
derivative for top-to-bottom increasing intensities, so normal 45 degrees
uses (upper-left, lower-right); 135 degrees uses (upper-right, lower-left).
"""
import unittest
import numpy as np
from src.postprocess import gradient_orientation, non_maximum_suppression


class NMSSignedOrientationTest(unittest.TestCase):
    def _point(self, theta, stronger_offsets):
        score=np.zeros((9,9),np.float32)
        score[4,4]=.5
        for dy,dx in stronger_offsets:
            score[4+dy,4+dx]=.9
        orientation=np.zeros_like(score)+np.deg2rad(float(theta))
        return non_maximum_suppression(score,orientation)[4,4]

    def test_45_matches_up_left_down_right(self):
        self.assertAlmostEqual(self._point(45,[(-1,1),(1,-1)]),.5)
        self.assertEqual(self._point(45,[(-1,-1)]),0)
        self.assertEqual(self._point(45,[(1,1)]),0)

    def test_135_matches_up_right_down_left(self):
        self.assertAlmostEqual(self._point(135,[(-1,-1),(1,1)]),.5)
        self.assertEqual(self._point(135,[(-1,1)]),0)
        self.assertEqual(self._point(135,[(1,-1)]),0)

    def test_horizontal_and_vertical_unchanged(self):
        self.assertEqual(self._point(0,[(0,1)]),0)
        self.assertEqual(self._point(90,[(1,0)]),0)
        self.assertAlmostEqual(self._point(0,[(-1,0),(1,0)]),.5)
        self.assertAlmostEqual(self._point(90,[(0,-1),(0,1)]),.5)

    def test_gradient_orientation_sign(self):
        yy,xx=np.mgrid[:64,:64]
        im=(xx+yy)/128.
        angle=gradient_orientation(im,sigma=1.0)
        self.assertAlmostEqual(float(angle[32,32]),np.pi/4.,delta=0.12)
        im=(xx-yy+64)/128.
        angle=gradient_orientation(im,sigma=1.0)
        self.assertAlmostEqual(float((angle[32,32]+np.pi) % np.pi),3*np.pi/4.,delta=0.12)

    def test_no_border_wraparound_in_final_output(self):
        score=np.ones((9,9),np.float32)
        orientation=np.zeros_like(score)
        out=non_maximum_suppression(score,orientation)
        self.assertTrue(np.all(out[0,:]==0))
        self.assertTrue(np.all(out[-1,:]==0))
        self.assertTrue(np.all(out[:,0]==0))
        self.assertTrue(np.all(out[:,-1]==0))


if __name__=="__main__":
    unittest.main()
