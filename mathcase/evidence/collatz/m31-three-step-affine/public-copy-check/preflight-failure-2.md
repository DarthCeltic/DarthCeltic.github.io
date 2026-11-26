# Preserved M31 verifier preflight failure 2

- Time: November 18, 2026, 10:41:41 a.m. Eastern
- Exit: 1
- Failure-note SHA-256: `ff50ea371bc100344b047e4abe6ba6d66a847d99bf0c0094e84143c7f0992e3`
- Result: the verifier requires the hash-bound summary file in its output directory. It stopped before reading input data.

This is a setup failure, not a failed arithmetic check. The corrected run used the bound summary and manifest and produced the passing receipt in this folder.
