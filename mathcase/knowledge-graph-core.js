(function (root, factory) {
  "use strict";
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  root.MathCaseKnowledgeGraphCore = api;
})(globalThis, function () {
  "use strict";

  const PIN = Object.freeze({
    commit: ["82668e1d58873982", "226d137339945a30", "ca4ee895"].join(""),
    recordCount: 4262
  });
  const SHA_RE = /^[0-9a-f]{64}$/;

  function parseSha256Sidecar(text, expectedName) {
    if (typeof text !== "string" || typeof expectedName !== "string") return null;
    const match = text.trim().match(/^([0-9a-f]{64})  ([A-Za-z0-9._-]+)$/);
    if (!match || match[2] !== expectedName) return null;
    return match[1];
  }

  function verifySnapshotHashes(manifestSidecar, recordsSidecar, manifest, actualHashes) {
    const manifestExpected = parseSha256Sidecar(manifestSidecar, "manifest.json");
    const recordsExpected = parseSha256Sidecar(recordsSidecar, "records.jsonl");
    if (!manifestExpected || !recordsExpected || !actualHashes ||
        manifestExpected !== actualHashes.manifest || recordsExpected !== actualHashes.records ||
        !manifest || manifest.index_sha256 !== actualHashes.index) {
      throw new Error("The downloaded files did not match the checksum chain in the pinned commit.");
    }
    return true;
  }

  function parseCollatzStatement(statement) {
    if (typeof statement !== "string") return null;
    const normalized = statement.replace(/\s+/g, " ").trim();
    const match = normalized.match(/^theorem\s+([A-Za-z0-9_'.]+)\s*:\s*∀\s*k\s*:\s*Nat,\s*iterate\s*\(\s*(\d+)\s*\*\s*k\s*\+\s*(\d+)\s*\)\s*(\d+)\s*=\s*(\d+)\s*\*\s*k\s*\+\s*(\d+)\s*∧\s*(\d+)\s*\*\s*k\s*\+\s*(\d+)\s*<\s*(\d+)\s*\*\s*k\s*\+\s*(\d+)$/);
    if (!match) return null;
    const [, theoremName, startSlope, startOffset, steps, endSlope, endOffset, repeatEndSlope, repeatEndOffset, repeatStartSlope, repeatStartOffset] = match;
    if (endSlope !== repeatEndSlope || endOffset !== repeatEndOffset || startSlope !== repeatStartSlope || startOffset !== repeatStartOffset) return null;
    const num = (value) => Number(value).toLocaleString("en-US");
    return Object.freeze({
      theoremName,
      startSlope,
      startOffset,
      steps,
      endSlope,
      endOffset,
      startText: `${num(startSlope)} × k + ${num(startOffset)}`,
      endText: `${num(endSlope)} × k + ${num(endOffset)}`,
      plainText: `For every natural number k, start at ${num(startSlope)} × k + ${num(startOffset)}. After ${num(steps)} standard Collatz steps, the result is exactly ${num(endSlope)} × k + ${num(endOffset)}, which is smaller than the start.`
    });
  }

  function validPackagePath(path, expectedRoot) {
    if (typeof path !== "string" || !path.startsWith(expectedRoot) || path.includes("\\") || path.startsWith("/")) return false;
    const pieces = path.split("/");
    return pieces.every((piece) => piece && piece !== "." && piece !== ".." && /^[A-Za-z0-9._-]+$/.test(piece));
  }

  function githubFileUrl(path, line) {
    const kind = path.startsWith("sources/") ? "sources/" : path.startsWith("evidence/") ? "evidence/" : null;
    if (!kind || !validPackagePath(path, kind)) return null;
    const encoded = path.split("/").map(encodeURIComponent).join("/");
    const suffix = Number.isInteger(line) && line > 0 ? `#L${line}` : "";
    return `https://github.com/DarthCeltic/MathCase/blob/${PIN.commit}/reproduction/m15-m20-r2/${encoded}${suffix}`;
  }

  function validateGraph(manifest, index, records, actualHashes) {
    if (!manifest || manifest.schema_version !== "mathcase-public-knowledge-graph-v1" ||
        manifest.status !== "PUBLIC_SAFE_PARTIAL_SLICE" || manifest.record_count !== PIN.recordCount ||
        manifest.cohort_counts?.["collatz-m15-m20-pinned-shards"] !== PIN.recordCount ||
        manifest.index_path !== "index.jsonl" || !actualHashes ||
        !SHA_RE.test(actualHashes.manifest || "") || !SHA_RE.test(actualHashes.index || "") ||
        !SHA_RE.test(actualHashes.records || "") || manifest.index_sha256 !== actualHashes.index ||
        manifest.m4_promotions !== 0 || manifest.external_calls !== 0 || manifest.external_spend_usd !== 0 ||
        manifest.excluded_owner_only_records !== 29 || manifest.excluded_historical_aggregate_records !== 3) {
      throw new Error("This proof library snapshot did not match its pinned release record.");
    }
    if (!Array.isArray(index) || !Array.isArray(records) || index.length !== PIN.recordCount || records.length !== PIN.recordCount) {
      throw new Error("The proof library did not contain all 4,262 expected records.");
    }
    const seen = new Set();
    for (let i = 0; i < records.length; i += 1) {
      const row = index[i];
      const record = records[i];
      if (!row || !record || row.case_id !== record.case_id || row.statement_sha256 !== record.statement_sha256 ||
          typeof row.case_id !== "string" || seen.has(row.case_id) || !SHA_RE.test(record.statement_sha256 || "") ||
          record.cohort !== "collatz-m15-m20-pinned-shards" || record.kind !== "bounded_residue_family_descent" ||
          record.lean_status !== "PASSED_PINNED_PER_SHARD_REPLAY" ||
          record.m0_status !== "NOT_REVIEWED_AS_INDIVIDUAL_SHARD_STATEMENT" ||
          record.m4_status !== "NOT_PROMOTED_PER_SHARD_REPLAY_ONLY" || record.sorryAx !== false ||
          record.novelty_status !== "NOT_ASSESSED" ||
          !Array.isArray(record.axioms) || !parseCollatzStatement(record.lean_statement_exact) ||
          !SHA_RE.test(record.source?.sha256 || "") || !Number.isInteger(record.source?.declaration_line) ||
          !SHA_RE.test(record.receipt?.file_sha256 || "") || !SHA_RE.test(record.receipt?.row_sha256 || "") ||
          !Number.isInteger(record.receipt?.line) ||
          !githubFileUrl(record.source?.package_path) || !githubFileUrl(record.receipt?.package_path, record.receipt?.line)) {
        throw new Error(`Proof record ${i + 1} did not match the exact-index, review, or source rules.`);
      }
      seen.add(row.case_id);
    }
    return true;
  }

  function normalizeSearch(value) {
    return String(value || "").toLocaleLowerCase().replace(/[\s*×]/g, "");
  }

  function matchesSearch(record, query) {
    const q = normalizeSearch(query);
    if (!q) return true;
    const parsed = parseCollatzStatement(record.lean_statement_exact);
    const haystack = normalizeSearch([record.case_id, parsed?.theoremName, parsed?.plainText, record.lean_statement_exact].join("\n"));
    return haystack.includes(q);
  }

  function selectionVisibleInResults(matches, selectedCaseId) {
    return typeof selectedCaseId === "string" && matches.some((record) => record.case_id === selectedCaseId);
  }

  return Object.freeze({ PIN, parseSha256Sidecar, verifySnapshotHashes, parseCollatzStatement, githubFileUrl, validateGraph, normalizeSearch, matchesSearch, selectionVisibleInResults });
});
