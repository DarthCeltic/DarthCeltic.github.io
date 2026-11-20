# A checked 42-vertex Ramsey construction

## In plain language

A known 42-vertex two-coloring of the complete graph has no monochromatic clique on five vertices. In Ramsey-number language, this gives the established lower bound `R(5,5) ≥ 43`.

The pinned formal target at FormalConjectures snapshot `b576d527b271b936f9e61c0e367c302d7386bc80` is:

```lean
∃ G : SimpleGraph (Fin 42), G.CliqueFree 5 ∧ (Gᶜ).CliqueFree 5
```

The English statement used on the site is: “There is a simple graph on 42 vertices with no clique of size five and no independent set of size five.” The graph and its complement represent the two colors. Ryan reviewed this statement (M0 YES, packet SHA-256 `3866a0a6be46bd580c52b0677b1bc9c096ce75038d3941bb77ec795dc77f50cb`). The exact target is `∃ G : SimpleGraph (Fin 42), G.CliqueFree 5 ∧ (Gᶜ).CliqueFree 5`.

MathCase independently reconstructed the published Exoo(42) construction and checked every 5-vertex subset: **850,668** subsets were examined, with no red or blue `K5`. The derived graph6 file has SHA-256 `0d855016014ce4c2fbfcdba270683086a351b4a1e59afd611cc53e9b15109da7`; the checker has SHA-256 `cfbacf65e9ebe4ac3eefe80adb53c712ffdf842a515f20e991603e7157eef538`.

The work page includes a browser-side verifier that checks the graph6 file's pinned SHA-256, decodes it, and exhaustively tests every five-vertex subset in both colors. It verifies this finite certificate; it does not prove a general Ramsey theorem or run Lean.

The separate graph6 browser check verifies this known finite construction. The Lean formalization is now published at [the MathCase R(5,5) source and receipt bundle](https://github.com/DarthCeltic/MathCase/tree/main/reproduction/ramsey-r55-lean-v1): 27 chunk receipts and a final composition receipt, with axioms `[propext, Classical.choice, Quot.sound]`. The original run used a warm local cache; fresh-checkout replay, independent review, and M4 acceptance remain open.

## Files and literature

`check_exoo42.py` deterministically creates the graph and checks all 5-subsets. `exoo42-derived.graph6` and `exoo42-verification-receipt.json` preserve the successful check. A separate supplied certificate failed because its YAML declared 42 vertices while its graph6 bytes decode to 41; that failure is retained in `graph6-order-mismatch-receipt.json` and is not used as evidence for the checked construction.

Prior-work check: the cited paper [Study of Exoo's Lower Bound for Ramsey number R(5,5)](https://arxiv.org/abs/2212.12630) describes and studies this known lower-bound construction. This is enough to reject a novelty claim for the construction reproduced here; no broad literature search is claimed. The FormalConjectures target is pinned to snapshot `b576d527b271b936f9e61c0e367c302d7386bc80`; see its exact [pinned source file](https://github.com/google-deepmind/formal-conjectures/blob/b576d527b271b936f9e61c0e367c302d7386bc80/FormalConjectures/Wikipedia/RamseyNumbers.lean).
