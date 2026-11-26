# A 101-vertex certificate for the known R(6,6) lower bound

A simple graph on 101 labeled vertices has no six-vertex clique and no six-vertex independent set. That finite witness gives the known lower bound **R(6,6) ≥ 102**.

This reproduces a known finite result. It is not a new Ramsey theorem, an exact value for R(6,6), or a Lean proof.

## The graph

The certificate is the Paley graph P(101): vertices are 0 through 100, and vertices i<j are adjacent when j−i modulo 101 is a nonzero quadratic residue. It has 2,525 edges and every vertex has degree 50.

## What was checked

Two separately implemented local checkers read the same edge list. Both searched for a clique of size six and an independent set of size six, returned neither, and exited 0. The C++ checker took 0.145 seconds under one-core affinity and below-normal priority. The independent Python checker took 0.114 seconds. Each reported 51,981 clique-search nodes and 54,976 independent-set-search nodes.

These are two implementations of the same recursive common-neighbor search idea. Their agreement is cross-implementation evidence, not independent mathematical proof. The result is computationally checked and is not Lean-checked.

## Reproduce locally

Requirements: Python 3 and a C++20 compiler. From this directory:

```sh
g++ -std=c++20 -O0 -g -Wall -Wextra -Werror ramsey66_exact_checker.cpp -o ramsey66_exact_checker
./ramsey66_exact_checker --self-test
./ramsey66_exact_checker graph-certificate.json 900
python verify_paley101_independent.py graph-certificate.json --out-dir r66-check-output
```

Use a fresh, nonexistent output directory for the Python run. Exit code 0 and the two `PASS` lines mean the bounded finite checker completed. `public-receipt.json` binds both verifier sources, the C++ executable, the certificate, and both output hashes. The two per-run receipt files preserve each checker's exit code and output digests; `SHA256SUMS.txt` binds the published files.

## Preserved development failures

Before the final published source and certificate were checked, two wrapper attempts failed while assembling receipts, and two earlier optimized C++ builds exited with Windows access-violation code `3221225477`. The exact cause of those crashes was not isolated. Those attempts produced no accepted result and remain preserved in the internal work record. The published checker was rebuilt with the documented `-O0` command, passed its self-tests, and then passed the exact finite check.

The checkers do not run Lean, contact a model or provider, or establish a theorem about graphs of other sizes. The result does not make a new-construction or novelty claim.