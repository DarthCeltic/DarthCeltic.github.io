import unittest
from pathlib import Path

from derive_coefficient_audit import EXPECTED_FAMILIES, EXPECTED_MODULES, extract_rows, parse_claim_line, render_tsv


class CoefficientAuditTests(unittest.TestCase):
    def test_parses_listed_equality_and_bound(self):
        line = "(∀ k : Nat, CollatzM20Shard001.iterate (1048576 * k + 239) 32 = 531441 * k + 122 ∧ 531441 * k + 122 < 1048576 * k + 239) ∧"
        self.assertEqual(parse_claim_line(line, "M20CompositionShard001.lean", 4), (1, 239, 122))

    def test_parses_final_proposition_line(self):
        line = "(∀ k : Nat, CollatzM20Shard133.iterate (1048576 * k + 1047967) 32 = 531441 * k + 531133 ∧ 531441 * k + 531133 < 1048576 * k + 1047967) := by"
        self.assertEqual(parse_claim_line(line, "M20CompositionShard133.lean", 17), (133, 1_047_967, 531_133))

    def test_rejects_mismatched_endpoint_in_inequality(self):
        line = "(∀ k : Nat, CollatzM20Shard001.iterate (1048576 * k + 239) 32 = 531441 * k + 122 ∧ 531441 * k + 123 < 1048576 * k + 239) ∧"
        with self.assertRaisesRegex(ValueError, "coefficients differ"):
            parse_claim_line(line, "M20CompositionShard001.lean", 4)

    def test_public_source_inventory_and_minimum_gap(self):
        repository_root = Path(__file__).resolve().parents[4]
        source_directory = repository_root / "evidence/collatz/m15-m20-pinned-replay/m20-composition-v1/sources"
        rows = extract_rows(source_directory)
        self.assertEqual(len(rows), EXPECTED_FAMILIES)
        self.assertEqual(len({row.module for row in rows}), EXPECTED_MODULES)
        self.assertEqual(min(row.intercept_gap for row in rows), 117)
        self.assertEqual(rows[0].intercept_gap, 117)
        self.assertTrue(all(row.intercept_gap > 0 for row in rows))
        self.assertEqual(render_tsv(rows).count(b"\n"), EXPECTED_FAMILIES + 1)


if __name__ == "__main__":
    unittest.main()
