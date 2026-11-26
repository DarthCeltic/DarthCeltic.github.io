#!/usr/bin/env python3
"""Extract and check the affine coefficients stated by the public M20 composition sources."""

from __future__ import annotations

import csv
import hashlib
import io
import re
from dataclasses import dataclass
from pathlib import Path

MODULUS = 1_048_576
ENDPOINT_COEFFICIENT = 531_441
STEP_COUNT = 32
SLOPE = MODULUS - ENDPOINT_COEFFICIENT
EXPECTED_MODULES = 133
EXPECTED_FAMILIES = 2_652
EXPECTED_MINIMUM_GAP = 117
FINAL_COMPOSITION_SOURCE_SHA256 = "8e8fb280df93829c988a360b01276def73e7e5cbd8c9ce8eca70987d5733d3e5"
EXPECTED_TABLE_SHA256 = "30f06904507a35d180fab9d0d9195759047d13edfd857c04e2ef483eaf75194a"

CLAIM_PREFIX = "(∀ k : Nat, CollatzM20Shard"
CLAIM = re.compile(
    r"^\(∀ k : Nat, CollatzM20Shard(?P<module>\d{3})\.iterate "
    r"\(1048576 \* k \+ (?P<r>\d+)\) 32 = 531441 \* k \+ (?P<q>\d+) ∧ "
    r"531441 \* k \+ (?P<inequality_q>\d+) < 1048576 \* k \+ (?P<inequality_r>\d+)\)$"
)


@dataclass(frozen=True)
class PairRow:
    index: int
    module: str
    source_line: int
    r: int
    q: int
    intercept_gap: int
    source_sha256: str


def parse_claim_line(line: str, source_file: str, line_number: int) -> tuple[int, int, int] | None:
    """Return (module number, r, q); reject any malformed proposition-shaped line."""
    text = line.strip()
    if not text.startswith(CLAIM_PREFIX):
        return None

    if text.endswith(" := by"):
        text = text[:-len(" := by")].rstrip()
    if text.endswith(" ∧"):
        text = text[:-len(" ∧")].rstrip()

    match = CLAIM.fullmatch(text)
    if match is None:
        raise ValueError(f"Unparsed coefficient statement at {source_file}:{line_number}")

    module_number = int(match.group("module"))
    r = int(match.group("r"))
    q = int(match.group("q"))
    if int(match.group("inequality_q")) != q or int(match.group("inequality_r")) != r:
        raise ValueError(f"Equality and inequality coefficients differ at {source_file}:{line_number}")
    expected_module = Path(source_file).stem.removeprefix("M20CompositionShard")
    if f"{module_number:03d}" != expected_module:
        raise ValueError(f"Statement module does not match {source_file}:{line_number}")
    return module_number, r, q


def extract_rows(source_directory: Path) -> list[PairRow]:
    final_source = source_directory / "M20CompositionAllFamiliesV1.lean"
    final_digest = hashlib.sha256(final_source.read_bytes()).hexdigest()
    if final_digest != FINAL_COMPOSITION_SOURCE_SHA256:
        raise ValueError("The pinned final composition source hash changed")
    sources = sorted(source_directory.glob("M20CompositionShard*.lean"))
    expected_names = [f"M20CompositionShard{i:03d}.lean" for i in range(1, EXPECTED_MODULES + 1)]
    if [source.name for source in sources] != expected_names:
        raise ValueError(f"Expected exactly {EXPECTED_MODULES} consecutively numbered composition modules")

    rows: list[PairRow] = []
    for source in sources:
        raw = source.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        text = raw.decode("utf-8", errors="strict")
        for line_number, line in enumerate(text.splitlines(), 1):
            parsed = parse_claim_line(line, source.name, line_number)
            if parsed is None:
                continue
            module_number, r, q = parsed
            rows.append(PairRow(
                index=len(rows) + 1,
                module=f"M20CompositionShard{module_number:03d}.lean",
                source_line=line_number,
                r=r,
                q=q,
                intercept_gap=r - q,
                source_sha256=digest,
            ))

    pairs = {(row.r, row.q) for row in rows}
    if len(rows) != EXPECTED_FAMILIES or len(pairs) != EXPECTED_FAMILIES:
        raise ValueError(f"Expected {EXPECTED_FAMILIES} distinct (r, q) pairs; found {len(rows)} rows and {len(pairs)} pairs")
    if any(row.intercept_gap <= 0 for row in rows):
        raise ValueError("A listed intercept gap is not positive")
    minimum = min(row.intercept_gap for row in rows)
    if minimum != EXPECTED_MINIMUM_GAP:
        raise ValueError(f"Expected minimum intercept gap {EXPECTED_MINIMUM_GAP}; found {minimum}")
    if SLOPE != 517_135:
        raise ValueError("The source affine coefficients no longer produce the recorded slope")
    return rows


def render_tsv(rows: list[PairRow]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(("pair", "composition_module", "source_line", "r", "q", "intercept_gap", "source_sha256"))
    for row in rows:
        writer.writerow((row.index, row.module, row.source_line, row.r, row.q, row.intercept_gap, row.source_sha256))
    return buffer.getvalue().encode("utf-8")


def main() -> None:
    script_directory = Path(__file__).resolve().parent
    repository_root = script_directory.parents[3]
    source_directory = repository_root / "evidence/collatz/m15-m20-pinned-replay/m20-composition-v1/sources"
    output_path = script_directory / "pairs.tsv"
    rows = extract_rows(source_directory)
    output = render_tsv(rows)
    table_digest = hashlib.sha256(output).hexdigest()
    if table_digest != EXPECTED_TABLE_SHA256:
        raise ValueError("The generated table hash differs from the pinned coefficient audit")
    output_path.write_bytes(output)
    print(
        f"families={len(rows)} modules={EXPECTED_MODULES} slope={SLOPE} "
        f"minimum_intercept={min(row.intercept_gap for row in rows)} "
        f"table_sha256={table_digest}"
    )


if __name__ == "__main__":
    main()
