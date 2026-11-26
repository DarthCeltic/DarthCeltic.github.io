# M31 residual second odd-step valuation census v1

Classification: `EXACT_FINITE_RESIDUAL_CLASS_CENSUS`.

## Question and frozen population

The prior M31 residual audit found that the first odd-to-odd valuation is fixed at one for every one of the 23,642,078 residue classes left by the saved 128-step strict-affine screen. This census measures the next valuation, which was not fixed by that initial screen statistic.

The population is exactly the unresolved residue set reconstructed from the hash-bound M30 coverage mask and the saved M31 family rows at modulus `2^31`. The expected population is 23,642,078 classes. For each residue `r`, use the same fixed positive representative as the prior audit, `n = r + 2^31`.

For each class, first recheck `v2(3n+1) = 1`. Define

```text
u = (3n + 1) / 2
a2 = v2(3u + 1) = v2((9n + 5) / 2)
```

Record the exact histogram of `a2`, the number of classes with `a2 < 30` and `a2 >= 30`, and the number with `3 <= a2 < 30`.

## Pre-registered interpretation

For any other member `n' = n + k*2^31` of the same residue class,

```text
(9n' + 5)/2 = (9n + 5)/2 + 9k*2^30.
```

Therefore, when the representative has `a2 < 30`, the second valuation is identical for every integer in that residue class. For such classes with `a2 >= 3`, two odd-to-odd transitions give

```text
T(T(n)) = (9n + 5) / 2^(a2 + 1) < n
```

for every positive member `n` of the class. The report may count these uniform finite descent families, but does not formalize them or promote them to Lean evidence. A representative with `a2 >= 30` is reported as non-uniform by this argument; no all-members conclusion is made for that class.

The histogram is an exact census of fixed representatives in this selected finite population. It is not a random sample, not a distribution theorem for odd integers, and not a Collatz convergence result. No post-hoc residue mining, longer trajectory search, or follow-up parameter sweep is authorized by this protocol.

## Inputs, execution, and stop rules

Use the existing verified M31 loader, the M31 scan and independent validation, the reconstructed M30 mask, and the saved `m31-residual-initial-valuation-v1` receipt. Recheck all package hashes and require the new census to reproduce its predecessor's population count and first-valuation histogram exactly.

Run sequentially on one local CPU. No Docker, GPU, Lean build, provider/model/search/network calls, or external spend. Do not alter the previous M31 sample, scan, or audit artifacts.

If any input binding, expected count, family-row match, parity, first valuation, or histogram-conservation check fails, preserve a failure receipt and stop. Do not repair inputs or retry under this version. This is an arithmetic census only; no M0/M4 status changes.
