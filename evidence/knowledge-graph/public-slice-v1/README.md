# Public safe partial knowledge graph slice

This published slice is a partial exact-statement index for the M15-M20 shard replay. It contains 4,262 theorem records. Each exact statement, source digest, dependency list, axiom report, and receipt row was checked against source bytes and receipts in the public evidence package. The graph index supports exact statement-hash matches only; it does not perform semantic retrieval or infer theorem reuse.

## What a row means

A row records the formal statement, its SHA-256, source imports and module-local declarations referenced by the statement block, the recorded axioms and `sorryAx` result, the pinned source path and digest, and the exact per-shard receipt line and digest. Dependency scope is intentionally limited: imported constant closure is not normalized from Lean environment metadata.

Every included row says `m0_status: NOT_REVIEWED_AS_INDIVIDUAL_SHARD_STATEMENT` and `m4_status: NOT_PROMOTED_PER_SHARD_REPLAY_ONLY`. For M20 rows, the separate aggregate M0 review does not review each shard theorem individually. `novelty_status` remains unassessed. The shard replay is finite affine descent evidence; it does not prove global Collatz convergence or complete residue classification.

The slice excludes 29 owner-local or out-of-package records and three historical aggregate records. It does not include the owner graph, personal paths, or restricted dossier content. The manifest records the index digest; `manifest.sha256` binds the manifest and `records.sha256` binds the record file. Individual source and receipt paths and digests are listed in the records; replay materials are browsable in the [M15–M20 evidence guide](../../collatz/m15-m20-pinned-replay/README.md).

## Browse and verify

On the [All work page](../../../work.html#knowledge-graph), click **Verify and load the index**. The browser checks the published manifest, index, and records against their pinned SHA-256 values, then checks each displayed statement against its recorded digest. The files are also available directly in this directory: `manifest.json`, `index.jsonl`, `records.jsonl`, `manifest.sha256`, and `records.sha256`.

The public Lean image and clean-room build context remain unavailable, so this data does not establish independent reproduction of the Lean replay. No M4 gate is changed.
