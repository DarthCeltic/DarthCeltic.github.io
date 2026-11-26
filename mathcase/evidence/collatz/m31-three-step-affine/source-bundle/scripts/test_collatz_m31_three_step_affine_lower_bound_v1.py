#!/usr/bin/env python3
"""Focused exact-arithmetic tests for the finite M31 lower bound."""
from __future__ import annotations

import unittest
from fractions import Fraction

from scripts.derive_collatz_m31_three_step_affine_lower_bound_v1 import affine_margin


class M31ThreeStepAffineBoundTests(unittest.TestCase):
    def test_populated_strata_have_exact_nonnegative_margin(self) -> None:
        cases = (
            ((1, 1), 27, 19, 8, Fraction(27), Fraction(38)),
            ((1, 2), 27, 19, 16, Fraction(0), Fraction(19)),
            ((2, 1), 27, 23, 16, Fraction(0), Fraction(23)),
        )
        for key, slope, constant, denominator, expected_slope, expected_constant in cases:
            with self.subTest(stratum=key):
                got_slope, got_constant = affine_margin(slope, constant, denominator)
                self.assertEqual((got_slope, got_constant), (expected_slope, expected_constant))
                self.assertGreaterEqual(got_slope, 0)
                self.assertGreaterEqual(got_slope + got_constant, 19)

    def test_exact_cross_multiplication_for_all_populated_formulas(self) -> None:
        cases = ((27, 19, 8), (27, 19, 16), (27, 23, 16))
        for slope, constant, denominator in cases:
            for n in (1, 3, 7, 1 << 31, 10**100):
                with self.subTest(formula=(slope, constant, denominator), n=n):
                    left = 16 * (slope * n + constant)
                    right = denominator * (27 * n + 19)
                    self.assertGreaterEqual(left, right)

    def test_sharp_stratum_is_exactly_the_populated_1_2_row(self) -> None:
        slope, constant = affine_margin(27, 19, 16)
        self.assertEqual((slope, constant), (0, 19))
        self.assertEqual(4_146_987 + 15_348_104 + 4_146_987, 23_642_078)

    def test_empty_2_2_stratum_is_not_covered_by_the_bound(self) -> None:
        slope, constant = affine_margin(27, 23, 32)
        self.assertEqual((slope, constant), (Fraction(-27, 2), Fraction(23, 2)))
        self.assertLess(slope + constant, 19)


if __name__ == "__main__":
    unittest.main()