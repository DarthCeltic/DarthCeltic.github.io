# How much of the M20 residue space is covered?

## Plain statement

The verified tier counts are finite counts of residue classes. At the largest tier, the checked library records descent for **1,021,248 of 1,048,576 classes modulo `2^20`**, a finite fraction of **97.393798828125%**, which rounds to **97.394%**.

This is not a percentage of the Collatz conjecture solved and not a natural-density theorem about integers. The M20 composition theorem is a separate exact theorem for 2,652 listed infinite progressions; the broader tier count comes from the recorded M15–M20 family-basis audit.

| Tier | Modulus | Checked descent classes | Fraction of that finite residue space |
|---|---:|---:|---:|
| M15 | `2^15 = 32,768` | 31,473 | 96.048% |
| M16 | `2^16 = 65,536` | 63,422 | 96.774% |
| M18 | `2^18 = 262,144` | 254,649 | 97.141% |
| M20 | `2^20 = 1,048,576` | 1,021,248 | 97.394% |

The audit checked 4,262 saved family rows, 229 shard modules, 496 bound inputs, and the 7,825-class M13 seed. It was an independent arithmetic/binding audit of already recorded results: it did not compile Lean or rescan trajectories. Its receipt SHA-256 is `23e2954b29d8e4da28dd5dbf27cd6f0e6a4dcda98e8d74ba8694f96e49523d84`; the receipt reports zero external calls, zero cost, and no M4 promotion.

## The historical rounding error

An older M20 README displays 97.395%. Exact division gives `1,021,248 / 1,048,576 = 97.393798828125%`; standard rounding to three decimal places is **97.394%**. The historical README is retained unchanged. `m15-m20-pinned-replay/m20-composition-v1/CORRECTION.md` points to this audit and prevents the old figure from being mistaken for the corrected one.

## Evidence location

The machine receipt, summary, run manifest, and audit scripts are in this folder. The searchable theorem slice is in `../knowledge-graph/public-slice-v1/`. The source and Lean receipts for the M15–M20 shard replay are in `../m15-m20-pinned-replay/`.

These counts summarize bounded first-descent certificates at each named modulus. They do not show convergence to 1, rule out cycles, or establish a general rule for uncovered classes.
