# M20 composition: what was replayed

## In plain language

For each of the 2,652 residue/coefficient pairs explicitly listed in `m15-m20-pinned-replay/m20-composition-v1/sources/M20CompositionAllFamiliesV1.lean`, and for every natural number `k`, the standard Collatz map sends

```text
1,048,576*k + r  → after exactly 32 steps → 531,441*k + q
```

and the endpoint is strictly smaller than the start. Here `1,048,576 = 2^20`, `531,441 = 3^12`, and the exact `(r,q)` pairs are the ones in the Lean source. The source-defined map is the ordinary map: halve an even input; send an odd input to `3n+1`.

The formal theorem proves both the exact 32-step equality and the strict inequality. The separate coefficient audit observes that

```text
start − endpoint = 517,135*k + (r − q)
```

and checks that all 2,652 intercept gaps are positive (the smallest is 117). This is bounded descent for the listed progressions. It does not prove global Collatz convergence, classify every residue, or claim novelty.

## Fresh source-to-kernel replay

Two independent isolated workspaces compiled the same pinned source set: 229 shard inputs, 133 composition modules, and the existing final theorem (363 Lean files per phase). Each phase also ran 23 axiom groups covering 4,262 queries. Every group reports `sorryAx = 0`; the final theorem reports `[propext, Quot.sound]`.

| | Phase 1 | Phase 2 |
|---|---|---|
| Inner compilation and axiom checks | completed; every compile row exit 0 | completed; every compile row exit 0 |
| Docker wrapper exit | 124, added two-hour watchdog expired after completion | 0 |
| Docker OOM | no | no |
| Source receipt SHA-256 | `115d08d619763e3478e17467a80852529e55d77f11be7b55e48361830462ebf4` | `6e48d17cf40f4f6b61a7a46793ae1b33f87ead146723ec3762b1f3af69ea45b6` |
| Output manifest SHA-256 | `7baa0fc698f848b125cfe1aef59d2c6793ffe9ace29290a916edb037fe3d37f4` | `b0e8eba33252d1f7eb253d55e05e0249fb599f58ebe75bc0db74c71fcbf967c9` |

Across all 363 modules, both runs agree on source, expected and produced OLEAN, stdout, stderr, and Lean exit-code hashes. Timings differ. Five metadata outputs differ because they contain run-specific timing/environment data. The fresh OLEAN hashes do not match the historical expected OLEAN hashes; both fresh runs nevertheless agree byte-for-byte with each other on OLEANs and axiom outputs.

Each run used Lean 4.33.1 (`819816b2e0a3bf405af45ae5c7af2491d8f5bee6`), Mathlib commit `0df444a360eaa60ab8c11dca51a86af692955474`, and image digest `sha256:ec3377f34aaf0b83502e6755d5403ca36382adb99e4c7ab1470d42a1ac5abdc7`; one CPU, 2 GiB memory and swap, network off. The pinned image supplied 346 prebuilt Mathlib dependency OLEANs. No MathCase OLEANs were reused. The two phases used fresh isolated workspaces, not separate Git clones.

The Phase 2 receipt binds Candidate A's source path. A separately recorded check found Candidate B byte-identical; it does not change which copy the receipt says Phase 2 consumed. The addendum is at `phase-2/source-provenance-addendum.json` (SHA-256 `686e09c3a99011632d82d3c68c90e1b6293e6852382910163d8c7bc8da8c0ca9`). Both copies have SHA-256 `8e8fb280df93829c988a360b01276def73e7e5cbd8c9ce8eca70987d5733d3e5`.

## Evidence files

- `phase-1/` and `phase-2/` contain the module timing/hash tables and axiom outputs. The original owner-local receipt hashes are recorded above; the site does not expose workstation paths.
- `public-receipt-projection.json` in each phase folder is a sanitized summary that points back to the original receipt digest above; it is not represented as the original receipt bytes.
- `../m15-m20-pinned-replay/m20-composition-v1/` contains the 2,652-family source, chunk modules, original attempt history, and exported archive bindings.
- `../m15-m20-coverage-audit/` contains the separately checked residue counts and corrected finite fraction.
- `../m15-m20-pinned-replay/m20-composition-v1/CORRECTION.md` corrects the old rounded percentage in its historical README.
- `../m15-m20-pinned-replay/m20-composition-v1/legacy-aggregate-stop.json` preserves the earlier all-at-once stop after 132 shards.

## Reproduction limit

This is not yet an anonymous clean-room reproduction package. The exact Docker image is not publicly pullable, and the complete image rebuild context is not staged. The fresh replay outputs total about 3.7 GB per phase; their hash manifests and text outputs are public here, but the OLEAN binaries are omitted. The receipts show what ran and bind the evidence; a stranger still needs the pinned environment or a complete rebuild recipe to repeat it.

An earlier root-guard failure stopped before Lean parsed any theorem (stderr SHA-256 `2def9b59c92924c0da78eacb2ff935fb652dede81c4186b7aec689b1c3cff0f6`). The Phase 1 wrapper exit 124 is separately preserved above. Neither is a Lean proof failure.
