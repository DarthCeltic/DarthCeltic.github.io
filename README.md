# Ryan J. Gurganious on GitHub Pages

[The portfolio](https://darthceltic.github.io/) introduces the projects and links to their source, demos, and upstream contributions.

- [MathCase](https://darthceltic.github.io/mathcase/) contains the activities, proof reader, workbench, classroom materials, research results, and public evidence.
- [ARGUS](https://darthceltic.github.io/argus/), [Determinex](https://darthceltic.github.io/determinex/), and [Herculaneum Scroll Tools](https://darthceltic.github.io/herculaneum-scroll-tools/) have project guides with setup or source links.
- [Millennial Mayhem](https://darthceltic.github.io/Millennial-Mayhem/) hosts the playable preview.

## MathCase updates

Edit public MathCase pages and their assets in `mathcase/`. The [visitor sync script](scripts/sync_mathcase_visitor.py) copies the approved workbench from a pinned public MathCase commit into `mathcase/visitor/`.

Older page URLs redirect to the corresponding MathCase page, including the query and fragment. The root portfolio also forwards bookmarked MathCase case IDs and section anchors. Existing direct evidence and asset URLs remain at their original paths for compatibility. Add new evidence under `mathcase/evidence/`.

For a research result, give readers a question, a small example, the exact claim, and one action they can try. Link to the scoped proof or computation and its receipt. A saved-case reader shows recorded evidence, and the visitor workbench can open the public Lean editor to check a draft.

## Local preview and checks

    python -B -m http.server 8000 --bind 127.0.0.1
    python -B tests/public_reading.py
    node --test tests/*.cjs test-*.cjs

## License

Apache-2.0. See [LICENSE](LICENSE).
