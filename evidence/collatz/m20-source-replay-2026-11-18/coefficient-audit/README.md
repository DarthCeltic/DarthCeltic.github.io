# M20 coefficient audit

For each of the 2,652 listed Collatz progressions, the starting value minus the recorded 32-step endpoint is `517,135k + (r − q)`, and the smallest listed intercept `r − q` is 117.

## What the calculation does

The replayed Lean statements use the start `1,048,576k + r` and endpoint `531,441k + q`. Subtracting gives:

```text
(1,048,576k + r) − (531,441k + q)
= (1,048,576 − 531,441)k + (r − q)
= 517,135k + (r − q).
```

The coefficient is positive, every listed intercept is positive, and the minimum intercept in the extracted list is 117. Thus this separate arithmetic audit confirms the endpoint expression is smaller for every natural `k` in every listed progression. The Lean theorem separately checks the exact 32-step equality and the strict inequality together.

This audit does not re-run Collatz trajectories, prove the equality, cover unlisted residues, establish global convergence, or claim a new theorem.

## Inputs and bindings

The rows are parsed from the 133 public `M20CompositionShard001.lean` through `M20CompositionShard133.lean` source files. Each row records its composition module, source line, `(r,q)` pair, intercept, and SHA-256 of that source module. The final imported composition theorem is `M20CompositionAllFamiliesV1.lean`, whose saved source SHA-256 is `8e8fb280df93829c988a360b01276def73e7e5cbd8c9ce8eca70987d5733d3e5`.

The generated human-readable table is `pairs.tsv`, SHA-256 `30f06904507a35d180fab9d0d9195759047d13edfd857c04e2ef483eaf75194a`. The browser calculator checks that digest before using the table, then checks the row count, uniqueness, coefficient arithmetic, and minimum intercept again.

## Reproduce the table check

From this directory, run:

```text
py -3 derive_coefficient_audit.py
py -3 -B -m unittest -v test_coefficient_audit.py
```

The generator fails closed if a proposition row is malformed, its equality and inequality coefficients disagree, the 133 source modules are missing or misnumbered, the pair count is not 2,652, a pair repeats, an intercept is nonpositive, or the minimum is not 117.

## Interactive calculation

On the All Work page, choose a one-based row number and any nonnegative integer `k`. The local browser calculation evaluates the start, endpoint, difference, and coefficient formula with exact integers and confirms they agree. It makes no network request beyond fetching the same-origin table; it does not call Lean or a model.

The table is stored here for the calculator: `evidence/collatz/m20-source-replay-2026-11-18/coefficient-audit/pairs.tsv`.
