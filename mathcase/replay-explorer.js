(function (root) {
  "use strict";

  const PAGE_SIZE = 30;
  const COMPARED_FIELDS = [
    ["Source SHA-256", "source_sha256"],
    ["Expected OLEAN SHA-256", "expected_olean_sha256"],
    ["Fresh OLEAN SHA-256", "olean_sha256"],
    ["Lean stdout SHA-256", "stdout_sha256"],
    ["Lean stderr SHA-256", "stderr_sha256"],
    ["Lean exit-code SHA-256", "exit_code_sha256"]
  ];
  const AXIOM_OUTPUT_SHA256 = "d34f68a239f8ad528c8716898d3670063e464fe4899f2e7b117d8e6c9c6c0508";

  function parseTsv(text) {
    const lines = text.replace(/^\uFEFF/, "").replace(/\r\n/g, "\n").trimEnd().split("\n");
    if (lines.length < 2) throw new Error("The table is empty.");
    const header = lines[0].split("\t");
    return lines.slice(1).filter(Boolean).map((line) => {
      const values = line.split("\t");
      return Object.fromEntries(header.map((name, index) => [name, values[index] || ""]));
    });
  }

  function compareRows(first, second) {
    const firstByModule = new Map(first.map((row) => [row.module, row]));
    const secondByModule = new Map(second.map((row) => [row.module, row]));
    if (firstByModule.size !== secondByModule.size || firstByModule.size === 0) {
      throw new Error("The phase tables have different module counts.");
    }
    const names = [...firstByModule.keys()].sort((a, b) => a.localeCompare(b));
    const fields = ["source_sha256", "expected_olean_sha256", "olean_sha256", "stdout_sha256", "stderr_sha256", "exit_code", "exit_code_sha256"];
    return names.map((module) => {
      const phase1 = firstByModule.get(module);
      const phase2 = secondByModule.get(module);
      if (!phase2) throw new Error("A module is missing from Phase 2.");
      const matches = fields.every((field) => phase1[field] === phase2[field]);
      return { module, phase1, phase2, matches };
    });
  }

  function compareAxiomRows(first, second) {
    const firstByGroup = new Map(first.map((row) => [row.group, row]));
    const secondByGroup = new Map(second.map((row) => [row.group, row]));
    if (firstByGroup.size !== secondByGroup.size || firstByGroup.size === 0) {
      throw new Error("The axiom group tables have different group counts.");
    }
    const fields = ["source_path", "source_sha256", "stdout_sha256", "stderr_sha256", "exit_code", "exit_code_sha256", "sorryAx_count"];
    return [...firstByGroup.keys()].sort((a, b) => a.localeCompare(b)).map((group) => {
      const phase1 = firstByGroup.get(group);
      const phase2 = secondByGroup.get(group);
      if (!phase2) throw new Error("An axiom group is missing from Phase 2.");
      const differences = fields.filter((field) => phase1[field] !== phase2[field]);
      return { group, phase1, phase2, matches: differences.length === 0, differences };
    });
  }

  function bytesToHex(buffer) {
    return [...new Uint8Array(buffer)].map((byte) => byte.toString(16).padStart(2, "0")).join("");
  }

  function makeElement(tag, className, text) {
    const element = root.document.createElement(tag);
    if (className) element.className = className;
    if (text !== undefined) element.textContent = text;
    return element;
  }

  function appendHashComparison(container, label, field, first, second) {
    const item = makeElement("div", "replay-hash");
    item.append(makeElement("strong", "", label));
    item.append(makeElement("span", "", first[field] === second[field] ? "Same in both phases" : "Different across phases"));
    item.append(makeElement("code", "", `Phase 1 · ${first[field] || "missing"}`));
    item.append(makeElement("code", "", `Phase 2 · ${second[field] || "missing"}`));
    container.append(item);
  }

  function makeRecord(item) {
    const details = makeElement("details", "replay-row");
    details.setAttribute("role", "listitem");
    const summary = makeElement("summary");
    summary.append(makeElement("span", "replay-module", item.module));
    summary.append(makeElement("span", "replay-kind", item.phase1.kind === "composition" ? "Composition module" : "Shard module"));
    const exitText = `Lean module exits: Phase 1 ${item.phase1.exit_code} · Phase 2 ${item.phase2.exit_code}. ${item.matches ? "Compared hashes agree." : "A difference is recorded."}`;
    summary.append(makeElement("span", "replay-result-note", exitText));
    details.append(summary);

    const body = makeElement("div", "replay-row-body");
    const relativePath = makeElement("p", "replay-source-path");
    relativePath.append(makeElement("strong", "", "Relative source path: "));
    relativePath.append(makeElement("code", "", item.phase1.source_path));
    body.append(relativePath);

    const hashes = makeElement("div", "replay-hash-grid");
    for (const [label, field] of COMPARED_FIELDS) appendHashComparison(hashes, label, field, item.phase1, item.phase2);
    body.append(hashes);

    const expectedMatches = item.phase1.expected_olean_match === "YES" && item.phase2.expected_olean_match === "YES";
    const duration = makeElement("p", "replay-duration");
    duration.textContent = `Compile time: Phase 1 ${item.phase1.duration_ms} ms · Phase 2 ${item.phase2.duration_ms} ms. Historical OLEAN match: ${expectedMatches ? "yes" : "no; the new phase outputs agree with each other but differ from the older expected bytes"}.`;
    body.append(duration);
    details.append(body);
    return details;
  }

  function makeAxiomRecord(item) {
    const details = makeElement("details", "replay-row");
    details.setAttribute("role", "listitem");
    const summary = makeElement("summary");
    summary.append(makeElement("span", "replay-module", item.group));
    summary.append(makeElement("span", "replay-kind", "Axiom group"));
    summary.append(makeElement("span", "replay-result-note", `Group exits: Phase 1 ${item.phase1.exit_code} · Phase 2 ${item.phase2.exit_code}. ${item.matches ? "Recorded fields agree." : `Differences: ${item.differences.join(", ")}.`} sorryAx: ${item.phase1.sorryAx_count} / ${item.phase2.sorryAx_count}.`));
    details.append(summary);

    const body = makeElement("div", "replay-row-body");
    const source = makeElement("p", "replay-source-path");
    source.append(makeElement("strong", "", "Relative Lean source: "));
    source.append(makeElement("code", "", item.phase1.source_path));
    body.append(source);
    const hashes = makeElement("div", "replay-hash-grid");
    for (const [label, field] of [
      ["Group source SHA-256", "source_sha256"],
      ["Lean output SHA-256", "stdout_sha256"],
      ["Standard error SHA-256", "stderr_sha256"],
      ["Exit-code SHA-256", "exit_code_sha256"]
    ]) appendHashComparison(hashes, label, field, item.phase1, item.phase2);
    body.append(hashes);
    const times = makeElement("p", "replay-duration");
    times.textContent = `sorryAx count: Phase 1 ${item.phase1.sorryAx_count} · Phase 2 ${item.phase2.sorryAx_count}. Recorded duration: Phase 1 ${item.phase1.duration_ms} ms · Phase 2 ${item.phase2.duration_ms} ms. Recorded interval: Phase 1 ${item.phase1.started_utc} to ${item.phase1.finished_utc} · Phase 2 ${item.phase2.started_utc} to ${item.phase2.finished_utc}.`;
    body.append(times);
    details.append(body);
    return details;
  }

  function init() {
    const results = root.document.getElementById("replay-results");
    if (!results) return;
    const status = root.document.getElementById("replay-status");
    const search = root.document.getElementById("replay-search");
    const kind = root.document.getElementById("replay-kind");
    const more = root.document.getElementById("replay-more");
    const failure = root.document.getElementById("replay-failure");
    const axiomResults = root.document.getElementById("axiom-results");
    const axiomStatus = root.document.getElementById("axiom-status");
    const axiomFailure = root.document.getElementById("axiom-failure");
    const axiomOutputPanel = root.document.getElementById("axiom-output-panel");
    const axiomOutputStatus = root.document.getElementById("axiom-output-status");
    const axiomOutputText = root.document.getElementById("axiom-output-text");
    const axiomOutputFailure = root.document.getElementById("axiom-output-failure");
    let records = [];
    let visibleCount = PAGE_SIZE;

    function filteredRecords() {
      const query = search.value.trim().toLocaleLowerCase();
      return records.filter((record) => {
        const rowKind = record.phase1.kind;
        const kindMatches = kind.value === "all" || rowKind === kind.value;
        const queryMatches = !query || record.module.toLocaleLowerCase().includes(query) || record.phase1.source_path.toLocaleLowerCase().includes(query);
        return kindMatches && queryMatches;
      });
    }

    function render() {
      const filtered = filteredRecords();
      results.replaceChildren(...filtered.slice(0, visibleCount).map(makeRecord));
      more.hidden = filtered.length <= visibleCount;
      status.textContent = `Showing ${Math.min(filtered.length, visibleCount)} of ${filtered.length} matching modules · ${records.length} module pairs loaded.`;
    }

    search.addEventListener("input", () => { visibleCount = PAGE_SIZE; render(); });
    kind.addEventListener("change", () => { visibleCount = PAGE_SIZE; render(); });
    more.addEventListener("click", () => { visibleCount += PAGE_SIZE; render(); });

    Promise.all([
      root.fetch("evidence/collatz/m20-source-replay-2026-11-18/phase-1/compile-records.tsv"),
      root.fetch("evidence/collatz/m20-source-replay-2026-11-18/phase-2/compile-records.tsv")
    ]).then((responses) => {
      if (responses.some((response) => !response.ok)) throw new Error("A phase table could not be fetched.");
      return Promise.all(responses.map((response) => response.text()));
    }).then(([phase1Text, phase2Text]) => {
      records = compareRows(parseTsv(phase1Text), parseTsv(phase2Text));
      const shardCount = records.filter((record) => record.phase1.kind === "replay").length;
      const compositionCount = records.filter((record) => record.phase1.kind === "composition").length;
      if (records.length !== 363 || shardCount !== 229 || compositionCount !== 134) {
        throw new Error("The loaded module totals do not match the recorded replay summary.");
      }
      if (records.some((record) => record.phase1.exit_code !== "0" || record.phase2.exit_code !== "0" || !record.matches)) {
        throw new Error("The module records contain an exit or hash difference; use the full report.");
      }
      render();
    }).catch(() => {
      status.textContent = "The phase tables did not pass the expected count and hash checks.";
      failure.hidden = false;
    });

    if (axiomResults && axiomStatus && axiomFailure) {
      Promise.all([
        root.fetch("evidence/collatz/m20-source-replay-2026-11-18/phase-1/axiom-records.tsv"),
        root.fetch("evidence/collatz/m20-source-replay-2026-11-18/phase-2/axiom-records.tsv")
      ]).then((responses) => {
        if (responses.some((response) => !response.ok)) throw new Error("An axiom group table could not be fetched.");
        return Promise.all(responses.map((response) => response.text()));
      }).then(([phase1Text, phase2Text]) => {
        const groups = compareAxiomRows(parseTsv(phase1Text), parseTsv(phase2Text));
        const invalid = groups.filter((item) => !item.matches || item.phase1.exit_code !== "0" || item.phase2.exit_code !== "0" || item.phase1.sorryAx_count !== "0" || item.phase2.sorryAx_count !== "0");
        axiomResults.replaceChildren(...groups.map(makeAxiomRecord));
        axiomStatus.textContent = `${groups.length} paired axiom groups loaded. ${invalid.length === 0 ? "All group source/output/exit records agree across phases; all exits are 0 and all sorryAx counts are 0." : `${invalid.length} group(s) contain a recorded difference or nonzero status; open the rows.`}`;
        axiomFailure.hidden = groups.length === 23 && invalid.length === 0;
        if (groups.length !== 23 || invalid.length !== 0) axiomFailure.hidden = false;
      }).catch(() => {
        axiomStatus.textContent = "The two axiom-group tables could not be compared.";
        axiomFailure.hidden = false;
      });
    }

    if (axiomOutputPanel && axiomOutputStatus && axiomOutputText && axiomOutputFailure) {
      let outputLoading = false;
      let outputLoaded = false;
      axiomOutputPanel.addEventListener("toggle", () => {
        if (!axiomOutputPanel.open || outputLoading || outputLoaded) return;
        outputLoading = true;
        axiomOutputStatus.textContent = "Fetching both saved output files and checking their SHA-256…";
        const base = "evidence/collatz/m20-source-replay-2026-11-18/phase-";
        Promise.all([1, 2].map((phase) => root.fetch(`${base}${phase}/axiom-output-all.txt`))).then((responses) => {
          if (responses.some((response) => !response.ok)) throw new Error("An output file could not be fetched.");
          return Promise.all(responses.map((response) => response.arrayBuffer()));
        }).then(async ([phase1Bytes, phase2Bytes]) => {
          if (!root.crypto || !root.crypto.subtle || typeof root.TextDecoder !== "function") throw new Error("This browser does not provide the required local SHA-256 check.");
          const [phase1Hash, phase2Hash] = await Promise.all([
            root.crypto.subtle.digest("SHA-256", phase1Bytes).then(bytesToHex),
            root.crypto.subtle.digest("SHA-256", phase2Bytes).then(bytesToHex)
          ]);
          if (phase1Hash !== AXIOM_OUTPUT_SHA256 || phase2Hash !== AXIOM_OUTPUT_SHA256 || phase1Hash !== phase2Hash) throw new Error("The saved output digests do not match the recorded value.");
          const output = new root.TextDecoder("utf-8", { fatal: true }).decode(phase1Bytes);
          const lineCount = output.trimEnd().split(/\r?\n/).length;
          if (lineCount !== 4262) throw new Error("The output line count differs from the recorded query count.");
          axiomOutputText.textContent = output;
          axiomOutputStatus.textContent = `Both phase files match SHA-256 ${AXIOM_OUTPUT_SHA256}; each contains ${lineCount.toLocaleString()} lines. Displaying the checked Phase 1 text.`;
          outputLoaded = true;
        }).catch(() => {
          axiomOutputStatus.textContent = "The axiom output is not displayed as verified.";
          axiomOutputFailure.hidden = false;
        }).finally(() => { outputLoading = false; });
      });
    }
  }

  if (typeof root.document !== "undefined") root.document.addEventListener("DOMContentLoaded", init);
  if (typeof module !== "undefined" && module.exports) module.exports = { parseTsv, compareRows, compareAxiomRows };
})(typeof globalThis === "undefined" ? this : globalThis);
