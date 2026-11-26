# Correction: finite M20 percentage

The historical README in this folder says 97.395%. That is a rounding error.

The exact count is `1,021,248 / 1,048,576 = 97.393798828125%`, which rounds to **97.394%** to three decimal places. The checked arithmetic/binding summary and receipt are in `../../m15-m20-coverage-audit/`.

This is a finite fraction of residue classes modulo `2^20`; it is not a percentage of the Collatz conjecture solved and is not a natural-density theorem. The historical README and its original hash-bound artifacts are preserved unchanged.
