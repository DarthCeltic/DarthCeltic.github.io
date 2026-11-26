# A checked three-step lower bound on a saved finite residue set

## Plain statement

For every positive integer in each of the **23,642,078 saved odd residue classes modulo `2^31`**, after three accelerated odd-to-odd Collatz steps the third value satisfies

```text
16*T^3(n) − 27*n ≥ 19
```

Equivalently, `T^3(n) ≥ (27*n + 19)/16`. Here `T(x) = (3x+1)/2^v2(3x+1)`. The bound is sharp on 4,146,987 saved classes in the `(a2,a3)=(1,2)` stratum.

| First-three valuation stratum | Saved classes | Exact third iterate | Margin `16*T^3(n) − 27*n` |
|---|---:|---|---|
| `(1,1)` | 15,348,104 | `(27*n+19)/8` | `27*n+38` |
| `(1,2)` | 4,146,987 | `(27*n+19)/16` | `19`, sharp |
| `(2,1)` | 4,146,987 | `(27*n+23)/16` | `23` |
| `(2,2)` | 0 | `(27*n+23)/32` | no population claim |

## What was checked

The independent verifier rehashed 30 bound source/input files, including 21 files from the pinned parent result. It checked that the four stratum counts conserve the saved population and confirmed the sharp-equality count. A corrected public-copy run passed with receipt SHA-256 `96136a90fc909bc3cb66913e51550fac175859200f8d427513f5a5fdf344d513`; the exact receipt is in `public-copy-check/verification-receipt.json`.

Two earlier verifier starts are preserved as setup failures in `public-copy-check/`: one started with no output directory (failure-note SHA-256 `2fc3aabddcfff41ad3a5a3f96fb6c5ce600ca7aab7c856e7cef0b382342cf9ca`); the next lacked the summary file the verifier requires in that directory (failure-note SHA-256 `ff50ea371bc100344b047e4abe6ba6d66a847d99bf0c0094e84143c7f0992e3`). Both stopped before reading the data. The corrected run copied the bound summary and manifest into its output directory and passed. Those failures were setup errors, not arithmetic counterexamples.

## Limits and files

This is an exact arithmetic corollary of recorded affine formulas, **not a Lean theorem**. It does not rescan trajectories, prove a fourth-step decrease, cover all odd integers, or imply convergence. No human M0 review or M4 gate is claimed.

The source bundle and input files are under `source-bundle/`. The residual-class input is an optional 94,568,312-byte file; the webpage does not fetch it. The source manifest records the original uncommitted-source state and hashes. A stranger can check the bundled arithmetic verifier, but the local Docker image and a clean-room Lean replay remain separate open work.
