# Visitor workbench Pages changes

The hosted workbench is based on the public MathCase visitor source at commit [`17174a4`](https://github.com/DarthCeltic/MathCase/tree/17174a4a6311eb2e32556d9e4fb38255290a36be/visitor). The source manifest at [`evidence/visitor-workbench/source-manifest.json`](../source-manifest.json) preserves the upstream file sizes and SHA-256 hashes.

The hosted Pages copy is not byte-for-byte identical to that upstream directory. This document separates changes already present at the Pages base from the new site overlay.

## Added in this Pages update

The [`visitor-guided-target-bound-workbench-2026-11-23-r1.json`](visitor-guided-target-bound-workbench-2026-11-23-r1.json) overlay records the Nov 23 human-guided workbench update. It starts from the 4-and-2 counterexample, lets visitors choose beginner, math, or Lean directions, makes the embedded Lean editor the primary action, and keeps a separate-window option available only on request. The local case checker binds the plain claim, exact Lean target, named declaration, proof source, compiler output, and reported axioms in a receipt.

The embedded editor is still the public `live.lean-lang.org` service. Opening it sends the displayed Lean code and generated exact-target check to that service; it does not create a MathCase receipt. The local checker is a separate path. A person must still review whether the plain-language claim means the Lean proposition. The overlay record pins the Pages baseline, MathCase source commit, and hashes for the three served files. The original source manifest and earlier overlay records remain unchanged.


[`visitor/index.html`](../../../visitor/index.html) moves the public-editor disclosure before the run controls and places the receipt-import button outside the collapsed local-check instructions. The button and file-input IDs stay the same, and the existing click and change listeners remain in [`visitor/workbench.js`](../../../visitor/workbench.js). The source and overlay hashes are recorded in [`visitor-disclosure-receipt-controls-2026-11-22-r1.json`](visitor-disclosure-receipt-controls-2026-11-22-r1.json).

The disclosure says the optional web-editor action sends Lean source to `live.lean-lang.org`, does not check the workbench's target proposition, and does not create a MathCase receipt. Imported receipts remain visitor-supplied compiler evidence.

The later [`teacher-answer-arithmetic-copy-2026-11-23-r1.json`](teacher-answer-arithmetic-copy-2026-11-23-r1.json) records a copy-only correction to the readable teacher answer and its Markdown download. It binds the Pages base and updated file hashes; the pinned MathCase source manifest and earlier overlay receipts remain unchanged.

## Differences already present at the Pages base

At Pages commit `1c46af8cec7c15915c07f8ee1a7a0bfec7bbb688`, three files already differed from the pinned source manifest. The table preserves those historical base hashes; later copy changes are bound by their own overlay records:

| File | Pinned source SHA-256 | Pages base SHA-256 |
| --- | --- | --- |
| `visitor/lesson.html` | `78ccc65358e87f80e9e59105d1db81adee235a7fd9b77a156bd7b3bdb1f0199b` | `0f6076d27e9698b5cbeff08fc61ff60b17fd39a894e14351264ce98b7b38fd58` |
| `visitor/model-workflow.html` | `df097c55a150e97e320197899ef94c39e34d78161a61b7824625764fb9e78674` | `c40ede97e2742afa720404d96d6becdd5ad4f4a3e7837148bde50f251466ffae` |
| `visitor/teacher-guide.md` | `d25b309995dce485a23478a61fc09eb0b6bbf83a6e33774adcf69b47e577bf20` | `08625cc408dd16aaad05bfca1f3deac81edfbf27c98f1cd67cbc482276c9f9cc` |

The other pinned visitor files matched the source manifest at that base. The manifest itself remains unchanged.
