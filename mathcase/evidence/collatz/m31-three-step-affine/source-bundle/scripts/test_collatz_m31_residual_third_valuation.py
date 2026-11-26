#!/usr/bin/env python3
"""Focused arithmetic tests for the frozen M31 third-valuation census."""

from __future__ import annotations

import unittest

from audit_collatz_m31_residual_third_valuation import (
    class_uniformity_cutoff,
    descent_minimum,
    formula_third_odd_iterate,
    third_odd_iterate,
    third_valuation,
    valuation_two,
)


def odd_step(n: int) -> tuple[int, int]:
    value = 3 * n + 1
    valuation = valuation_two(value)
    return value >> valuation, valuation


class ThirdValuationTests(unittest.TestCase):
    def test_two_adic_valuation(self) -> None:
        self.assertEqual(valuation_two(1), 0)
        self.assertEqual(valuation_two(8), 3)
        self.assertEqual(valuation_two(24), 3)
        with self.assertRaises(ValueError):
            valuation_two(0)

    def test_direct_iterate_matches_affine_formulas(self) -> None:
        # 7 has (a1, a2) = (1, 1); 11 has (a1, a2) = (1, 2).
        cases = ((7, 1), (11, 2))
        for n, a2 in cases:
            a3 = third_valuation(n, a2)
            self.assertEqual(third_odd_iterate(n, a2, a3), formula_third_odd_iterate(n, a2, a3))

    def test_registered_uniformity_cutoffs_on_class_shifts(self) -> None:
        modulus = 1 << 31
        for n, expected_a2 in ((7, 1), (11, 2)):
            _, a1 = odd_step(n)
            t2, a2 = odd_step(odd_step(n)[0])
            self.assertEqual(a1, 1)
            self.assertEqual(a2, expected_a2)
            expected_a3 = third_valuation(n, a2)
            self.assertLess(expected_a3, class_uniformity_cutoff(a2))
            for k in range(1, 9):
                shifted = n + k * modulus
                t1_shifted, a1_shifted = odd_step(shifted)
                t2_shifted, a2_shifted = odd_step(t1_shifted)
                self.assertEqual(a1_shifted, 1)
                self.assertEqual(a2_shifted, expected_a2)
                _, a3_shifted = odd_step(t2_shifted)
                self.assertEqual(a3_shifted, expected_a3)

    def test_descent_threshold_matches_direct_arithmetic(self) -> None:
        checked = 0
        for n in range(1, 20_000, 2):
            t1, a1 = odd_step(n)
            if a1 != 1:
                continue
            t2, a2 = odd_step(t1)
            if a2 not in (1, 2):
                continue
            t3, a3 = odd_step(t2)
            self.assertEqual(t3, third_odd_iterate(n, a2, a3))
            threshold = 3 if a2 == 1 else 2
            self.assertEqual(t3 < n, a3 >= threshold)
            checked += 1
        self.assertGreater(checked, 1_000)

    def test_least_positive_member_thresholds_are_strict(self) -> None:
        self.assertGreaterEqual(descent_minimum(1), 4)
        self.assertFalse(formula_third_odd_iterate(3, 1, 3) < 3)
        self.assertTrue(formula_third_odd_iterate(4, 1, 3) < 4)
        self.assertGreaterEqual(descent_minimum(2), 5)
        self.assertFalse(formula_third_odd_iterate(4, 2, 2) < 4)
        self.assertTrue(formula_third_odd_iterate(5, 2, 2) < 5)


if __name__ == "__main__":
    unittest.main()
