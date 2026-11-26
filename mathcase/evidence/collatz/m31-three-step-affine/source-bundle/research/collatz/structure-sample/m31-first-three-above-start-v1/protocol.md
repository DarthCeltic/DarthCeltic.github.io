# M31 first-three iterates above the starting value — protocol v1

## Question and scope

For every positive integer `n` in each of the 23,642,078 saved odd residual classes modulo `2^31`, do the first three accelerated odd-to-odd Collatz iterates all remain strictly above the original `n`?

This is a finite, source-conditioned affine derivation over the saved residual set. It does not assert that consecutive iterates increase, that a later iterate falls below `n`, that the Collatz sequence converges, or that any open problem is solved.

The accelerated odd-to-odd map is `T(n) = (3n + 1) / 2^v2(3n+1)` for positive odd `n`. The saved initial, second, and third valuation audits establish uniformly over every member of the residual classes that `a1=1`, `a2` is 1 or 2, and the recorded `a3` strata are as follows:

| `a2` | `a3` | class count |
|---:|---:|---:|
| 1 | 1 | 15,348,104 |
| 1 | 2 | 4,146,987 |
| 2 | 1 | 4,146,987 |
| 2 | 2 | 0 |

The counts sum to 23,642,078. The exact population, uniformity, source bindings, and independent third-census receipt are checked by the derivation and verifier.

## Exact affine calculation

For every such `n`, `T(n)=(3n+1)/2`, hence `T(n)-n=(n+1)/2 > 0`.

The second iterate is `(9n+5)/4` when `a2=1` and `(9n+5)/8` when `a2=2`. Therefore its difference from the original start is respectively `(5n+5)/4` and `(n+5)/8`, both positive for every positive `n`.

The third iterate is:

| `a2` | `a3` | `T^3(n)` | `T^3(n)-n` |
|---:|---:|---|---|
| 1 | 1 | `(27n+19)/8` | `(19n+19)/8` |
| 1 | 2 | `(27n+19)/16` | `(11n+19)/16` |
| 2 | 1 | `(27n+23)/16` | `(11n+23)/16` |
| 2 | 2 | `(27n+23)/32` | empty stratum; no population claim |

Each populated third-step stratum has positive difference from `n` for every positive `n`. Together, these identities establish `T(n)>n`, `T^2(n)>n`, and `T^3(n)>n` for every positive member of the saved residual set.

## Nonmonotonicity is explicit

This result is about each iterate versus the original `n`; it is not monotonic growth across consecutive iterates. The exact pairwise differences are:

- `a2=1`: `T^2(n)-T(n)=(3n+3)/4 > 0`.
- `a2=2`: `T^2(n)-T(n)=(1-3n)/8 < 0` for positive `n`. This occurs in 4,146,987 saved classes.
- `(a2,a3)=(1,1)`: `T^3(n)-T^2(n)=(9n+9)/8 > 0`.
- `(a2,a3)=(1,2)`: `T^3(n)-T^2(n)=-(9n+1)/16 < 0` for positive `n`. This occurs in 4,146,987 saved classes.
- `(a2,a3)=(2,1)`: `T^3(n)-T^2(n)=(9n+13)/16 > 0`.
- `(a2,a3)=(2,2)` is empty; no observed-class conclusion is attached to it.

Accordingly, “no iterate below the starting value in steps 1–3” is supported, while “the iterates increase at each step” is false. Step 4 is the first step not excluded by this calculation; this does not show that a below-start value occurs at step 4 or later.

## Inputs and reproduction

Run from the MathCase repository root:

```powershell
python -m unittest scripts/test_derive_collatz_m31_first_three_above_start_v1.py
python scripts/derive_collatz_m31_first_three_above_start_v1.py --output-dir research/collatz/structure-sample/m31-first-three-above-start-v1/run-1
python scripts/verify_collatz_m31_first_three_above_start_v1.py --output research/collatz/structure-sample/m31-first-three-above-start-v1/run-1/verification-receipt.json
```

The derivation binds the three earlier valuation audit packages and their source code, plus the third-census independent verification and exact aggregate decomposition. The independent verifier rehashes those inputs, rechecks parent status and bindings, reconstructs the formulas and pairwise signs, and conserves the stratum population. Existing v1 and v2 folders, source files, and receipts are preserved unchanged.

## Limits

No trajectory census, Lean compilation, model/provider/search call, or external spend is part of this derivation. It is not a Lean proof or an M4 result. It establishes no convergence theorem, density statement, probability claim, novelty claim, or universal Collatz result beyond the stated finite residual classes. It does not prove a later descent.
