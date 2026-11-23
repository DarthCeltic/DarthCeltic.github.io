# darthceltic.github.io

The live site for MathCase and Ryan Gurganious's public projects: https://darthceltic.github.io/

## What this is

- **MathCase** — a provenance-first formal mathematics system (Lean 4). Try the guided lesson, inspect saved cases in the Case Desk reader, or bring your own claim to the visitor workbench. The demo is the judged work: see below.
- **Projects** — [/projects/](https://darthceltic.github.io/projects/) lists the public work: MathCase, Determinex, ARGUS, Herculaneum Scroll Tools, plus upstream contributions.

## Judging

MathCase is entered in the Nebius × NVIDIA Global AI Hackathon. Judging runs Nov 16–Dec 4, 2026; winners are announced Jan 25, 2027 at 12:00pm PST. The demo stays live through Dec 23. [Official schedule](https://nebiusglobalaihackathon.devpost.com/details/dates).

## How the site works

A static GitHub Pages site. No backend, no accounts. Opening a saved case makes no model, Lean, or search call — the results shown are saved evidence. The visitor workbench runs in your browser; its optional Lean check hands source to the public Lean web editor (live.lean-lang.org) and produces no MathCase receipt.

## Pages

- `/` — MathCase guide and judge path
- `/reader.html` — Saved Case Desk: two saved cases, a counterexample and a checked lemma
- `/saved-demo/` — the saved data files behind the reader; its index redirects to `/reader.html`
- `/visitor/` — visitor workbench: make your own case
- `/work.html` — evidence ledger
- `/projects/` — portfolio
- `/collatz.html`, `/replay.html`, `/timeline.html`, `/roadmap.html`, `/tools.html` — theorem, replay, timeline, roadmap, tools

## License

Apache-2.0. See [LICENSE](LICENSE).
