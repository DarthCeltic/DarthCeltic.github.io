# M31 three-step affine lower bound, protocol v1

## Question

What sharp uniform lower bound follows from the already verified first-three odd-only affine strata on the 23,642,078 saved odd residue classes modulo 2^31?

## Exact statement and scope

Let T(x)=(3x+1)/2^v2(3x+1), the accelerated odd-to-odd Collatz map. For every positive member n=r+k*2^31 (k>=0) of every residue class in the pinned M31 residual set, the verified first-three valuation strata imply

```text
16*T^3(n) - 27*n >= 19.
```

The inequality is sharp: equality holds throughout the populated (a2,a3)=(1,2) stratum, containing 4,146,987 saved classes. Equivalently, T^3(n) >= (27*n+19)/16, so this third iterate exceeds 27/16 of the starting value by at least 19/16.

This is a derived exact finite affine corollary of the previously verified strata. It is not a new Lean theorem, a global statement about all odd integers, a step-four descent result, a Collatz convergence result, or a novelty claim.

## Algebra

For the three populated strata, the parent result gives T^3(n) as (27*n+19)/8, (27*n+19)/16, or (27*n+23)/16. The exact margins 16*T^3(n)-27*n are therefore 27*n+38, 19, and 23, respectively. The fourth listed stratum (a2,a3)=(2,2) has zero classes and carries no population claim.

## Inputs and audit

Use only the bound M31 first-three-above-start run at `m31-first-three-above-start-v1/run-1`. Verify its run manifest, independent verification receipt, summary, all 21 source inputs, and source hashes before deriving this corollary. The new derivation uses the checked summary formulas and counts; it does not rescan trajectories or reread the 23-million-row residual population.

The derivation and independent verifier are standard-library Python. One focused unit-test run precedes the arithmetic derivation. The output directory is immutable: the runner refuses to overwrite it and preserves a failure receipt on an error. The source Git field identifies the base revision; exact uncommitted source bytes are separately bound in the input map. No Lean, Docker, model, provider, search, network, GPU, or paid service is used. No M0/M4 or downstream status changes follow.

## Reproduction

From the repository root:

```powershell
python -m unittest scripts/test_collatz_m31_three_step_affine_lower_bound_v1.py
python scripts/derive_collatz_m31_three_step_affine_lower_bound_v1.py --output-dir research/collatz/structure-sample/m31-three-step-affine-lower-bound-v1/run-1
python scripts/verify_collatz_m31_three_step_affine_lower_bound_v1.py --output-dir research/collatz/structure-sample/m31-three-step-affine-lower-bound-v1/run-1
```
