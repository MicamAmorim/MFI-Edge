#!/usr/bin/env python3
"""PREFREEZE adapter tests: synthetic grayscale/RGB, NO real data and NO GT."""
import json
from pathlib import Path
import sys
import unittest
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.paper_a_prefreeze_map_adapter import (
    DESCRIPTORS, norm_image_256, predict_original_pregt,
)
from src.paper_a_h1h2_inference_core import predict_from_native_maps
from skimage.transform import resize

RECIPE=json.loads((ROOT/"docs/paper_a_confirmation/P1_DEVELOPMENT_RECIPE_UNATTESTED.json").read_text(encoding="utf-8"))


def generated(name, img):
    h,w=img.shape[:2]
    yy,xx=np.indices((h,w),dtype=float)
    if name==DESCRIPTORS[0]:
        score=xx/max(w,1)
    elif name==DESCRIPTORS[1]:
        score=yy/max(h,1)
    elif name==DESCRIPTORS[2]:
        score=(xx+yy)/(w+h)
    elif name==DESCRIPTORS[3]:
        score=(xx*2-yy+h)/(w*2+h)
    else:
        raise KeyError(name)
    return score.astype(np.float32)


class PreGTAdapterTests(unittest.TestCase):
    def test_only_four_exact_frozen_maps(self):
        self.assertEqual(len(DESCRIPTORS),4)
        self.assertEqual(len(set(DESCRIPTORS)),4)

    def test_max256_downscale_matches_historical_geometry(self):
        a=np.ones((513,1027,3),dtype=np.uint8)*100
        r=norm_image_256(a)
        self.assertEqual(r.shape[:2],(128,256))
        self.assertTrue(np.allclose(r,100))

    def test_small_images_do_not_need_resizing(self):
        a=np.zeros((48,52,3),dtype=np.float32)
        self.assertIs(norm_image_256(a),a)

    def test_pre_gt_pipeline_on_synthetic_image_only(self):
        img=np.zeros((48,52,3),dtype=np.float32)
        yy,xx=np.indices(img.shape[:2])
        img[...,0]=(xx/52).astype(np.float32)
        out=predict_original_pregt(img,RECIPE,descriptor_fn=generated)
        self.assertEqual(out.original_geometry,(48,52))
        self.assertEqual(out.inference_geometry,(48,52))
        self.assertEqual(set(out.predictions),{"H1","H2"})
        for v in out.predictions.values():
            self.assertEqual(v.candidate.dtype,np.bool_)
            self.assertEqual(v.candidate.shape,(48,52))

    def test_downsample_and_reregister_to_native_not_gt(self):
        img=np.zeros((280,300,3),dtype=np.uint8)
        img[:,100:200]=255
        calls=[]
        def fake(name, frame):
            calls.append(frame.shape[:2])
            return generated(name, frame)
        out=predict_original_pregt(img,RECIPE,descriptor_fn=fake)
        self.assertEqual(out.original_geometry,(280,300))
        self.assertEqual(out.inference_geometry,(239,256))
        self.assertEqual(calls,[(239,256)]*4)
        self.assertTrue(all(m.shape==(280,300) for m in out.descriptors.values()))

    def test_missing_or_malformed_source_rejected(self):
        with self.assertRaises(ValueError):
            norm_image_256(np.zeros((4,4,3),dtype=np.uint8))
        with self.assertRaises(ValueError):
            norm_image_256(np.zeros((40,40,4),dtype=np.uint8))
        a=np.zeros((30,40,3),dtype=np.float32)
        a[0,0,0]=np.inf
        with self.assertRaises(ValueError):
            norm_image_256(a)

    def test_quantized_descriptor_rejected(self):
        img=np.zeros((48,52,3),dtype=np.uint8)
        def bad(name,frame):
            return (generated(name,frame)*255).astype(np.uint8)
        with self.assertRaises(ValueError):
            predict_original_pregt(img,RECIPE,descriptor_fn=bad)

    def test_descriptor_shape_drift_rejected(self):
        img=np.zeros((48,52,3),dtype=np.uint8)
        def bad(name,frame):
            return generated(name,frame)[:-1]
        with self.assertRaises(ValueError):
            predict_original_pregt(img,RECIPE,descriptor_fn=bad)

    def test_existing_inference_equivalent_no_modification_of_recipe(self):
        img=np.zeros((48,52,3),dtype=np.float32)
        before=json.dumps(RECIPE,sort_keys=True)
        out=predict_original_pregt(img,RECIPE,descriptor_fn=generated)
        direct=predict_from_native_maps(img,out.descriptors,RECIPE)
        for k in ("H1","H2"):
            np.testing.assert_array_equal(out.predictions[k].candidate,direct[k].candidate)
            np.testing.assert_array_equal(out.predictions[k].control,direct[k].control)
        self.assertEqual(json.dumps(RECIPE,sort_keys=True),before)

if __name__=="__main__":
    unittest.main()
