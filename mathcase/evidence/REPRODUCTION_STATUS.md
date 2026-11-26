# What a stranger can reproduce today

## Available from this public Pages repository

- Human-readable MathCase result summaries and exact source locations.
- M20 composition source files, shard receipts, two fresh source-replay hash/timing tables, grouped axiom output, and the source-binding addendum. The [public MathCase repository](https://github.com/DarthCeltic/MathCase/tree/main/reproduction/m20-public-source-replay-v1) also publishes its v2 runner and dated full-run evidence.
- A public slice of 4,262 theorem statements with hash-checked local browser search.
- The M31 affine-bound source, input files, and successful independent arithmetic-verifier receipt.
- Three affine Collatz family sources with saved local Lean receipts.
- Erdős–Straus aggregate audit/summary and per-range maxima on this Pages site. The public MathCase main branch now carries the per-witness payloads for all 100 recorded ranges through `d ≤ 10,000,000`; its [human-readable guide](https://github.com/DarthCeltic/MathCase/blob/main/research/number-theory/egyptian-fractions/README.md) explains the bundle and recheck commands.
- The Ramsey finite-graph construction, exact checker, graph6 output, and receipt. The public MathCase repository also links a separate Lean proof bundle with all 29 sources and 28 chunk/composition receipts.

## Still open

On November 26, an author-side v2 runner completed the M20 source replay from pinned public MathCase and Mathlib sources. It compiled all 363 modules, passed 23 axiom groups covering 4,262 theorem queries, and recorded the runner hash. A separate same-host audit rehashed the sources, outputs, logs, and dependencies without rerunning Lean. All 363 new OLEANs match the November 18 Phase 2 outputs; none match the original container OLEAN hashes. The run, receipt, logs, artifact audit, and public bootstrap instructions are in the [dated run folder](https://github.com/DarthCeltic/MathCase/tree/main/reproduction/m20-public-source-replay-v1/runs/2026-11-26-full-r2) and [replay guide](https://github.com/DarthCeltic/MathCase/blob/main/reproduction/m20-public-source-replay-v1/ORIGINAL_REPLAY.md).

This is an author-side run and same-host artifact audit, not an independent stranger reproduction. The local Docker image used for that run has no public pull URL; the documented pinned-source bootstrap is the public route. A separate November 23 saved full run later passed a same-host file audit but did not record the runner hash. The still older smoke receipt covers only one shard. These are distinct records. A stranger's full run remains outstanding.

The older Docker image for the historical M20 and affine Lean runs is not anonymously pullable, and those M20 phase outputs are large; OLEAN binaries were intentionally omitted from this Pages copy. This site therefore does not contain all run artifacts, though public source replay instructions and current v2 evidence are linked above.

The top-level M15–M20 export manifest is omitted because it contains a pointer to a non-public source branch. The shard statements, source hashes, axiom records, and receipt rows included in the public graph slice remain individually bound; the narrower M20 composition subpackage has its own manifest.

Independent human review remains open. The M20 shard records do not have individual M0 review; M4 was not promoted. The R(5,5) target has M0 YES and a Lean proof in 27 chunks plus a final composition, but the recorded run used a warm local cache and has not been independently reviewed or rebuilt from a fresh checkout. The model-based transfer comparison and learner evaluation are staged, not run; no model calls are running and spend is $0.

The public MathCase repository now includes the R(5,5) source-and-receipt bundle at main commit `bdda68f561d852daef16c38cae8a2a5b8b1499c5`. This Pages publication links to that bundle; it does not alter the MathCase repository.
