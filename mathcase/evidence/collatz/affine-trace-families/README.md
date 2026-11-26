# Three Lean-checked affine Collatz families

These are infinite, parameterized descent lemmas over exactly three progressions. They are stronger than checking a finite list of starting values, but much narrower than a global descent theorem.

| Starting progression | Exact endpoint after standard steps | Strict gap | Lean receipt |
|---|---|---|---|
| `2^31*k + 111` | after 50 steps: `1,162,261,467*k + 61` | `985,222,181*k + 50` | `receipts/m31-residue111-lean-check-receipt.json` |
| `2^31*k + 223` | after 50 steps: `1,162,261,467*k + 122` | `985,222,181*k + 101` | `receipts/m31-residue223-attempt-1-receipt.json` |
| `2^29*k + 167` | after 47 steps: `387,420,489*k + 122` | `149,450,423*k + 45` | `receipts/m29-residue167-attempt-3-receipt.json` |

Each statement holds for every natural `k`. The receipts report Lean 4.33.1, network-disabled local execution, one CPU, 2 GiB, exit code zero, and axioms `[propext, Quot.sound]`. The certificate sources and relevant runner scripts are in `sources/`.

The owner directed public display of these three MathCase-authored family certificates for this site release on November 18, 2026. The release scope is summarized in `../../RELEASE_SCOPE.md`. The receipt fields describe the earlier local runs; they are not independent review, M0 review, M4 acceptance, or a claim that the pinned image is publicly rebuildable. The M29/M31 arithmetic scans remain exploratory evidence for how the candidate rows were selected.

These families do not prove that every integer descends, that every trajectory reaches 1, or that the Collatz conjecture is solved. A separate compositional transfer statement is not included here.
