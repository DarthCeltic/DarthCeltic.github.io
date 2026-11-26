from __future__ import annotations

import hashlib
import itertools
import json
import pathlib
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parent
OUTPUT_GRAPH = ROOT / "exoo42-derived.graph6"
OUTPUT_RECEIPT = ROOT / "exoo42-verification-receipt.json"
N_CIRCLE = 43
VERTICES = tuple(range(1, 43))
RED_LENGTHS = {1, 2, 7, 10, 12, 13, 14, 16, 18, 20, 21}
FLIP_I_01 = {4, 5, 6, 7, 13, 14, 15, 16, 23, 24, 30, 33, 39, 40}
FLIP_I_12 = {3, 12, 22, 29, 32, 38}
FLIP_I_22_23 = {1, 2, 8, 11, 17, 18, 19, 25, 26, 27, 28, 34, 35, 36, 37}
FLIPPED_EDGES = set()
for i in FLIP_I_01:
    FLIPPED_EDGES.add(tuple(sorted((i % N_CIRCLE, (i + 1) % N_CIRCLE))))
for i in FLIP_I_12:
    FLIPPED_EDGES.add(tuple(sorted(((i + 1) % N_CIRCLE, (i + 2) % N_CIRCLE))))
for i in FLIP_I_22_23:
    FLIPPED_EDGES.add(tuple(sorted(((i + 22) % N_CIRCLE, (i + 23) % N_CIRCLE))))
FLIPPED_EDGES.add((11, 32))

def cyclic_distance(a: int, b: int) -> int:
    delta = abs(a - b) % N_CIRCLE
    return min(delta, N_CIRCLE - delta)

def red_edge(a: int, b: int) -> bool:
    if a == b:
        return False
    pair = tuple(sorted((a, b)))
    base_red = cyclic_distance(a, b) in RED_LENGTHS
    return base_red and pair not in FLIPPED_EDGES

if len(FLIPPED_EDGES) != 16:
    raise SystemExit(f"expected 16 unique recolorings, got {len(FLIPPED_EDGES)}")
if any(cyclic_distance(a, b) not in RED_LENGTHS for a, b in FLIPPED_EDGES):
    raise SystemExit("a listed recoloring was not originally red")

# Produce a graph6 witness from the published construction, relabeling vertices 1..42 to 0..41.
bits = [int(red_edge(a, b)) for a, b in itertools.combinations(VERTICES, 2)]
payload = []
for offset in range(0, len(bits), 6):
    group = bits[offset:offset + 6]
    group.extend([0] * (6 - len(group)))
    value = 0
    for bit in group:
        value = (value << 1) | bit
    payload.append(value + 63)
graph6 = bytes([42 + 63, *payload]) + b"\n"
OUTPUT_GRAPH.write_bytes(graph6)

# Verify the generated graph through a separately decoded graph6 path.
decoded = graph6.strip()
n = decoded[0] - 63
values = [b - 63 for b in decoded[1:]]
expected_chars = (n * (n - 1) // 2 + 5) // 6
if n != 42 or len(values) != expected_chars:
    raise SystemExit(f"generated graph6 shape mismatch: n={n}, payload={len(values)}")
adj = [0] * n
bit_index = 0
for i in range(n):
    for j in range(i + 1, n):
        bit = (values[bit_index // 6] >> (5 - bit_index % 6)) & 1
        bit_index += 1
        if bit:
            adj[i] |= 1 << j
            adj[j] |= 1 << i
cliques = 0
independent = 0
subsets = 0
for subset in itertools.combinations(range(n), 5):
    subsets += 1
    e = [((adj[a] >> b) & 1) for a, b in itertools.combinations(subset, 2)]
    cliques += int(all(e))
    independent += int(not any(e))
if subsets != 850668 or cliques != 0 or independent != 0:
    raise SystemExit(f"Exoo(42) check failed: subsets={subsets}, K5={cliques}, independent5={independent}")

receipt = {
    "schema": "mathcase-exoo42-derived-certificate-verification-v1",
    "status": "PASS_EXACT_FINITE_CHECK",
    "source_paper": "https://arxiv.org/abs/2212.12630",
    "source_scope": "Independent implementation of the explicitly listed Exoo(42) construction; not a new construction or theorem.",
    "target": "There exists a 42-vertex graph with no monochromatic K5 in either color; this gives the known lower bound R(5,5) >= 43.",
    "construction_parameters": {
        "base_cycle_vertices": 43,
        "red_cyclic_distances": sorted(RED_LENGTHS),
        "deleted_vertex": 0,
        "recolored_edges": len(FLIPPED_EDGES),
        "recolored_edge_list": [list(pair) for pair in sorted(FLIPPED_EDGES)]
    },
    "certificate": {
        "file": "exoo42-derived.graph6",
        "sha256": hashlib.sha256(graph6).hexdigest(),
        "vertices": n,
        "red_edges": sum(value.bit_count() for value in adj) // 2
    },
    "check": {
        "five_vertex_subsets_checked": subsets,
        "red_K5_count": cliques,
        "blue_K5_count": independent,
        "result": "PASS"
    },
    "formal_conjectures_snapshot": {
        "commit": "b576d527b271b936f9e61c0e367c302d7386bc80",
        "file": "FormalConjectures/Wikipedia/RamseyNumbers.lean",
        "theorem": "ramsey_number_five_five_lower_bound",
        "m0_status": "UNASSESSED_BY_OWNER",
        "m4_status": "NOT_PROMOTED"
    },
    "generator_and_checker_sha256": hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),
    "checked_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    "provider_calls": 0,
    "external_spend_usd": 0
}
OUTPUT_RECEIPT.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps({
    "status": receipt["status"],
    "vertices": n,
    "recolored_edges": len(FLIPPED_EDGES),
    "five_vertex_subsets_checked": subsets,
    "red_K5_count": cliques,
    "blue_K5_count": independent,
    "certificate_sha256": receipt["certificate"]["sha256"],
    "checker_sha256": receipt["generator_and_checker_sha256"],
    "receipt": str(OUTPUT_RECEIPT)
}, indent=2))
