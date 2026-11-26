# M31 residual third odd-step valuation census v1

Classification: `EXACT_FINITE_RESIDUAL_CLASS_CENSUS`. This protocol is a new,
separately versioned follow-up; it does not extend or rewrite the v1 sample,
initial-valuation audit, or second-valuation census.

## Frozen question and population

Measure the third odd-to-odd valuation on every one of the 23,642,078 odd
classes left outside the saved M31 strict-affine screen modulo `2^31`. Rebuild
the population from the hash-bound M30 coverage mask and saved M31 family rows,
then require exact agreement with the prior residual audit and both M31
package validators. For each class `r`, use the previously fixed
representative `n = r + 2^31`.

The prior census binds `a1 = v2(3n+1) = 1` and `a2 = v2(3T(n)+1)` to either 1
or 2 for every class member. Define `T(n) = (3n+1)/2^a` for odd `n`, where
`a = v2(3n+1)`, and measure

```text
a3 = v2(3*T(T(n)) + 1).
```

Record the exact `a3` histogram, the fixed-representative count for which
`T^3(n) < n`, and the count whose third valuation is uniform throughout its
residue class by the registered congruence bound.

## Registered class-uniformity and descent checks

If `a2 = 1`, then `T^2(n) = (9n+5)/4`. Replacing `n` by `n + k*2^31` changes
`3*T^2(n)+1` by `27*k*2^29`, so `a3 < 29` is invariant throughout the class.
If `a2 = 2`, then `T^2(n) = (9n+5)/8`; the corresponding change is
`27*k*2^28`, so `a3 < 28` is invariant throughout the class. Values at or above
these cutoffs are reported as not certified uniform by this bound; no claim
that they actually vary is made.

For the fixed representatives, the exact formulas are

```text
a2 = 1: T^3(n) = (27n + 19) / 2^(a3 + 2)
a2 = 2: T^3(n) = (27n + 23) / 2^(a3 + 3).
```

Consequently the predicted descent thresholds are `a3 >= 3` when `a2 = 1`
and `a3 >= 2` when `a2 = 2`. The run must compare these predicates with direct
three-step arithmetic for every representative. A class is counted as a
uniform three-step descent family only if its third valuation is below its
class-uniformity cutoff and its least positive member satisfies the exact
strict-descent inequality. Otherwise the report may claim only the measured
representative result.

## Stop rules and evidence

Run once, sequentially, on one local CPU. No Docker, Lean build, GPU,
provider/model/search/network calls, or external spend. Do not retry a failure
under this version. If any input binding, expected count, first/second
valuation, histogram conservation, direct-versus-formula check, or
class-uniformity check fails, preserve the failure receipt and stop.

The run records the protocol, script, parent audit, M30/M31 inputs, output
summary, a sorted four-byte little-endian index of every unresolved residue,
an independent direct-trajectory verification receipt, focused-test source, and
hashes in a new `run-1` directory. The independent verifier must reconstruct
the residual set with set membership (separate from the primary sorted-merge
enumeration), check the index row-for-row, recompute all three odd steps, and
match every summary count and histogram before the run qualifies as verified.
No M0/M4 status changes follow from this arithmetic census. It is not a Lean
proof, distribution theorem, novelty claim, or Collatz convergence result.
This version authorizes no fourth-valuation scan or adaptive residue mining.
