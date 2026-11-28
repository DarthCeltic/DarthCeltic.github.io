# What a stranger can reproduce today

## Available from this public Pages repository

- Human-readable MathCase result summaries and exact source locations.
- M20 composition source files, shard receipts, two fresh source-replay hash/timing tables, grouped axiom output, and the source-binding addendum.
- A public slice of 4,262 theorem statements with hash-checked local browser search.
- The M31 affine-bound source, input files, and successful independent arithmetic-verifier receipt.
- Three affine Collatz family sources with saved local Lean receipts.
- Erdős–Straus aggregate audit/summary and per-range maxima on this Pages site. The public MathCase main branch now carries the per-witness payloads for all 100 recorded ranges through `d ≤ 10,000,000`; its [human-readable guide](https://github.com/DarthCeltic/MathCase/blob/main/research/number-theory/egyptian-fractions/README.md) explains the bundle and recheck commands.
- The Ramsey finite-graph construction, exact checker, graph6 output, and receipt. The public MathCase repository also links a separate Lean proof bundle with all 29 sources and 28 chunk/composition receipts.

## Still open

The pinned Docker image used for the older M20 and affine Lean runs is not anonymously pullable, and its complete rebuild context is not staged here. The M20 phase outputs are large; OLEAN binaries were intentionally omitted, while file hashes and text evidence are available. The newer clean public-source replay uses the documented pinned bootstrap instead of that image; see the linked M20 replay folder for its terminal receipt and full stage manifest.

The top-level M15–M20 export manifest is omitted because it contains a pointer to a non-public source branch. The shard statements, source hashes, axiom records, and receipt rows included in the public graph slice remain individually bound; the narrower M20 composition subpackage has its own manifest.

Independent human review remains open. The M20 shard records do not have individual M0 review; M4 was not promoted. The R(5,5) target has M0 YES and a Lean proof in 27 chunks plus a final composition, but the recorded run used a warm local cache and has not been independently reviewed or rebuilt from a fresh checkout. The model-based transfer comparison and learner evaluation are staged, not run; no model calls are running and spend is $0.

The public MathCase repository now includes the R(5,5) source-and-receipt bundle at main commit `bdda68f561d852daef16c38cae8a2a5b8b1499c5`. This Pages publication links to that bundle; it does not alter the MathCase repository.
