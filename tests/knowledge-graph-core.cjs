const test = require("node:test");
const assert = require("node:assert/strict");
const core = require("../knowledge-graph-core.js");

test("reads a verified Collatz family in plain words", () => {
  const parsed = core.parseCollatzStatement("theorem descent_mod32768_127 : ∀ k : Nat, iterate (32768 * k + 127) 24 = 19683 * k + 77 ∧ 19683 * k + 77 < 32768 * k + 127");
  assert.equal(parsed.theoremName, "descent_mod32768_127");
  assert.equal(parsed.startText, "32,768 × k + 127");
  assert.equal(parsed.endText, "19,683 × k + 77");
  assert.match(parsed.plainText, /after 24 standard Collatz steps/i);
  assert.match(parsed.plainText, /smaller than the start/i);
});

test("rejects a statement whose final inequality changes the checked expression", () => {
  const damaged = "theorem x : ∀ k : Nat, iterate (32768 * k + 127) 24 = 19683 * k + 77 ∧ 19683 * k + 76 < 32768 * k + 127";
  assert.equal(core.parseCollatzStatement(damaged), null);
});

test("reads the SHA-256 sidecars from the pinned commit without hardcoding data digests", () => {
  const digest = "a".repeat(64);
  assert.equal(core.parseSha256Sidecar(`${digest}  manifest.json\n`, "manifest.json"), digest);
  assert.equal(core.parseSha256Sidecar(`${digest}  other.json\n`, "manifest.json"), null);
  assert.equal(core.parseSha256Sidecar(`${digest} manifest.json\n`, "manifest.json"), null);
  assert.equal(core.parseSha256Sidecar(`${digest}\n${digest}  manifest.json\n`, "manifest.json"), null);
  assert.equal("manifestSha256" in core.PIN, false);
  assert.equal("indexSha256" in core.PIN, false);
  assert.equal("recordsSha256" in core.PIN, false);
});

test("requires all downloaded bytes to match the committed checksum chain", () => {
  const manifestHash = "a".repeat(64);
  const indexHash = "b".repeat(64);
  const recordsHash = "c".repeat(64);
  const manifest = { index_sha256: indexHash };
  const actual = { manifest: manifestHash, index: indexHash, records: recordsHash };
  assert.equal(core.verifySnapshotHashes(`${manifestHash}  manifest.json\n`, `${recordsHash}  records.jsonl\n`, manifest, actual), true);
  assert.throws(() => core.verifySnapshotHashes(`${"d".repeat(64)}  manifest.json\n`, `${recordsHash}  records.jsonl\n`, manifest, actual), /checksum chain/);
  assert.throws(() => core.verifySnapshotHashes(`${manifestHash}  manifest.json\n`, `${"d".repeat(64)}  records.jsonl\n`, manifest, actual), /checksum chain/);
  assert.throws(() => core.verifySnapshotHashes(`${manifestHash}  manifest.json\n`, `${recordsHash}  records.jsonl\n`, { index_sha256: "d".repeat(64) }, actual), /checksum chain/);
});

test("links only to safe source and evidence paths in the pinned commit", () => {
  const sourceUrl = core.githubFileUrl("sources/repository/research/collatz/m15/lean/modules/Descent127.lean", 9);
  assert.ok(sourceUrl.includes(`/blob/${core.PIN.commit}/reproduction/m15-m20-r2/sources/`));
  assert.ok(sourceUrl.endsWith("#L9"));
  assert.equal(core.githubFileUrl("sources/../../private.txt"), null);
  assert.equal(core.githubFileUrl("sources/private\\file.lean"), null);
});

test("normalizes spacing for human text searches without claiming semantic matches", () => {
  const record = { case_id: "collatz:m15:Descent127:descent_mod32768_127", lean_statement_exact: "theorem descent_mod32768_127 : ∀ k : Nat, iterate (32768 * k + 127) 24 = 19683 * k + 77 ∧ 19683 * k + 77 < 32768 * k + 127" };
  assert.equal(core.matchesSearch(record, "32768k+127"), true);
  assert.equal(core.matchesSearch(record, "not a theorem here"), false);
});

test("searches explicit source and dependency fields for reusable neighbors", () => {
  const record = {
    case_id: "collatz:m16:sample",
    lean_statement_exact: "theorem sample : True",
    source: { package_path: "sources/repository/research/collatz/m16/lean/modules/M16ShardA.lean" },
    dependencies: { imports: ["Mathlib.Data.Nat.Prime.Basic"], module_local_declarations_referenced: ["iterate"] }
  };
  assert.equal(core.matchesSearch(record, "M16ShardA.lean"), true);
  assert.equal(core.matchesSearch(record, "Mathlib.Data.Nat.Prime.Basic"), true);
  assert.equal(core.matchesSearch(record, "iterate"), true);
});

test("clears a selected proof when a search no longer includes it", () => {
  const selected = { case_id: "collatz:m15:Descent127" };
  const other = { case_id: "collatz:m15:Descent143" };
  assert.equal(core.selectionVisibleInResults([], selected.case_id), false);
  assert.equal(core.selectionVisibleInResults([other], selected.case_id), false);
  assert.equal(core.selectionVisibleInResults([selected, other], selected.case_id), true);
});

test("summarizes only explicit source and dependency connections", () => {
  const summary = core.summarizeConnections([
    { source: { package_path: "sources/A.lean" }, dependencies: { imports: ["Mathlib.X"], module_local_declarations_referenced: ["iterate"] } },
    { source: { package_path: "sources/A.lean" }, dependencies: { imports: ["Mathlib.X"], module_local_declarations_referenced: ["iterate", "C"] } },
    { source: { package_path: "sources/B.lean" }, dependencies: { imports: ["Mathlib.Y"], module_local_declarations_referenced: ["C"] } }
  ]);
  assert.equal(summary.recordCount, 3);
  assert.equal(summary.uniqueSourceFiles, 2);
  assert.deepEqual(summary.sourceFiles[0], { name: "sources/A.lean", count: 2 });
  assert.deepEqual(summary.imports[0], { name: "Mathlib.X", count: 2 });
  assert.equal(summary.limits.semanticEquivalenceInferred, false);
});
