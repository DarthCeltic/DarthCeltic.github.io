# A checked 42-vertex Ramsey construction

## In plain language

A known 42-vertex two-coloring of the complete graph has no monochromatic clique on five vertices. In Ramsey-number language, this gives the established lower bound `R(5,5) ≥ 43`.

MathCase independently reconstructed the published Exoo(42) construction and checked every 5-vertex subset: **850,668** subsets were examined, with no red or blue `K5`. The derived graph6 file has SHA-256 `0d855016014ce4c2fbfcdba270683086a351b4a1e59afd611cc53e9b15109da7`; the checker has SHA-256 `cfbacf65e9ebe4ac3eefe80adb53c712ffdf842a515f20e991603e7157eef538`.

This reproduces a known finite construction. It is not a new Ramsey result, and it has not been formalized in Lean. The pinned FormalConjectures target remains `sorry` in its source; Ryan's M0 statement review is still unassessed. The exact M0 question is staged owner-local and is not part of this public bundle.

## Files and literature

`check_exoo42.py` deterministically creates the graph and checks all 5-subsets. `exoo42-derived.graph6` and `exoo42-verification-receipt.json` preserve the successful check. A separate supplied certificate failed because its YAML declared 42 vertices while its graph6 bytes decode to 41; that failure is retained in `graph6-order-mismatch-receipt.json` and is not used as evidence for the checked construction.

The construction is known in the literature; see [the R(5,5) lower-bound construction paper](https://arxiv.org/abs/2212.12630). The FormalConjectures target is pinned to snapshot `b576d527b271b936f9e61c0e367c302d7386bc80`; its source is [RamseyNumbers](https://google-deepmind.github.io/formal-conjectures/src/FormalConjectures/Wikipedia/RamseyNumbers/).
