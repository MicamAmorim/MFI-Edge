"""Regression checks for the historical MFI-Edge mathematical implementation.

Run: python test_math.py   or   python -m unittest test_math -v

The original Stage1-5 API is tested as-is. For strict generalized Choquet,
use tests/test_stage24_math_contracts.py instead. unittest checks also run
under python -O, unlike the former module-level 'assert' statements.
"""
from __future__ import annotations

import unittest
import numpy as np

from src.operators import (
    FUNCTIONS, TP, TL, choquet_standard, choquet_expanded, cf_integral,
    cf1f2_integral, check_cf1f2_pair,
)
from src.fuzzy_measures import (
    capacity_table_additive, capacity_table_sugeno, capacity_table_2additive,
    tail_capacities, validate_capacity_table, shapley_values, interaction_matrix,
)
from src.measure_learning import learn_additive, learn_2additive

# Frozen API inventory: compare identifiers, not a magic numeric operator count.
# Additions to the research registry require an explicit decision rather than
# accidentally changing the historical operator search space.
EXPECTED_LEGACY_OPERATORS = frozenset((
    "TP", "TM", "TL", "AVG", "THP", "TDP",
    "OB", "OmM", "ODiv", "GM", "HM", "S",
    "CF", "CL", "ORS", "FGL", "FBPC",
    "FNA", "FNA2", "FIM", "FIP",
))


class LegacyMathematicalContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.x = np.random.default_rng(1).random((200, 8))

    def test_historical_operator_inventory(self):
        self.assertSetEqual(set(FUNCTIONS), set(EXPECTED_LEGACY_OPERATORS))

    def test_choquet_cf1f2_classical_reductions(self):
        a = choquet_standard(self.x, .1)
        b = choquet_expanded(self.x, .1)
        c = cf_integral(self.x, TP, .1)
        d = cf1f2_integral(self.x, TP, TP, .1)
        for label, value in (("expanded", b), ("CF/TP", c), ("CF1F2/TP,TP", d)):
            self.assertLess(float(np.max(np.abs(a-value))), 1e-10, label)

    def test_historical_pair_screening(self):
        chk = check_cf1f2_pair(TP, TL)
        self.assertTrue(chk.dominates)
        self.assertTrue(chk.f1_first_increasing)
        self.assertTrue(chk.boundary_ok)

    def test_additive_choquet_equals_weighted_mean(self):
        w = np.arange(1, 9, dtype=float)
        w /= w.sum()
        ca = choquet_standard(self.x, measure_spec={"kind": "additive", "weights": w})
        self.assertLess(float(np.max(np.abs(ca - self.x @ w))), 1e-9)
        self.assertTrue(validate_capacity_table(capacity_table_additive(w)))

    def test_sugeno_lambda_three_density_regimes(self):
        w = np.arange(1, 9, dtype=float)
        w /= w.sum()
        for target in (.7, 1., 1.3):
            with self.subTest(target=target):
                self.assertTrue(validate_capacity_table(
                    capacity_table_sugeno(w * target), tol=1e-6))

    def test_normalized_2additive_shapley_efficiency(self):
        singleton = np.full(8, .08, dtype=float)
        pair = np.zeros((8,8), dtype=float)
        for i in range(7):
            pair[i,i+1] = pair[i+1,i] = .01
        raw_mass = float(singleton.sum()+sum(pair[i,j] for i in range(8)
                                               for j in range(i+1,8)))
        self.assertAlmostEqual(raw_mass, .71, places=12)
        table = capacity_table_2additive(singleton, pair)
        self.assertTrue(validate_capacity_table(table, tol=1e-6))
        self.assertAlmostEqual(float(table[-1]), 1., places=12)
        shapley = shapley_values(table)
        self.assertAlmostEqual(float(shapley.sum()), 1., places=7)
        # Theoretical Möbius formula for an explicitly normalized 2-additive capacity.
        expected = np.array([singleton[i]+.5*sum(pair[i,j]
                             for j in range(8) if i != j) for i in range(8)])
        expected /= raw_mass
        np.testing.assert_allclose(shapley, expected, rtol=1e-9, atol=1e-9)
        interaction = interaction_matrix(table)
        self.assertLess(float(np.max(np.abs(interaction-interaction.T))), 1e-12)

    def test_adaptive_tail_weights_form_decreasing_chain(self):
        for spec in (
            {"kind":"adaptive_power","mode":"mean"},
            {"kind":"adaptive_power","mode":"geomean"},
            {"kind":"local_additive","mode":"softmax"},
        ):
            with self.subTest(spec=spec):
                values = tail_capacities(self.x, spec)
                self.assertEqual(values.shape, self.x.shape)
                self.assertTrue(np.isfinite(values).all())
                self.assertGreaterEqual(float(np.min(values)), -1e-9)
                self.assertLessEqual(float(np.max(values)), 1.+1e-9)
                self.assertTrue(np.all(np.diff(values, axis=-1) <= 1e-8))

    def test_learned_capacity_validity(self):
        y = (self.x[:,0]+.7*self.x[:,1]>.9).astype(float)
        additive = learn_additive(self.x, y)
        self.assertTrue(validate_capacity_table(
            np.asarray(additive["capacity_table"])))
        two_additive = learn_2additive(self.x, y, maxiter=150)
        self.assertTrue(validate_capacity_table(
            np.asarray(two_additive["capacity_table"]), tol=1e-5))


if __name__ == "__main__":
    unittest.main(verbosity=2)
