# M31 finite third-step affine bound

**Result:** an independently checked exact arithmetic corollary for the 23,642,078 odd residue classes in the pinned M31 residual set.

Let `T(x) = (3*x + 1) / 2^v2(3*x + 1)`, the accelerated odd-to-odd Collatz map. For every positive member `n` of each saved class, the checked first-three-step affine formulas imply

```text
16*T^3(n) - 27*n >= 19
```

Equivalently, `T^3(n) >= (27*n + 19)/16`. The inequality is sharp: equality holds for all 4,146,987 saved classes in the populated `(a2,a3)=(1,2)` stratum.

| First-three valuation stratum | Saved classes | `T^3(n)` | Exact margin `16*T^3(n)-27*n` |
| --- | ---: | --- | --- |
| `(1,1)` | 15,348,104 | `(27*n + 19)/8` | `27*n + 38` |
| `(1,2)` | 4,146,987 | `(27*n + 19)/16` | `19` (sharp) |
| `(2,1)` | 4,146,987 | `(27*n + 23)/16` | `23` |
| `(2,2)` | 0 | `(27*n + 23)/32` | no population claim |

The independent verifier rechecked all 30 source/input bindings, including the 21 inputs in the pinned parent run, and confirmed population conservation and the sharp equality count. It did not rescan trajectories.

## Limits

This is a finite affine corollary of previously recorded M31 arithmetic. It is not a Lean theorem, does not cover other residues or all odd integers, gives no fourth-step descent or convergence result, and carries no novelty claim. No M0/M4 or downstream gate was changed.

## Reproduction

Run from the MathCase repository root with the local virtual environment:

```powershell
.venv\Scripts\python.exe -m unittest scripts/test_collatz_m31_three_step_affine_lower_bound_v1.py
.venv\Scripts\python.exe scripts/derive_collatz_m31_three_step_affine_lower_bound_v1.py --output-dir research/collatz/structure-sample/m31-three-step-affine-lower-bound-v1/run-2
.venv\Scripts\python.exe scripts/verify_collatz_m31_three_step_affine_lower_bound_v1.py --output-dir research/collatz/structure-sample/m31-three-step-affine-lower-bound-v1/run-2
```

The first derivation attempt is preserved at `run-1/failure-receipt.json`: an implementation guard incorrectly required the parent source script to appear in its separate input map even though the same bytes matched the dedicated source hash field. The corrected attempt is `run-2`; the failed receipt was not overwritten.
