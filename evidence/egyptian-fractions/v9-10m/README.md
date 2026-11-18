# Erdős–Straus: a bounded witness campaign

## In plain language

The campaign searched a factor-conditioned subset of the residual `n ≡ 1 (mod 12)` cases, using 100 recorded denominator-parameter ranges through `d = 10,000,000`. Across the audited baseline and extension runs, the records contain **831,860 candidates and 831,860 exact Egyptian-fraction witnesses**. All 427 base-search misses were resolved within the fixed 65,536 offset cap.

This is finite witness data for the recorded filter and range. The full Erdős–Straus conjecture remains open. Filtered-out values and values beyond the campaign range are not covered.

## What the offset and miss audit found

- Largest recorded first-denominator offset: **35,498**, at `n = 16,459,249`, in the `d = 1,300,001–1,400,000` range. That leaves 30,038 below the fixed cap.
- The overall per-range maximum association was noisy (`r = 0.267`); for v9 alone it was weak (`r = 0.067`). This is not a bound on future offsets.
- Of the 427 base misses, 4 were composite, 131 prime, and 292 prime powers. All had `n ≡ 1 (mod 24)`, a restriction imposed by the candidate filter. The finer residue and factor patterns did not reveal one rule covering all misses.
- No new parameterized identity was established. The work did not prove the conjecture or claim novelty.

The aggregate audit checks 100 range bindings, candidate/result row counts, witness counts, extension receipts, and exact identity rows. Its human-readable source summary, range maxima, and audit record are in this directory.

The public MathCase release at commit `7238e9e` includes the per-witness payloads for all 100 recorded ranges through `d = 10,000,000`. Use the [human-readable bundle guide](https://github.com/DarthCeltic/MathCase/blob/7238e9ea51fd7fcb035c102b7e8b33361e798648/research/number-theory/egyptian-fractions/README.md) for the file map and recheck commands, and the [10-million aggregate audit summary](https://github.com/DarthCeltic/MathCase/blob/7238e9ea51fd7fcb035c102b7e8b33361e798648/research/number-theory/egyptian-fractions/campaign-v9-10m-audit-v1/summary.md) for the audit scope. The 831,860 exact witnesses remain finite evidence for the stated factor-conditioned candidates only.

## Literature context

The bounded offset campaign measures a different object from computational searches over primes. For example, see the published work on the `n ≡ 13 (mod 24)` case ([arXiv:2005.03273](https://arxiv.org/abs/2005.03273)) and the later study of a divisor criterion in the `n ≡ 1 (mod 24)` setting ([arXiv:2608.24035](https://arxiv.org/abs/2608.24035)). These citations are context, not evidence that this campaign matches or extends those results.
